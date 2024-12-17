cd  toolbench/tooleval
export API_POOL_FILE=../../openai_key.json
export CONVERTED_ANSWER_PATH=../../output/data/model_predictions_converted
export PASS_RATE_PATH=../../output/data/pass_rate_results
export REFERENCE_MODEL=chatgpt_function_CoT@1
export EVAL_MODEL=gpt-4-turbo-preview
export test_set=$2
export CANDIDATE_MODEL=$1
export SAVE_PATH=../../output/data/preference_results/${test_set}
mkdir -p ${SAVE_PATH}


python eval_preference.py \
    --converted_answer_path ${CONVERTED_ANSWER_PATH} \
    --reference_model ${REFERENCE_MODEL} \
    --output_model ${CANDIDATE_MODEL} \
    --test_ids ../../solvable_queries/test_query_ids \
    --save_path ${SAVE_PATH} \
    --pass_rate_result_path ${PASS_RATE_PATH} \
    --max_eval_threads 1 \
    --use_pass_rate true \
    --evaluate_times 3 \
    --test_set ${test_set} \
#    --overwrite