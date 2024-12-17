cd toolbench/tooleval
export RAW_ANSWER_PATH=../../output/data/answer
export CONVERTED_ANSWER_PATH=../../output/data/model_predictions_converted
export MODEL_NAME="$1"

for test_set in G1_category G2_category G1_tool G1_instruction G2_instruction G3_instruction; do
    echo "convert ${test_set}"
    export test_set=${test_set}

    mkdir -p ${CONVERTED_ANSWER_PATH}/${MODEL_NAME}
    answer_dir=${RAW_ANSWER_PATH}/${MODEL_NAME}/${test_set}
    output_file=${CONVERTED_ANSWER_PATH}/${MODEL_NAME}/${test_set}.json

    # method填写DFS或者CoT
    python convert_to_answer_format.py\
        --answer_dir ${answer_dir} \
        --method DFS \
        --output ${output_file}
done