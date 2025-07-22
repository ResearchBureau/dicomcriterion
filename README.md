# DICOM Criterion

[![CI](https://github.com/ResearchBureau/dicomcriterion/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/ResearchBureau/dicomcriterion/actions/workflows/build.yml?query=branch%3Amain)
[![PyPI](https://img.shields.io/pypi/v/dicomcriterion)](https://pypi.org/project/dicomcriterion/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dicomcriterion)](https://pypi.org/project/dicomcriterion/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)


A Python library for creating and evaluating boolean expressions against DICOM datasets. Build flexible validation rules using intuitive syntax to filter, validate, and process medical imaging data.

## Quick Start

```python
from pydicom import Dataset
from dicomcriterion import Criterion

# Create a sample DICOM dataset
dataset = Dataset()
dataset.PatientName = "John Doe"
dataset.StudyDescription = "Brain MRI with contrast"
dataset.Modality = "MR"

# Create validation criteria
criterion = Criterion("PatientName.equals('John Doe') and StudyDescription.contains('MRI')")

# Evaluate against dataset
result = criterion.evaluate(dataset)  # Returns True
```

## Key Features

- **Simple syntax**: Write validation rules using natural boolean expressions
- **Built-in functions**: `equals()`, `contains()`, `exists()` for common validations
- **Boolean operators**: Combine rules with `and`, `or`, `not`, and parentheses
- **Extensible**: Add custom validation functions for specialized requirements

## Installation

```bash
pip install dicomcriterion
```

## Credits
This package was created with the [kiro](https://kiro.dev/) editor.