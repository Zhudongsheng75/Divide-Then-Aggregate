import argparse
from flask import Flask, request, jsonify

from inference.LLM.tool_llama3_model import ToolLLaMA

app = Flask(__name__)


@app.route("/llama_parse", methods=["POST"])
def llama_parse():
    # 获取JSON请求数据
    data = request.get_json()

    llm.change_messages(data["messages"])
    output = llm.parse(functions=data["functions"], process_id=0)

    return jsonify(output)


@app.route("/llama_parse_parallel", methods=["POST"])
def llama_parse_parallel():
    # 获取JSON请求数据
    data = request.get_json()

    llm.change_messages(data["messages"])
    output = llm.parse_parallel(functions=data["functions"], process_id=0)

    return jsonify(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8555, help="Port number for the Flask server")
    # tool-llama
    parser.add_argument("--llama_model_path", type=str, required=True, help="Path to the tool-llama model file")
    parser.add_argument(
        "--llama_template", type=str, required=False, default="tool-llama-single-round", help="conversation template"
    )
    parser.add_argument(
        "--llama_device", type=str, required=False, default="cuda:0", help="Device to use for inference"
    )

    args = parser.parse_args()
    llm = ToolLLaMA(args.llama_model_path, args.llama_template, args.llama_device)

    print("Model loaded successfully")

    app.run(host="0.0.0.0", debug=False, use_reloader=False, port=args.port)
