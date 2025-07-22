"""DICOM Criterion - Boolean expressions for DICOM attribute validation.

This package provides a Criterion class that models boolean expressions
for DICOM attribute validation using the boolean.py library and pydicom.
"""

__version__ = "0.1.0"

from .criterion import Criterion
from .exceptions import (
    CriterionError,
    EvaluationError,
    ExpressionParseError,
    FunctionNotFoundError,
    SymbolParseError,
)
from .functions import (
    DicomFunction,
    EqualsFunction,
    ContainsFunction,
    ExistsFunction,
    FunctionRegistry,
    default_registry,
)
from .symbol import DicomSymbol

__all__ = [
    "Criterion",
    "ContainsFunction",
    "CriterionError",
    "DicomFunction",
    "DicomSymbol",
    "EqualsFunction",
    "ExistsFunction",
    "EvaluationError",
    "ExpressionParseError",
    "FunctionNotFoundError",
    "FunctionRegistry",
    "SymbolParseError",
    "default_registry",
]
