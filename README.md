<p align="center"></p>
<h2 align="center">Cyclic Classes</h2>
<p align="center">
<a href="https://github.com/rgryta/Cyclic-Classes/actions/workflows/main.yml"><img alt="Python package" src="https://github.com/rgryta/Cyclic-Classes/actions/workflows/main.yml/badge.svg?branch=main"></a>
<a href="https://pypi.org/project/cyclic-classes/"><img alt="PyPI" src="https://img.shields.io/pypi/v/cyclic-classes"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://github.com/PyCQA/pylint"><img alt="pylint" src="https://img.shields.io/badge/linting-pylint-yellowgreen"></a>
<a href="https://github.com/rgryta/NoPrint"><img alt="NoPrint" src="https://img.shields.io/badge/NoPrint-enabled-blueviolet"></a>
</p>

## About

Ever had a situation when you wanted to create a cyclic reference between two objects, but don't want to maintain a large singular file?
You're tired of seeing "cyclic-import" errors? This package is for you!
Simply "register" a class you want to share between different modules and you're pretty much good to go!

See the [documentation](https://github.com/rgryta/Cyclic-Classes/#Usage) for more information.

## Requirements

There's ***NONE!***

## Installation

Pull straight from this repo to install manually or just use pip: `pip install cyclic-classes` will do the trick.

## Usage

Consider a package `myk8s` with two modules, maybe one is to reference a k8s deployment and the other one is for pods within that deployment.


`deployment.py`
```python
from .pod import Pod

class Deployment:
    def __init__(self, name: str):
        self.name = name
    
    @property
    def pods(self):
        return [Pod(f"{self.name}-pod-{i}") for i in range(3)]
```

Now, if you want to create a back-reference for Deployment within Pod, like this:
`pod.py`
```python
from .deployment import Deployment

class Pod:
    def __init__(self, name: str):
        self.name = name
        
    @property
    def deployment(self):
        return Deployment(self.name.split("-")[0])
```

In the above example, you would get a cyclic-import error. To avoid this, you can use `cyclic_classes` to register the classes you want to share between modules.
Do so like this:

`deployment.py`
```python
from cyclic_classes import register, cyclic_import

with cyclic_import():  # This is required to avoid cyclic-import errors - you're actually importing a registered class underneath, but IDE will think it's your actual class
    from .pod import Pod

@register  # You have to register the class you want to access so that Pod will also be able to use it in the pod.py file
class Deployment:
    def __init__(self, name: str):
        self.name = name
    
    @property
    def pods(self):
        return [Pod(f"{self.name}-pod-{i}") for i in range(3)]
```

Now, if you want to create a back-reference for Deployment within Pod, like this:
`pod.py`
```python
from cyclic_classes import register, cyclic_import

with cyclic_import():
    from .deployment import Deployment

@register  # Making Pod available to cyclic_import
class Pod:
    def __init__(self, name: str):
        self.name = name
        
    @property
    def deployment(self):
        return Deployment(self.name.split("-")[0])
```

And that's it! You can now use the classes in your code without any issues.

### Note

Cyclic import supports multiple ways of imports, including relative imports, absolute imports, and even module imports.
As such, in the `cyclic_import` context you can use either of the following:

```python
import myk8s.deployment as depl  # And later use depl.Deployment
from .deployment import Deployment
from myk8s.deployment import Deployment

# Not recommended, but also possible
# Reason: Such imports wouldn't work even if there was no cyclic import issue, but it works with cyclic import (you'll get a warning though) and some IDEs think it's correct 
from deployment import Deployment
import deployment
```

This also works with aliases! So feel free to use `import ... as ...` or `from ... import ... as ...` as you wish.

## Development

### Installation

Install virtual environment and cyclic_classes package in editable mode with dev dependencies.

```bash
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
```


### Formatting

Use black and isort (with black profile) to format the code.

```bash
isort .
black .
```

### Syntax checks

Use pylint to check the code for errors and potential problems.
Also use noprint to detect print statements in the code (use logging instead!).

```bash
isort -c .
black --check .
pylint cyclic_classes tests tests/packages/**/cc_one tests/packages/**/cc_two
noprint -ve cyclic_classes tests
```

### Testing

For testing use coverage with pytest workers - this is due to errors that pytest-cov sometimes has with Python 3.9 and above.

```bash
coverage run -m pytest -xv tests
coverage report -m --fail-under=30
coverage erase
```

### Clean up

Clean up the project directory from temporary files and directories. Purge virual environment.

```bash
coverage erase
rm -rf cyclic_classes.egg-info/ dist/ build/
rm -rf venv/
```
