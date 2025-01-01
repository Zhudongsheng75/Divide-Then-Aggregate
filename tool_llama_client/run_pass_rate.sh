cd  toolbench/tooleval
export API_POOL_FILE=../../openai_key.json
export CONVERTED_ANSWER_PATH=../../output/model_predictions_converted
export SAVE_PATH=../../output/pass_rate_results
mkdir -p ${SAVE_PATH}
export CANDIDATE_MODEL="$1"
export EVAL_MODEL=gpt-4-turbo-preview
mkdir -p ${SAVE_PATH}/${CANDIDATE_MODEL}
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy

python eval_pass_rate.py \
    --converted_answer_path ${CONVERTED_ANSWER_PATH} \
    --save_path ${SAVE_PATH}/${CANDIDATE_MODEL} \
    --reference_model ${CANDIDATE_MODEL} \
    --test_ids ../../solvable_queries/test_query_ids \
    --max_eval_threads 1 \
    --evaluate_times 3 \
    --test_set  $2 \
    --overwrite