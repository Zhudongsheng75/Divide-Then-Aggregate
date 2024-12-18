export CUDA_VISIBLE_DEVICES=$1
python qwen_server.py --llama_model_path=/mnt/ailabtemp/zhudongsheng/models/models--Qwen--Qwen2.5-7B-Instruct \
                          --llama_template=tool-llama3-parallel \
                          --llama_device=cuda:0 \
                          --retriever_model_path=/mnt/ailabtemp/zhudongsheng/tool_learning/tool_llama_server/my_models/retriever \
                          --corpus_tsv_path=data/retrieval/G1/corpus.tsv  \
                          --retriever_device=cuda:0 \
                          --port=8899 \
