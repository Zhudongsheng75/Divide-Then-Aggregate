import ast
import re
import os
import json
import time
import requests
from tqdm import tqdm
from termcolor import colored
import random
from toolbench.inference.LLM.chatgpt_function_model import ChatGPTFunction
from toolbench.inference.LLM.tool_llama_net import ToolLLaMANet
from toolbench.inference.Algorithms.single_chain import single_chain
from toolbench.inference.Algorithms.DFS_serial import DFS_tree_search
from toolbench.inference.Algorithms.DFS_parallel_llama import DFS_parallel_search_llama
from toolbench.inference.Algorithms.DFS_parallel_GPT import DFS_parallel_search_GPT
from toolbench.inference.server import get_rapidapi_response
from toolbench.utils import standardize, change_name, replace_llama_with_condense

from toolbench.inference.Downstream_tasks.base_env import base_env
from concurrent.futures import ThreadPoolExecutor


# For pipeline environment preparation
def get_white_list(tool_root_dir):
    # print(tool_root_dir)
    white_list_dir = os.path.join(tool_root_dir)
    white_list = {}
    for cate in tqdm(os.listdir(white_list_dir)):
        if not os.path.isdir(os.path.join(white_list_dir, cate)):
            continue
        for file in os.listdir(os.path.join(white_list_dir, cate)):
            if not file.endswith(".json"):
                continue
            standard_tool_name = file.split(".")[0]
            # print(standard_tool_name)
            with open(os.path.join(white_list_dir, cate, file)) as reader:
                js_data = json.load(reader)
            origin_tool_name = js_data["tool_name"]
            white_list[standardize(origin_tool_name)] = {
                "description": js_data["tool_description"],
                "standard_tool_name": standard_tool_name,
            }
    return white_list


def contain(candidate_list, white_list):
    output = []
    for cand in candidate_list:
        if cand not in white_list.keys():
            return False
        output.append(white_list[cand])
    return output


