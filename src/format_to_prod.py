import json

def format(student_id: int):
    with open(f"out/data/corpus_students/student_{student_id}.json") as f:
        data = json.load(f)

    res: list[dict[str, str]] = []
    for step in data:
        for t in step["tasks"]:
            res.append({"parser_element_id": t["id"], "step_name": step["name"], "algo_name": t["algoName"], "algo_family": t["algoFamily"]})

    with open(f"out/data/corpus_students/student_{student_id}_compatible_reimport.json", "w") as f:
        json.dump(res, f)

if __name__ == '__main__':
    import os
    format(os.getenv("STUDENT_ID"))
