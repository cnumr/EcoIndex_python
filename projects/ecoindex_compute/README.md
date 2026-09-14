# Ecoindex python

[![Validate project quality](https://github.com/cnumr/ecoindex_python_fullstack/actions/workflows/quality_check.yml/badge.svg?branch=main)](https://github.com/cnumr/ecoindex_python_fullstack/actions/workflows/quality_check.yml)
![PyPI - Version](https://img.shields.io/pypi/v/ecoindex-compute?logo=pypi)
![PyPI - Downloads](https://img.shields.io/pypi/dm/ecoindex-compute?style=social&logo=pypi)

This basic module provides a simple interface to get the [Ecoindex](http://www.ecoindex.fr) based on 3 parameters:

- The number of DOM elements in the page
- The size of the page
- The number of external requests of the page

## Requirements

- Python ^3.10 with [pip](https://pip.pypa.io/en/stable/installation/)

## Install

```shell
pip install ecoindex_compute
```

## Use

### Compute ecoindex

You can easily compute the ecoindex by calling the function `compute_ecoindex()`:

```python
(function) compute_ecoindex: (dom: int, size: float, requests: int) -> Coroutine[Any, Any, Ecoindex]
```

Example:

```python
import asyncio
from pprint import pprint

from ecoindex.compute import compute_ecoindex

# Get ecoindex from DOM elements, size of page and requests of the page
ecoindex = asyncio.run(compute_ecoindex(nodes=100, size=100, requests=100))
pprint(ecoindex)
```

Result example:

```python
Ecoindex(grade='B', score=72.0, ges=1.56, water=2.34, ecoindex_version='3.0.0')
```
