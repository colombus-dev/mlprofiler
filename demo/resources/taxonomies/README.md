# Supported "steps" Taxonomies

## Taxonomies list

### Headergen

*Note: This is the adapted taxonomy of HeaderGen with less overlapping*

#### Source

* **article**: VENKATESH, Ashwin Prasad Shivarpatna, WANG, Jiawei, LI, Li, et al. Enhancing comprehension and navigation
  in jupyter notebooks with static analysis. In : 2023 IEEE international Conference on software analysis, evolution and
  reengineering (SANER). IEEE, 2023. p. 391-401.

* **code
  **: https://github.com/secure-software-engineering/HeaderGen/blob/1ea52265ca4e76bb202a2deb26f3b9394d3caa95/framework_models/\_\_init\_\_.py#L28

### DSPipelines

#### Source

* **article**: BISWAS, Sumon, WARDAT, Mohammad, et RAJAN, Hridesh. The art and practice of data science pipelines: A
  comprehensive study of data science pipelines in theory, in-the-small, and in-the-large. In : Proceedings of the 44th
  International Conference on Software Engineering. 2022. p. 2091-2103.

* **code
  **: https://github.com/sumonbis/DS-Pipeline/blob/7684ef7f790da2c26a4567fe88840dafaabc446e/src/pipeline-generator.py#L110

### DASWOW

#### Source

* **article**: RAMASAMY, Dhivyabharathi, SARASUA, Cristina, BACCHELLI, Alberto, et al. Workflow analysis of data science
  code in public GitHub repositories. Empirical Software Engineering, 2023, vol. 28, no 1, p. 7.

* **code**: https://zenodo.org/records/7109939

## Add a new taxonomy

1. Update this README.md by specifying the taxonomy name, related article and code links.

2. Create a new JSON file in the current directory following the naming convention **{taxonomy-name}_taxonomy.json**.
   This JSON content should be a dictionary with the following format (stage_name can be the same as step_name):

```json
{"stage_name": ["step_a_name", "step_b_name", ...], ...}
```

3. Create a new Jinja2 template file in the [templates/](../../templates/) directory for the user prompt following the
   naming convention **user_prompt_{taxonomy-name}_taxonomy.jinja**. The template content should match the following
   format:

```
The {{ steps_taxonomy|length }} categories are {{ steps_taxonomy }}.

Each category is explained below:

[...]

If you can't tell what it is, say Other.

Code snippet:

```python
{{ python_code_line }}
.```

The classification for the given code snippet is:
```

Fill [...] with any additional details and explanations (e.g., as the definition of each class). Also, remove the dot
before ``` in the code snippet.
