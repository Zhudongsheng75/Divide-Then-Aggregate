<div align= "center">
    <h1>DTA-Llama</h1>
</div>

<div align="center">

</div>

# How to use
In this project, there are two sub-projects naming `tool_llama_client` and `tool_llama_server`. The `tool_llama_client` contains 
training scrips and inference parts, while we keep the model prediction part in `tool_llama_server` so that we can deploy the model in a machine with powerful GPUs and run the inference
client script in a machine with network connection to openAI.

Please following the `Readme.md` in each sub-project.
- `tool_llama_client`: training, running the inference client and eval the inference results.
- `tool_llama_server`: deploying the trained model, such as llama2-7b

# License
This repository's code is under [MIT License](LICENSE). Many codes are based on [ToolBench](https://github.com/OpenBMB/ToolBench) and [StableToolBench](https://github.com/THUNLP-MT/StableToolBench) with  Apache-2.0 License.
