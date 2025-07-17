import json


def load_taxonomy(taxonomy_name: str):
    with open(f"resources/{taxonomy_name}_taxonomy.json") as f:
        stages_steps_taxonomy = json.load(f)
        return [v for s in stages_steps_taxonomy.values() for v in s]
