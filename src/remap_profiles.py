import json

def remap(student_id: int):
    with open(f"data/corpus_students/student_{student_id}_subgraph.json") as f:
        parser_profil = json.load(f)

    with open(f"out/data/corpus_students/student_{student_id}_compatible_reimport.json") as f:
        llm_profil = json.load(f)

    for i, element in enumerate(sorted(parser_profil["elements"], key=lambda sg: sg["line_start"])):
        llm_profil[i]["parser_element_id"] = element["id"]

    with open(f"out/data/corpus_students/student_{student_id}_llm_final.json", "w") as f:
        json.dump({"profile": llm_profil}, f)
    return {"profile": llm_profil}

if __name__ == '__main__':
    import os
    remap(os.getenv("STUDENT_ID"))
