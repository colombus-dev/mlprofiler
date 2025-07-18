import json

from app.custom_types import SupportedTaxonomiesFunction


def load_taxonomy(taxonomy_name: SupportedTaxonomiesFunction) -> list[str]:
    with open(f"resources/taxonomies/{taxonomy_name}_taxonomy.json") as f:
        stages_steps_taxonomy = json.load(f)
        return [v for s in stages_steps_taxonomy.values() for v in s]