# rapidapi env wrapper
class rapidapi_wrapper(base_env):
    def __init__(self, query_json, tool_descriptions, retriever, args, process_id=0):
        super(rapidapi_wrapper).__init__()

        self.tool_root_dir = args.tool_root_dir
        self.toolbench_key = args.toolbench_key
        self.rapidapi_key = args.rapidapi_key
        self.use_rapidapi_key = args.use_rapidapi_key
        self.api_customization = args.api_customization
        self.service_url = os.getenv("SERVICE_URL", "http://localhost:8080/virtual")
        # self.service_url = "http://localhost:8080/virtual"
        self.max_observation_length = args.max_observation_length
        self.observ_compress_method = args.observ_compress_method
        self.retriever = retriever
        self.process_id = process_id

        self.tool_names = []
        self.cate_names = []

        self.input_description = query_json["query"]
        self.functions = []
        self.api_name_reflect = {}

        if self.retriever is not None:
            query_json = self.retrieve_rapidapi_tools(
                self.input_description, args.retrieved_api_nums, args.tool_root_dir
            )
            data_dict = self.fetch_api_json(query_json)
            tool_descriptions = self.build_tool_description(data_dict)
        else:
            # 包含了该query所有相关api的描述和请求参数类型、地址等信息
            data_dict = self.fetch_api_json(query_json)

        # 把原始的api json转成openai function call风格的json
        for k, api_json in enumerate(data_dict["api_list"]):
            standard_tool_name = tool_descriptions[k][0]
            openai_function_json, cate_name, pure_api_name = self.api_json_to_openai_json(api_json, standard_tool_name)
            self.functions.append(openai_function_json)

            self.api_name_reflect[openai_function_json["name"]] = pure_api_name
            self.tool_names.append(standard_tool_name)
            self.cate_names.append(cate_name)

        finish_func = {
            "name": "Finish",
            "description": "If you believe that you have obtained a result that can answer the task, please call this function to provide the final answer. Alternatively, if you recognize that you are unable to proceed with the task in the current state, call this function to restart. Remember: you must ALWAYS call this function at the end of your attempt, and the only part that will be shown to the user is the final answer, so it should contain sufficient information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "return_type": {
                        "type": "string",
                        "enum": ["give_answer", "give_up_and_restart"],
                    },
                    "final_answer": {
                        "type": "string",
                        "description": 'The final answer you want to give the user. You should have this field if "return_type"=="give_answer"',
                    },
                },
                "required": ["return_type"],
            },
        }

        self.functions.append(finish_func)
        self.CALL_MAX_TIME = 3
        self.task_description = f"""You should use functions to help handle the real time user querys. Remember:
1.ALWAYS call \"Finish\" function at the end of the task. And the final answer should contain enough information to show to the user,If you can't handle the task, or you find that function calls always fail(the function is not valid now), use function Finish->give_up_and_restart.
2.Do not use origin tool names, use only subfunctions' names.
You have access of the following tools:\n"""

        unduplicated_reflection = {}
        for standardize_tool_name, tool_des in tool_descriptions:
            unduplicated_reflection[standardize_tool_name] = tool_des

        for k, (standardize_tool_name, tool_des) in enumerate(unduplicated_reflection.items()):
            try:
                striped = tool_des[:512].replace("\n", "").strip()
            except:
                striped = ""
            if striped == "":
                striped = "None"
            self.task_description += f"{k+1}.{standardize_tool_name}: {striped}\n"

        self.success = 0

    def build_tool_description(self, data_dict):
        """
        构造(tool_name, tool_description)的列表
        """
        white_list = get_white_list(self.tool_root_dir)
        origin_tool_names = [standardize(cont["tool_name"]) for cont in data_dict["api_list"]]
        tool_des = contain(origin_tool_names, white_list)
        tool_descriptions = [[cont["standard_tool_name"], cont["description"]] for cont in tool_des]
        return tool_descriptions

    def retrieve_rapidapi_tools(self, query, top_k, jsons_path):
        retrieved_tools = self.retriever.retrieving(query, top_k=top_k)
        query_json = {"api_list": []}
        for tool_dict in retrieved_tools:
            if len(query_json["api_list"]) == top_k:
                break
            category = tool_dict["category"]
            tool_name = tool_dict["tool_name"]
            api_name = tool_dict["api_name"]
            if os.path.exists(jsons_path):
                if os.path.exists(os.path.join(jsons_path, category)):
                    if os.path.exists(os.path.join(jsons_path, category, tool_name + ".json")):
                        query_json["api_list"].append(
                            {"category_name": category, "tool_name": tool_name, "api_name": api_name}
                        )
        return query_json

    def fetch_api_json(self, query_json):
        """
        将instruction文件中生成该query所用的api list中的每个api所属的tool下的所有api的信息都加到列表中
        这么做的原因是：之前给GPT的prompt中的api信息不够完整，没有包含请求必须的url等信息
        Args:
            query_json (dict): 包含API查询信息的JSON字典，其中必须包含"api_list"键，
                该键对应的值是一个包含多个字典的列表，每个字典至少包含"category_name"（API所属分类名）、
                "tool_name"（工具名）、"api_name"（API名）三个键。

        Returns:
            dict: 包含查询结果的字典，其中包含一个"api_list"键，
                该键对应的值是一个包含多个字典的列表，每个字典表示一个API的信息，
                包括"category_name"（API所属分类名）、"api_name"（API名）、
                "api_description"（API描述）、"required_parameters"（API必填参数）、
                "optional_parameters"（API可选参数）、"tool_name"（工具名）等键。

        """
        data_dict = {"api_list": []}
        for item in query_json["api_list"]:
            cate_name = item["category_name"]
            tool_name = standardize(item["tool_name"])
            api_name = change_name(standardize(item["api_name"]))
            tool_json = json.load(open(os.path.join(self.tool_root_dir, cate_name, tool_name + ".json"), "r"))
            append_flag = False
            api_dict_names = []
            for api_dict in tool_json["api_list"]:
                api_dict_names.append(api_dict["name"])
                pure_api_name = change_name(standardize(api_dict["name"]))
                if pure_api_name != api_name:
                    continue
                api_json = {}
                api_json["category_name"] = cate_name
                api_json["api_name"] = api_dict["name"]
                api_json["api_description"] = api_dict["description"]
                api_json["required_parameters"] = api_dict["required_parameters"]
                api_json["optional_parameters"] = api_dict["optional_parameters"]
                api_json["tool_name"] = tool_json["tool_name"]
                data_dict["api_list"].append(api_json)
                append_flag = True
                break
            if not append_flag:
                print(api_name, api_dict_names)
        return data_dict

    def api_json_to_openai_json(self, api_json, standard_tool_name):
        """
        将API的JSON格式转换为OpenAI的JSON格式。

        Args:
            api_json (dict): 包含API信息的字典，包含"api_name"、"api_description"、"required_parameters"和"optional_parameters"等键。
            standard_tool_name (str): 标准的工具名称，用于拼接新的API名称。

        Returns:
            tuple: 包含三个元素的元组，分别为：
                - templete (dict): 转换后的OpenAI格式的JSON字典，包含"name"、"description"和"parameters"等键。
                - category_name (str): API所属的分类名称。
                - pure_api_name (str): 标准化后的API名称。

        """
        description_max_length = 256
        templete = {
            "name": "",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "optional": [],
            },
        }

        map_type = {"NUMBER": "integer", "STRING": "string", "BOOLEAN": "boolean"}

        pure_api_name = change_name(standardize(api_json["api_name"]))
        # 拼接api_name和tool_name作为新的api_name
        templete["name"] = pure_api_name + f"_for_{standard_tool_name}"
        templete["name"] = templete["name"][-64:]

        # 添加头部说明，同时将里面的tool_name替换成上面拼接后的api_name
        templete["description"] = f'This is the subfunction for tool "{standard_tool_name}", you can use this tool.'
        if api_json["api_description"].strip() != "":
            tuncated_description = (
                api_json["api_description"]
                .strip()
                .replace(api_json["api_name"], templete["name"])[:description_max_length]
            )
            templete["description"] = (
                templete["description"] + f'The description of this function is: "{tuncated_description}"'
            )
        if "required_parameters" in api_json.keys() and len(api_json["required_parameters"]) > 0:
            for para in api_json["required_parameters"]:
                name = standardize(para["name"])
                # 对制定的api_name前面添加is_，应该是为了符合ChatGPT的规范
                name = change_name(name)
                # 如果参数类型是NUMBER、STRING、BOOLEAN，则将其转换为相应的OpenAI类型
                if para["type"] in map_type:
                    param_type = map_type[para["type"]]
                else:
                    param_type = "string"
                prompt = {
                    "type": param_type,
                    "description": para["description"][:description_max_length],
                }

                # 将api参数的默认值改为openAI的示例值
                default_value = para["default"]
                if len(str(default_value)) != 0:
                    prompt = {
                        "type": param_type,
                        "description": para["description"][:description_max_length],
                        "example_value": default_value,
                    }
                else:
                    prompt = {"type": param_type, "description": para["description"][:description_max_length]}

                templete["parameters"]["properties"][name] = prompt
                templete["parameters"]["required"].append(name)
            for para in api_json["optional_parameters"]:
                name = standardize(para["name"])
                name = change_name(name)
                if para["type"] in map_type:
                    param_type = map_type[para["type"]]
                else:
                    param_type = "string"

                default_value = para["default"]
                if len(str(default_value)) != 0:
                    prompt = {
                        "type": param_type,
                        "description": para["description"][:description_max_length],
                        "example_value": default_value,
                    }
                else:
                    prompt = {"type": param_type, "description": para["description"][:description_max_length]}

                templete["parameters"]["properties"][name] = prompt
                templete["parameters"]["optional"].append(name)

        return templete, api_json["category_name"], pure_api_name

    def check_success(self):
        return self.success

    def to_json(self):
        return {}

    def restart(self):
        pass

    def get_score(self):
        return 0.0

    def step(self, **args):
        output = self._step(**args)
        obs, code = output["observation"], output["status_code"]
        if len(obs) > self.max_observation_length:
            obs = obs[: self.max_observation_length] + "..."
        return obs, code, output["success"]

    def _step(self, action_name="", action_input=""):
        """
        根据传入的action_name和action_input执行相应的步骤，并返回api调用结果和状态码。
        注意：如果是action_name为Finish，则不需调用，直接解析输入返回

        Args:
            action_name (str, optional): 要执行的action的名称。传入api_name或者Finish
            action_input (str, optional): action的输入参数。默认为空字符串。

        Returns:
            tuple: 包含两个元素的元组，分别为：
                - observation_str (str): 观察字符串，包含返回的API结果或错误信息。
                - status_code (int): 状态码，表示不同的情况，具体含义如下：
                    0: 正常响应
                    1: 没有对应的API名称
                    2: 输入有误
                    3: 生成结束，最终答案出现
                    4: 模型自己决定进行剪枝
                    5: API调用超时
                    6: 404错误
                    7: 未订阅
                    8: 未授权
                    9: 请求过多
                    10: 每分钟请求限制
                    11: 消息中包含"error"字段
                    12: 发送请求时发生错误

        """
        if action_name == "Finish":
            # 如果action为Finish，则尝试解释给出的数据，如果因为不符合json格式解析失败，则尝试从中提取有效的信息，尽可能不因为某些小的格式错误导致整个交互被认为失败
            try:
                if isinstance(action_input, dict):
                    json_data = action_input
                else:
                    json_data = ast.literal_eval(action_input)
            except:
                try:
                    json_data = json.loads(action_input, strict=False)
                except:
                    json_data = {}
                    if '"return_type": "' in action_input:
                        if '"return_type": "give_answer"' in action_input:
                            return_type = "give_answer"
                        elif '"return_type": "give_up_and_restart"' in action_input:
                            return_type = "give_up_and_restart"
                        else:
                            return_type = action_input[
                                action_input.find('"return_type": "')
                                + len('"return_type": "') : action_input.find('",')
                            ]
                        json_data["return_type"] = return_type
                    if '"final_answer": "' in action_input:
                        final_answer = action_input[action_input.find('"final_answer": "') + len('"final_answer": "') :]
                        json_data["final_answer"] = final_answer
            if "return_type" not in json_data.keys():
                return dict(observation='{error:"must have "return_type""}', status_code=2, success=0)
            if json_data["return_type"] == "give_up_and_restart":
                return dict(observation='{"response":"chose to give up and restart"}', status_code=4, success=0)
            elif json_data["return_type"] == "give_answer":
                if "final_answer" not in json_data.keys():
                    return dict(observation='{error:"must have "final_answer""}', status_code=2, success=0)
                self.success = 1  # succesfully return final_answer
                return dict(
                    observation='{"response":"successfully giving the final answer."}', status_code=3, success=1
                )
            else:
                return dict(observation='{error:""return_type" is not a valid choice"}', status_code=2, success=0)
        else:
            # 找到对应的api，这块用for循环比较耗时，可以改进
            for k, function in enumerate(self.functions):
                if function["name"].endswith(action_name):
                    # 找到原始的api_name，而不是修改后用于适应openAId的那个api_name_for_tool_name格式
                    pure_api_name = self.api_name_reflect[function["name"]]
                    payload = {
                        "category": self.cate_names[k],
                        "tool_name": self.tool_names[k],
                        "api_name": pure_api_name,
                        "tool_input": action_input,
                        "strip": self.observ_compress_method,
                        "toolbench_key": self.toolbench_key,
                    }
                    if self.process_id == 0:
                        print(
                            colored(
                                f"query to {self.cate_names[k]}-->{self.tool_names[k]}-->{action_name}", color="yellow"
                            )
                        )
                    if self.use_rapidapi_key or self.api_customization:
                        payload["rapidapi_key"] = self.rapidapi_key
                        response = get_rapidapi_response(payload, api_customization=self.api_customization)
                    else:
                        time.sleep(1)  # rate limit: 30 per minute
                        headers = {"toolbench_key": self.toolbench_key}
                        timeout = None if self.service_url.endswith("virtual") else 15
                        try:
                            response = requests.post(self.service_url, json=payload, headers=headers, timeout=timeout)
                        except requests.exceptions.Timeout:
                            return dict(
                                observation=json.dumps({"error": f"Timeout error...", "response": ""}),
                                status_code=5,
                                success=0,
                            )
                        if response.status_code != 200:
                            return dict(
                                observation=json.dumps(
                                    {
                                        "error": f"request invalid, data error. status_code={response.status_code}",
                                        "response": "",
                                    }
                                ),
                                status_code=12,
                                success=0,
                            )
                        try:
                            response = response.json()
                        except:
                            # print(response)
                            return dict(
                                observation=json.dumps({"error": f"request invalid, data error", "response": ""}),
                                status_code=12,
                                success=0,
                            )

                    # 1 Hallucinating function names
                    # 4 means that the model decides to pruning by itself
                    # 5 represents api call timeout
                    # 6 for 404
                    # 7 means not subscribed
                    # 8 represents unauthorized
                    # 9 represents too many requests
                    # 10 stands for rate limit
                    # 11 message contains "error" field
                    # 12 error sending request
                    if response["error"] == "API not working error...":
                        status_code = 6
                    elif response["error"] == "Unauthorized error...":
                        status_code = 7
                    elif response["error"] == "Unsubscribed error...":
                        status_code = 8
                    elif response["error"] == "Too many requests error...":
                        status_code = 9
                    elif response["error"] == "Rate limit per minute error...":
                        print("Reach api calling limit per minute, sleeping...")
                        time.sleep(1)
                        status_code = 10
                    elif response["error"] == "Message error...":
                        status_code = 11
                    else:
                        status_code = 0
                    return dict(observation=json.dumps(response), status_code=status_code, success=0)
                    # except Exception as e:
                    #     return json.dumps({"error": f"Timeout error...{e}", "response": ""}), 5
            return dict(
                observation=json.dumps({"error": f"No such function name: {action_name}", "response": ""}),
                status_code=1,
                success=0,
            )


