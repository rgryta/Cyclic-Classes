<p align="center"></p>
<h2 align="center">Cyclic Classes</h2>
<p align="center">
<a href="https://github.com/rgryta/Cyclic-Classes/actions/workflows/main.yml"><img alt="Python package" src="https://github.com/rgryta/Cyclic-Classes/actions/workflows/main.yml/badge.svg?branch=main"></a>
<a href="https://pypi.org/project/noprint/"><img alt="PyPI" src="https://img.shields.io/pypi/v/cyclic-classes"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://github.com/PyCQA/pylint"><img alt="pylint" src="https://img.shields.io/badge/linting-pylint-yellowgreen"></a>
<a href="https://github.com/rgryta/NoPrint"><img alt="NoPrint" src="https://img.shields.io/badge/NoPrint-enabled-blueviolet"></a>
</p>

## About

Do not allow prints in your python code anymore. Official repository of NoPrint package. Packages are scanned recursively.

## Requirements

There's ***NONE!***

## Installation

Pull straight from this repo to install manually or just use pip: `pip install cyclic-classes` will do the trick.

## Usage

```python
# TODO
```

## Development

To install the package in editable mode for development, run `pip install -e .[dev]` in the root directory of the repository.

To execute tests, you also need to install test packages from `tests/packages` directory.

### Formatting

```bash
isort .
black .
```

### Syntax checks

```bash
isort -c .
black --check .
pylint cyclic_classes tests/ tests/packages/**/cc_one tests/packages/**/cc_two
noprint -ve cyclic_classes
```

### Testing

```bash
coverage run -m pytest -xv tests
coverage report --fail-under=70
coverage erase
```
