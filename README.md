# pyFAT
A Python package which does FAIR assessment. 

## Installation
```bash
uv build
uv pip install <location to whl file>
```

## How to use

1. Make sure that you have `settings.toml` file in the root directory of your project. 
```python
import json
from pyfat import __main__ as fat
if __name__ == '__main__':
    variable_dict = {"FACETS": json.load(open("c4deaedf1c1b.json"))}
    res = fat.evaluate("tests/resources/cmdi/rename_later.xml", variable_dict)
    # facet: Fair Score -> into VLO
    print(res.score)

    # Dump res into TTL file
    print(res)
```


See the specs WIP:
https://docs.google.com/document/d/1iZ_c6WQeBLvzkuN9FBi6BCLs1cBbgPNJ_G3-AxcJHPY


### NOTES:
To export the toml file to a requirements.txt file:
  - $ poetry export -f requirements.txt --output requirements.txt --without-hashes   