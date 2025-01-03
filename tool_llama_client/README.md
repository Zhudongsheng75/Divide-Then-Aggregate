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
    - Base Model
    - Train the model
- Inference
  - The Virtual API Server
    - The folder structure
    - Running the server
    - Testing the Server
  - Inference and Evaluation
    - output folder structure
    - Inference answers
    - Performance Evaluation

Welcome to **Divide-Then-Aggregate**: An Efficient Tool Learning Method via Parallel Tool Invocation.

# Features
- We transformed the serial data into a DAG format, contributing a high-quality and high-quantity parallel tool invocation dataset to the open-source community.
- A new tool invocation framework has been established, transforming invocation into Process/Threads format. This, along with the parallel paradigm, significantly simplifies the trajectories of tool invocation, enhancing efficiency
while reducing unnecessary noise.
- The experiments comprehensively verified the superiority of our method from three aspects: tool invocation effectiveness, computational
cost, and generalization ability.

# Train
## Dataset
The dataset is refined from the train data in ToolBench. We fix the error steps and use ChatGPT to recognize 
if the tool execution step can be parallel, separate the tool execution step into parallelable and non-parallelable and 
finally merge the dataset into a train dataset.

We provide our train dataset [download link](https://huggingface.co/datasets/dongsheng/DTA-Tool).

## Model Training
### Base Model
We here provide the base model download link:
- Llama-2-7b-hf: https://huggingface.co/meta-llama/Llama-2-7b-hf
- Llama-2-13b-hf: https://huggingface.co/meta-llama/Llama-2-13b-hf
- Llama-3-8b-hf: https://huggingface.co/meta-llama/Meta-Llama-3-8B

### Train the model

There are some important parameters for training:
- data_path: the train dataset downloaded above
- eval_data_path: the eval dataset downloads from the `Data Release` section of [ToolBench](https://github.com/OpenBMB/ToolBench?tab=readme-ov-file) named `toolllama_G123_dfs_eval.json`. However, since this part of the data has not been parallelized, it is not recommended to refer to the results of the eval_data.
- conv_template: The conversation template for training. For better performance, we split each 
multi-turn conversation in the dataset into single-turn conversations and mask the output of the last assistant response.
Here we have to kinds of conversation templates for llama2 and llama3 respectively to adapt to their different，
tokenization:
  - llama2: tool-llama-single-round
  - llama3: tool-llama3-parallel

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

### The folder structure
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

### Running the server
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
## Inference and Evaluation

### output folder structure
To running the inference, we need to prepare the data as following:
```
├── /data/
│  └── /toolenv/
```
`toolenv` is also downloaded from the `Data Release` of [ToolBench](https://github.com/OpenBMB/ToolBench?tab=readme-ov-file).

The overall output structure:
```
output/
├── answer/
│   ├── chatgpt_function_CoT@1
│   │   ├── G1_instruction/
│   │   │   ├── 28_CoT@1.json
│   │   │   └── 100_CoT@1.json
│   │   ├── G2_instruction/
│   │   ├── G3_instruction/
│   │   ├── G1_category/
│   │   ├── G2_category/
│   │   └── G1_tool/
│   └── toollama_net_DFS_woFilter_w2_llama2_7b/
│   │   ├── .../
│   │   └── .../
│   │      ├── 28_DFS_woFilter_w2_llama2_7b.json
│   │      └── 100_DFS_woFilter_w2_llama2_7b.json
├── model_predictions_converted/
│   ├── chatgpt_function_CoT@1/
│   └── toollama_net_DFS_woFilter_w2_llama2_7b/
├── pass_rate_results/
│   ├── chatgpt_function_CoT@1/
│   └── toollama_net_DFS_woFilter_w2_llama2_7b/
├── preference_results
│   ├── G1_instructio/
│   ├── .../
└── └── G1_tool/
```


### Inference answers

Before inferencing the answers, we would like to introduce the parameters
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
- **llama_model_server_url**  
The url of the tool_llama_server.
  - serial(baseline): http://{ip}:{port}/llama_parse
  - parallel(ours): http://{ip}:{port}/llama_parse_parallel

Based on the parameter values above, run the following command to inference answers:
```bash
# Inference with ChatGPT model
sh run_qa_pipeline_multithread.sh ${backbone_model} ${method} ${test_set} ""

# Inference with trained llama model
sh run_qa_pipeline_multithread.sh ${backbone_model} ${method} ${test_set} ${llama_model_server_url}

# Here is an example for ours method (DTA-llama)
sh run_qa_pipeline_multithread.sh toolllama_net DFS_parallel_llama_woFilter_w2 http://10.17.202.221:8876/llama_parse_parallel
```

### Performance Evaluation

This part of the code mainly comes from the StableToolEval section within [StableToolBench](https://github.com/THUNLP-MT/StableToolBench). The relevant configurations can be resolved by referring to the corresponding documents.

1. Convert the answer into GPT evaluatable format.
```bash
sh run_convert_answer.sh ${candidate_dir} 
```

2. Evaluate **Solvable Pass Rate**
```bash
sh run_pass_rate.sh ${candidate_dir} ${test_set}
```

3. Evaluate **Solvable Win Rate**
```bash
sh run_preference.sh ${candidate_dir} ${test_set}
```

4. Evaluate **Time and Token Cost**
```bash
# step cost
python step_calculate.py

# Time cost, prompt token cost and completion token cost
python time_token_cost.py
```

