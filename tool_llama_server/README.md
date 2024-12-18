<div align= "center">
    <h1>DTA-Llama</h1>
</div>

# Introduction
This project is buildt as the inference server so that we can deploy the model in a machine with powerful GPUs and run the inference
client script in a machine with network connection to openAI.

# Run the server
1. install the requirements
```bash
# for llama2
pip install -r requirements.txt

# for llama3
pip install -r requirements_llama3.txt
```
2. start the server
The model_path is the path to the trained model output directory.
```bash
# llama2. Note: llama2-13 needs more gpu memory, so we can specify cuda_device=0,1 or more
sh run_server.sh ${cuda_device} ${model_path}

# llama3
sh run_server_llama3.sh ${cuda_device} ${model_path}

```