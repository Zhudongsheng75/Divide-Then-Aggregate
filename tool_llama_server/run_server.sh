#!/bin/bash

export CUDA_VISIBLE_DEVICES=$1
python llama_server.py --llama_model_path=$2 \
                          --llama_template=tool-llama-parallel \
                          --llama_device=cuda:0 \
                          --retriever_model_path=./hf_model/retriever/ \
                          --corpus_tsv_path=data/retrieval/G1/corpus.tsv  \
                          --retriever_device=cuda:0 \
                          --port=8899 \
