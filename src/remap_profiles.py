import json

def remap(student_id: int):
    with open(f"data/corpus_students/student_{student_id}_subgraph.json") as f:
        parser_profil = json.load(f)

    with open(f"out/data/corpus_students/student_{student_id}_compatible_reimport.json") as f:
        llm_profil = json.load(f)

    assert len(parser_profil["elements"]) == len(llm_profil)

    # Sort parser elements by line_start, start_pos, and end_pos for more precise matching
    sorted_parser_elements = sorted(
        parser_profil["elements"],
        key=lambda sg: (sg["line_start"], sg.get("start_pos", 0), sg.get("end_pos", 0))
    )

    # Map elements based on sorted parser elements and original LLM profil order
    # We assume the LLM profil is already in the correct order
    # TODO: Check in the llm profiling function the order
    for i, element in enumerate(sorted_parser_elements):
        if i < len(llm_profil):
            llm_profil[i]["parser_element_id"] = element["id"]

    with open(f"out/data/corpus_students/student_{student_id}_llm_final.json", "w") as f:
        json.dump({"profile": llm_profil}, f)
    return {"profile": llm_profil}

if __name__ == '__main__':
    import os
    remap(os.getenv("STUDENT_ID"))