class pipeline_runner:
    def __init__(self, args, process_id=0, server=False):
        self.args = args
        self.add_retrieval = args.add_retrieval
        self.process_id = process_id
        self.server = server
        if not self.server:
            self.task_list = self.generate_task_list()
        else:
            self.task_list = []

    def get_backbone_model(self):
        args = self.args
        backbone_model = args.backbone_model
        return backbone_model

    def get_args(self):
        return self.args

    def generate_task_list(self):
        args = self.args
        query_dir = args.input_query_file
        answer_dir = args.output_answer_file
        if not os.path.exists(answer_dir):
            os.makedirs(answer_dir, exist_ok=True)
        method = args.method
        backbone_model = self.get_backbone_model()
        white_list = get_white_list(args.tool_root_dir)
        task_list = []
        querys = json.load(open(query_dir, "r"))
        for query_id, data_dict in enumerate(querys):
            if "query_id" in data_dict:
                query_id = data_dict["query_id"]
            if "api_list" in data_dict:
                origin_tool_names = [standardize(cont["tool_name"]) for cont in data_dict["api_list"]]
                tool_des = contain(origin_tool_names, white_list)
                if tool_des == False:
                    continue
                tool_des = [[cont["standard_tool_name"], cont["description"]] for cont in tool_des]
            else:
                tool_des = None
            task_list.append((method, backbone_model, query_id, data_dict, args, answer_dir, tool_des))
        return task_list

    def method_converter(
        self,
        backbone_model,
        openai_key,
        method,
        env,
        process_id,
        single_chain_max_step=12,
        max_query_count=60,
        callbacks=None,
    ):
        if callbacks is None:
            callbacks = []
        if backbone_model == "chatgpt_function":
            model = os.getenv("GPT_MODEL", "gpt-4o")
            llm_forward = ChatGPTFunction(
                model=model, api_base="http://llms-se.baidu-int.com:8200", openai_key=openai_key
            )
        elif backbone_model == "toolllama_net":
            llm_forward = ToolLLaMANet(url=self.args.llama_server_url)
        else:
            model = backbone_model
            llm_forward = model

        print(f"method: {method}")
        # 开始执行chain调用（COT或者DFS），这一块写在这里不太好
        if method.startswith("CoT"):
            passat = int(method.split("@")[-1].split("_")[0])
            chain = single_chain(llm=llm_forward, io_func=env, process_id=process_id)
            result = chain.start(pass_at=passat, single_chain_max_step=single_chain_max_step, answer=1)
        elif method.startswith("DFS"):
            pattern = r".+_w(\d+)"
            re_result = re.match(pattern, method)
            assert re_result != None
            width = int(re_result.group(1))
            with_filter = True
            if "woFilter" in method:
                with_filter = False
            if "parallel_llama" in method:
                chain = DFS_parallel_search_llama(
                    llm=llm_forward, io_func=env, process_id=process_id, callbacks=callbacks
                )
            elif "parallel_GPT" in method:
                chain = DFS_parallel_search_GPT(
                    llm=llm_forward, io_func=env, process_id=process_id, callbacks=callbacks, method=method
                )
            elif "parallel_qwen" in method:
                chain = DFS_parallel_search_Qwen(
                    llm=llm_forward, io_func=env, process_id=process_id, callbacks=callbacks, method=method
                )
            else:
                chain = DFS_tree_search(llm=llm_forward, io_func=env, process_id=process_id, callbacks=callbacks)
            result = chain.start(
                single_chain_max_step=single_chain_max_step,
                tree_beam_size=width,
                max_query_count=max_query_count,
                answer=1,
                with_filter=with_filter,
                backbone_model=backbone_model,
            )
        else:
            print("invalid method")
            raise NotImplementedError
        return chain, result

    def run_single_task(
        self,
        method,
        backbone_model,
        query_id,
        data_dict,
        args,
        output_dir_path,
        tool_des,
        retriever=None,
        process_id=0,
        callbacks=None,
        server=None,
    ):
        """
        执行一个task
        """
        if server is None:
            server = self.server
        if callbacks is None:
            if server:
                print("Warning: no callbacks are defined for server mode")
            callbacks = []
        print(f"输出目录：{output_dir_path}")
        os.makedirs(output_dir_path, exist_ok=True)
        # 如果已经存在输出文件，则不在执行这个task，直接返回
        output_file_path = os.path.join(output_dir_path, f"{query_id}_{method}.json")
        if (not server) and os.path.exists(output_file_path):
            return
        # callback目前不清楚作用是什么，可能是rapidapi作为server的时候有用（应该是运行ui server的时候）
        [callback.on_tool_retrieval_start() for callback in callbacks]
        env = rapidapi_wrapper(data_dict, tool_des, retriever, args, process_id=process_id)
        [callback.on_tool_retrieval_end(tools=env.functions) for callback in callbacks]
        query = data_dict["query"]
        if process_id == 0:
            print(colored(f"[process({process_id})]now playing {query}, with {len(env.functions)} APIs", "green"))
        [callback.on_request_start(user_input=query, method=method) for callback in callbacks]
        chain, result = self.method_converter(
            backbone_model=backbone_model,
            openai_key=args.openai_key,
            method=method,
            env=env,
            process_id=process_id,
            single_chain_max_step=12,
            max_query_count=200,
            callbacks=callbacks,
        )
        [
            callback.on_request_end(chain=chain.terminal_node[0].messages, outputs=chain.terminal_node[0].description)
            for callback in callbacks
        ]
        if output_dir_path is not None:
            with open(output_file_path, "w") as writer:
                data = chain.to_json(answer=True, process=True)
                data["answer_generation"]["query"] = query
                json.dump(data, writer, indent=2)
                success = (
                    data["answer_generation"]["valid_data"]
                    and "give_answer" in data["answer_generation"]["final_answer"]
                )
                if process_id == 0:
                    print(colored(f"[process({process_id})]valid={success}", "green"))
        return result

    def run(self):
        task_list = self.task_list
        random.seed(42)
        random.shuffle(task_list)
        print(f"total tasks: {len(task_list)}")
        new_task_list = []
        for task in task_list:
            out_dir_path = task[-2]
            query_id = task[2]
            output_file_path = os.path.join(out_dir_path, f"{query_id}_{self.args.method}.json")
            if not os.path.exists(output_file_path):
                new_task_list.append(task)
        task_list = new_task_list
        print(f"undo tasks: {len(task_list)}")
        retriever = None
        if self.args.num_thread == 1:
            for k, task in enumerate(task_list):
                print(f"process[{self.process_id}] doing task {k}/{len(task_list)}: real_task_id_{task[2]}")
                result = self.run_single_task(*task, retriever=retriever, process_id=self.process_id)
        else:

            def distribute_single_tasks(input):
                id, task = input
                return self.run_single_task(*task, retriever=retriever, process_id=id + self.process_id)

            with ThreadPoolExecutor(self.args.num_thread) as executor:
                for _ in tqdm(
                    executor.map(distribute_single_tasks, zip(range(len(task_list)), task_list)),
                    total=len(task_list),
                    disable=self.args.disable_tqdm,
                ):
                    pass
