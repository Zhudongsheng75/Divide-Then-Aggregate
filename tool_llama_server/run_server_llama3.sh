export CUDA_VISIBLE_DEVICES=$1
python llama_server.py --llama_model_path=./hf_model/toollama_13b_sub_single/4ep/ \
                          --llama_template=tool-llama-parallel \
                          --llama_device=cuda:0 \
                          --port=8899
