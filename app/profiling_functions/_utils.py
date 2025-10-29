from pathlib import Path

from pydantic import BaseModel

from app.custom_types import SupportedTaxonomiesFunction


class TaxonomyElement(BaseModel):
    compatible_name: str
    original_name: str
    definition: str
    stage: str


class Taxonomy(BaseModel):
    name: SupportedTaxonomiesFunction
    elements: list[TaxonomyElement]

    def get_original_steps_names(self) -> list[str]:
        return [e.original_name for e in self.elements]

    def get_compatible_steps_names(self) -> list[str]:
        return [e.compatible_name for e in self.elements]

    def get_original_name_from_compatible(
        self, compatible_name: str, default_name: str
    ):
        for e in self.elements:
            if e.compatible_name == compatible_name:
                return e.original_name
        return default_name


def load_taxonomy(taxonomy_name: SupportedTaxonomiesFunction) -> Taxonomy:
    raw_taxonomy = Path(
        f"resources/taxonomies/{taxonomy_name}_taxonomy.json"
    ).read_text()
    return Taxonomy.model_validate_json(raw_taxonomy)
