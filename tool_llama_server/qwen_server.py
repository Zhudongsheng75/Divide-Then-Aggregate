import torch
import argparse
from flask import Flask, request, jsonify

from inference.LLM.tool_qwen_model import ToolLLaMA

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return "Hello World!"


@app.route("/qwen2_parse_parallel", methods=["POST"])
def qwen2_parse_parallel():
    # 获取JSON请求数据
    data = request.get_json()

    llm.change_messages(data["messages"])
    output = llm.qwen2_parse_parallel(functions=data["functions"], process_id=0)

    response_data = {"data": output}
    return jsonify(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8555, help="Port number for the Flask server")
    # tool-llama
    parser.add_argument("--llama_model_path", type=str, required=True, help="Path to the tool-llama model file")
    parser.add_argument(
        "--llama_template",
        type=str,
        required=False,
        default="tool-llama-single-round",
        help="conversation template，一般无需修改",
    )
    parser.add_argument(
        "--llama_device", type=str, required=False, default="cuda:0", help="Device to use for inference"
    )
    parser.add_argument(
        "--max_source_sequence_length",
        type=int,
        default=4096,
        required=False,
        help="original maximum model sequence length",
    )
    parser.add_argument(
        "--max_sequence_length", type=int, default=8192, required=False, help="maximum model sequence length"
    )
    # retriever
    parser.add_argument("--corpus_tsv_path", type=str, default="", help="默认不需要，只有在open-domain下才需要指定")
    parser.add_argument("--retriever_model_path", type=str, required=True, help="Path to the retriever model file")
    parser.add_argument("--retriever_device", type=str, required=False, default="cuda:1", help="")

    args = parser.parse_args()
    llm = ToolLLaMA(args.llama_model_path, args.llama_template, args.llama_device)

    print("Model loaded successfully")

    app.run(host="0.0.0.0", debug=False, use_reloader=False, port=args.port)
