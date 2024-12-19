<div align= "center">
    <h1>DTA-Llama</h1>
</div>

<div align="center">

</div>

# Contents
- Features
- Train
  - Dataset
  - Model Training
- Inference
  - The Virtual API Server
  - The Model Server
- Performance Evaluation
  - Solvable Pass Rate
  - Solvable Win Rate
  - Time and Token Cost

Welcome to **Divide-Then-Aggregate**: An Efficient Tool Learning Method via Parallel Tool Invocation.

# Features
- We transformed the serial data into a DAG format, contributing a high-quality and high-quantity parallel tool invocation dataset to the open-source community.
- A new tool invocation framework has been established, transforming invocation into Process/Threads format. This, along with the parallel paradigm, significantly simplifies the trajectories of tool invocation, enhancing efficiency
while reducing unnecessary noise.
- The experiments comprehensively verified the superiority of our method from three aspects: tool invocation effectiveness, computational
cost, and generalization ability.

# Train
## Dataset
The dataset is refined from the train data in ToolBench. We fixed the error steps and use ChatGPT to recognize 
if the tool execution step can be parallel, separate the tool execution step into parallelable and non-parallelable and 
finally merge the dataset into a train dataset.

We provide the dataset [download link](https://huggingface.co/datasets/dongsheng/DTA-Tool) here.

给出数据集下载后存放的位置（因为我们是做了multi转single的处理，这边也贴一个代码然后讲一下吧），然后对应的脚本也需要修改一下。

## Model Training
### Base Model
We here provide the base model download link:
- Llama-2-7b-hf: https://huggingface.co/meta-llama/Llama-2-7b-hf
- Llama-2-13b-hf: https://huggingface.co/meta-llama/Llama-2-13b-hf
- Llama-3-8b-hf: https://huggingface.co/meta-llama/Meta-Llama-3-8B

### Train the model
```bash
# train llama2-7b or llama2-13b 
sh run_train_llama2.sh ${base_model_dir} ${output_dir}

# train llama3-8b
sh run_train_llama3.sh ${base_model_dir} ${output_dir}
```


# Inference
## The Virtual API Server
We use the  [StableToolBench](https://github.com/THUNLP-MT/StableToolBench/tree/master?tab=readme-ov-file) as the api server for the virtual tool invocation. The virtual server returns the response by the following step:
1. Check if the request exists in the cache. If not, turn to step 2.
2. Call the real api server. If fails, turn to step 3.
3. Call the gpt-4-turbo-preview model to simulate the response.

#### The folder structure
```
├── /virtual_server/
│  ├── /tools/
│  │  └── ...
│  ├── /tool_response_cache/
│  │  └── ...
│  ├── config.yml
│  ├── main.py
│  ├── utils.py
```

#### Running the server
You need to first specify your configurations in `server/config.yml` before running the server. Parameters needed are:
 - `api_key`: The API key for OpenAI models.
 - `api_base`: The API base for OpenAI models if you are using Azure.
 - `model`: The OpenAI model to use. The default value is gpt-4-turbo-preview.
 - `temperature`: The temperature for LLM simulation. The default value is 0.
 - `toolbench_url`: The real ToolBench server URL. The default value is `http://8.218.239.54:8080/rapidapi`.
 - `tools_folder`: The tools environment folder path. Default to `./tools`.
 - `cache_folder`: The cache folder path. Default to `./tool_response_cache`.
 - `is_save`: A flag to indicate whether to save real and simulated responses into the cache. The new cache is saved at `./tool_response_new_cache`.
 - `port`: The server port to run on, default to 8080.

Run the server by running:
```
cd virtual_server
python main.py
```
The server will be run at `http://localhost:{port}/virtual`. 
To use the server, you will further need a toolbench key. You can apply one from this [form](https://forms.gle/oCHHc8DQzhGfiT9r6).


### Testing the Server
You can test the server with
```
import requests
import json
import os

url = 'http://localhost:8080/virtual'
data = {
    "category": "Media",
    "tool_name": "newapi_for_media",
    "api_name": "url",
    "tool_input": {'url': 'https://api.socialmedia.com/friend/photos'},
    "strip": "",
    "toolbench_key": ""
}
headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json',
}

# Make the POST request
response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.text)
```
## Infer

这边需要贴我们的模型地址，搞一个目录索引；

### Parameter Description

- **backbone_model**  
Used to select the type of model，GPT-series models or Open-source models.
  - **chatgpt_function**: GPT-series models
  - **toolllama_net**: Open-source models
- **method**  
The specific implementation method of Tool Learning.
  - **CoT@1**: The CoT/ReAct method, which is repeatedly mentioned in the paper, refers to ReAct in the experiments;
  - **DFS_woFilter_w2**: The DFSDT method in the experiments of the paper; 
  - **DFS_parallel_GPT_woFilter_w2**: It is used exclusively for GPT-series models, referring to the Parallel method in the paper's GPT-series;
  - **DFS_parallel_llama_woFilter_w2**: That is, our Divide-Then-Aggregate method.
- **test_set**  
The six subsets in the benchmark.
   - **G1_instruction**: The I1-Inst. in the experiments of the paper;
   - **G2_instruction:** The I2-Inst. in the experiments of the paper;
   - **G3_instruction**: The I3-Inst. in the experiments of the paper;
   - **G1_category**: The I1-Cat. in the experiments of the paper;
   - **G2_category**: The I2-Cat. in the experiments of the paper;
   - **G1_tool**: The I1-Tool in the experiments of the paper.

run_qa_pipeline_multithread.sh文件里面有很多其他的参数，涉及到openai、toolbench、GPT_MODEL、llama_model_server_url等，都详细解释一下吧，必要的话也可以搞成参数。

### Inference answers

Run the following command to run the inference pipeline:
```bash
# Inference with ChatGPT model
sh run_qa_pipeline_multithread.sh ${backbone_model} ${method} ${test_set} ""

# Inference with trained llama model
sh run_qa_pipeline_multithread.sh ${backbone_model} ${method} ${test_set} ${llama_model_server_url}
```

最后再给一个我们的方法的示例

## Performance Evaluation
First please convert the answer into GPT evaluatable format.
```bash
sh run_convert_answer.sh ${candidate_dir} 
```

### Solvable Pass Rate
```bash
sh run_pass_rate.sh ${candidate_dir} ${test_set}
```

### Solvable Win Rate
```bash
sh run_preference.sh ${candidate_dir} ${test_set}
```

### Time and Token Cost
```bash
# step cost
python step_calculate.py

# Time cost, prompt token cost and completion token cost
python time_token_cost.py
```

整体步骤看起来有点乱，按执行顺序来说明吧
