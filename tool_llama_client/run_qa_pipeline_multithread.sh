# Please fill the OPENAI_KEY and OPENAI_API_BASE when your backbone_model is based on ChatGPT
export OPENAI_KEY=""
export OPENAI_API_BASE=""

# The tool directory downloaded from ToolBench
export TOOL_DIR=""
# The toolbench key we applied by filling the form (https://forms.gle/oCHHc8DQzhGfiT9r6)
export TOOLBENCH_KEY=""

export GPT_MODEL="gpt-3.5-turbo-16k"
export SERVICE_URL="http://localhost:8080/virtual"

export BACKBONE_MODEL="$1"
export METHOD="$2"
export OUTPUT_DIR="output/answer/${BACKBONE_MODEL}_${METHOD}"
group=$3

mkdir -p $OUTPUT_DIR; mkdir -p $OUTPUT_DIR/$group

python toolbench/inference/qa_pipeline_multithread.py \
  --tool_root_dir $TOOL_DIR \
  --backbone_model $BACKBONE_MODEL \
  --openai_key $OPENAI_KEY \
  --max_observation_length 1024 \
  --method $METHOD \
  --input_query_file solvable_queries/test_instruction/${group}.json \
  --output_answer_file $OUTPUT_DIR/$group \
  --toolbench_key $TOOLBENCH_KEY \
  --num_thread 1 \
  --llama_server_url $4
