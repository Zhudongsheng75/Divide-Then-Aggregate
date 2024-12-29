<div align= "center">
    <h1>DTA-Llama Server</h1>
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
   - For llama2. Note: llama2-13b needs more gpu memory, so we can specify cuda_device=0,1 or more
    ```bash
    export CUDA_VISIBLE_DEVICES=$1
    python llama_server.py --llama_model_path=$2 \
                              --llama_template=tool-llama-parallel \
                              --llama_device=cuda:0 \
                              --port=8899 
    ```
   - For llama3
   ```bash
   export CUDA_VISIBLE_DEVICES=$1
   python llama_server.py --llama_model_path=$2 \
                          --llama_template=tool-llama-parallel \
                          --llama_device=cuda:0 \
                          --port=8899 
   ```