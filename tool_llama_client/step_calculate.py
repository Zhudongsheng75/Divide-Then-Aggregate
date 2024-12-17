import json
import os
import pandas as pd

cols = ["name", "G1_instruction", "G1_category", "G1_tool", "G2_category", "G2_instruction", "G3_instruction"]


def calculate(input_file):
    results = {}
    subdirectories = [f.path for f in os.scandir(input_file) if f.is_dir()]
    for subdir in subdirectories:
        candidate = os.path.basename(subdir)
        results[candidate] = {}
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++")
        print(f"now is processing {subdir}")
        subfolders = [f.name for f in os.scandir(subdir) if f.is_dir()]
        for test_set in subfolders:
            print(f"now is processing {test_set}")
            subfolder = os.path.join(subdir, test_set)
            totoal_step = []
            for filename in os.listdir(subfolder):
                file_path = os.path.join(subfolder, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.loads(f.read())
                    totoal_step.append(data["answer_generation"]["query_count"])
            res_str = f"avg: {round(0 if len(totoal_step) == 0 else sum(totoal_step) / len(totoal_step),2)}\nmin: {0 if len(totoal_step) == 0 else min(totoal_step)}\nmax: {0 if len(totoal_step) == 0 else max(totoal_step)}"

            results[candidate][test_set] = res_str

    final_results = []
    for key, value in results.items():
        value.update({"name": key})
        final_results.append(value)
    df = pd.DataFrame(final_results)
    df = df[cols]
    df.to_excel("output/data/answer_steps.xlsx", index=False)


if __name__ == "__main__":
    input_file = "output/data/answer"
    calculate(input_file)
