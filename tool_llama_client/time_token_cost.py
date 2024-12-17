import json
import os
import pandas as pd

cols = ["name", "G1_instruction", "G1_category", "G1_tool", "G2_category", "G2_instruction", "G3_instruction"]


def calculate(input_file):
    token_record_dict = {}
    time_record_dict = {}
    subdirectories = [f.path for f in os.scandir(input_file) if f.is_dir()]
    for subdir in subdirectories:
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++")
        print(f"now is processing {subdir}")
        candidate = os.path.basename(subdir)
        token_record_dict[candidate] = {}
        time_record_dict[candidate] = {}
        files = [f for f in os.listdir(subdir) if os.path.isfile(os.path.join(subdir, f))]
        for subfile in files:
            test_set = subfile.split(".")[0]
            print(subfile)
            file_name = subfile.split(".")[0]
            totoal_step, totol_completion_tokens, total_prompt_tokens, total_cost_time = [], [], [], []
            with open(os.path.join(subdir, subfile), "r") as file:
                data = json.loads(file.read())
                for js in data.values():
                    totoal_step.append(js["answer"]["total_steps"])
                    totol_completion_tokens.append(js["answer"]["completion_tokens"])
                    total_prompt_tokens.append(js["answer"]["prompt_tokens"])
                    total_cost_time.append(js["answer"]["cost_time"])
            print(f"{file_name}: ")
            print(
                f"avg_completion: {sum(totol_completion_tokens)//len(totol_completion_tokens)}\tmin_completion: {min(totol_completion_tokens)}\tmax_completion: {max(totol_completion_tokens)}"
            )
            print(
                f"avg_prompt: {sum(total_prompt_tokens)//len(total_prompt_tokens)}\tmin_prompt: {min(total_prompt_tokens)}\tmax_prompt: {max(total_prompt_tokens)}"
            )
            print(
                f"avg_time: {sum(total_cost_time)//len(total_cost_time)}\t\tmin_cost: {round(min(total_cost_time), 2)}\t\tmax_cost: {round(max(total_cost_time), 2)}"
            )

            avg_completion = sum(totol_completion_tokens) // len(totol_completion_tokens)
            min_completion = min(totol_completion_tokens)
            max_completion = max(totol_completion_tokens)
            avg_prompt = sum(total_prompt_tokens) // len(total_prompt_tokens)
            min_prompt = min(total_prompt_tokens)
            max_prompt = max(total_prompt_tokens)
            token_record_dict[candidate][
                test_set
            ] = f"avg: {avg_completion}/{avg_prompt}\nmin: {min_completion}/{min_prompt}\nmax: {max_completion}/{max_prompt}"
            avg_time = sum(total_cost_time) // len(total_cost_time)
            min_time = round(min(total_cost_time), 2)
            max_time = round(max(total_cost_time), 2)
            time_record_dict[candidate][test_set] = f"avg: {avg_time}\nmin: {min_time}\nmax: {max_time}"

    final_results = []
    for key, value in token_record_dict.items():
        value.update({"name": key})
        final_results.append(value)
    df = pd.DataFrame(final_results)
    df = df[cols]
    df.to_excel("output/data/token_results.xlsx", index=False)

    final_results = []
    for key, value in time_record_dict.items():
        value.update({"name": key})
        final_results.append(value)
    df = pd.DataFrame(final_results)
    df = df[cols]
    df.to_excel("output/data/time_results.xlsx", index=False)


if __name__ == "__main__":
    input_file = "output/data/model_predictions_converted"
    calculate(input_file)
