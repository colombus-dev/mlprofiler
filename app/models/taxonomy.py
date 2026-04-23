from enum import Enum

from pydantic import BaseModel


class TaxonomyFunction(str, Enum):
    DSPIPELINES = "dspipelines"
    DASWOW = "daswow"
    HEADERGEN = "headergen"


class TaxonomyElement(BaseModel):
    name: str
    definition: str


class Taxonomy(BaseModel):
    name: str
    elements: list[TaxonomyElement]
    default_step: str

    def get_steps_names(self) -> list[str]:
        return [e.name for e in self.elements]


DEFAULT_STEP_NAME = "Other"

TAXONOMY_BY_NAME = {
    TaxonomyFunction.DSPIPELINES.value: Taxonomy(
        name=TaxonomyFunction.DSPIPELINES.value,
        elements=[
            TaxonomyElement(
                name="Data Acquisition",
                definition="this code reads/loads new data",
            ),
            TaxonomyElement(
                name="Data Preparation",
                definition="the code contributes to the preparation of data so that it is suitable for further processing and analysis",
            ),
            TaxonomyElement(
                name="Modeling",
                definition="the code instantiates or builds a model",
            ),
            TaxonomyElement(
                name="Training",
                definition="the code trains a model",
            ),
            TaxonomyElement(
                name="Evaluation",
                definition="the code evaluates a model",
            ),
            TaxonomyElement(
                name="Prediction",
                definition="the code makes inference using a model",
            ),
            TaxonomyElement(
                name=DEFAULT_STEP_NAME,
                definition="",
            ),
        ],
        default_step=DEFAULT_STEP_NAME,
    ),
    TaxonomyFunction.DASWOW.value: Taxonomy(
        name=TaxonomyFunction.DASWOW.name,
        elements=[
            TaxonomyElement(
                name="helper_functions",
                definition="Code that is not directly related to the data science activity at hand, but provides useful scripting functions (e. g. importing or configuring libraries).",
            ),
            TaxonomyElement(
                name="load_data",
                definition="The process of loading a dataset of any type (e.g., .csv, .pkl) into a Jupyter notebook environment.",
            ),
            TaxonomyElement(
                name="data_preprocessing",
                definition="The process of preparing the dataset(s) for the subsequent analysis. It includes tasks such as cleaning, instance selection, normalisation, data transformation, and feature selection.",
            ),
            TaxonomyElement(
                name="data_exploration",
                definition="The process of inspecting the content and shape of a dataset to understand the nature and characteristics of the data. Note that it may involve the usage of visualisation techniques but differs in its purpose.",
            ),
            TaxonomyElement(
                name="modelling",
                definition="The process of applying statistical models and learning-based algorithms to learn from sample data.",
            ),
            TaxonomyElement(
                name="evaluation",
                definition="The process of assessing a model using one/various evaluation metric(s) such as goodness of fit and accuracy.",
            ),
            TaxonomyElement(
                name="model_inference",
                definition="The process of applying a model trained on a set of data to other or newly arriving pieces of data to forecast new values.",
            ),
            TaxonomyElement(
                name="result_visualization",
                definition="The process of obtaining a graphical representation (e.g., tables, plots, graphs) of a/several measurement(s).",
            ),
            TaxonomyElement(
                name="save_results",
                definition="The process of serialising and storing the data.",
            ),
            TaxonomyElement(
                name="comment_only",
                definition="Lines of comment including commented code.",
            ),
            TaxonomyElement(
                name=DEFAULT_STEP_NAME,
                definition="",
            ),
        ],
        default_step=DEFAULT_STEP_NAME,
    ),
    TaxonomyFunction.HEADERGEN.value: Taxonomy(
        name=TaxonomyFunction.HEADERGEN.name,
        elements=[
            TaxonomyElement(name="Library Loading", definition=""),
            TaxonomyElement(name="Visualization", definition=""),
            TaxonomyElement(name="Data Loading", definition=""),
            TaxonomyElement(name="Exploratory Data Analysis", definition=""),
            TaxonomyElement(name="Data Preparation", definition=""),
            TaxonomyElement(
                name="Data Sub-sampling and Train-test Splitting", definition=""
            ),
            TaxonomyElement(name="Feature Transformation", definition=""),
            TaxonomyElement(name="Feature Selection", definition=""),
            TaxonomyElement(name="Model Assembling", definition=""),
            TaxonomyElement(name="Model Parameter Tuning", definition=""),
            TaxonomyElement(name="Model Training", definition=""),
            TaxonomyElement(name="Model Validation", definition=""),
            TaxonomyElement(name=DEFAULT_STEP_NAME, definition=""),
        ],
        default_step=DEFAULT_STEP_NAME,
    ),
}
