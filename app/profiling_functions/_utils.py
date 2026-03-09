from pydantic import BaseModel


class TaxonomyElement(BaseModel):
    name: str
    definition: str


class Taxonomy(BaseModel):
    name: str
    elements: list[TaxonomyElement]

    def get_steps_names(self) -> list[str]:
        return [e.name for e in self.elements]
