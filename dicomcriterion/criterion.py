"""Core Criterion class for DICOM boolean expression evaluation."""

import re
from typing import Dict, Optional, Set

import pydicom
from boolean import BooleanAlgebra, Symbol

from .exceptions import ExpressionParseError, SymbolParseError
from .functions import FunctionRegistry, default_registry
from .symbol import DicomSymbol


class Criterion:
    """Boolean expression evaluator for DICOM attributes.

    The Criterion class provides a flexible way to define and evaluate boolean
    expressions for DICOM attribute validation. It supports complex expressions
    with logical operators (and, or, not) and parentheses for grouping, using
    specialized functions to validate DICOM attributes.

    Supported Functions
    ------------------
    equals(value) : Check if DICOM attribute equals a specific value
    contains(substring) : Check if DICOM attribute contains a substring
    exists() : Check if DICOM attribute is present in the dataset

    Expression Syntax
    ----------------
    - Use standard boolean operators: 'and', 'or', 'not'
    - Use parentheses for grouping: '(condition1 or condition2) and condition3'
    - DICOM symbols format: 'attribute.function(argument)'
    - String arguments should be quoted: "PatientName.equals('John Doe')"

    Examples
    --------
    Simple equality check:
    >>> criterion = Criterion("PatientName.equals('John Doe')")
    >>> result = criterion.evaluate(dataset)

    Complex expression with multiple conditions:
    >>> expression = "(PatientName.equals('John') or
    PatientName.equals('Jane')) and StudyDescription.contains('MRI')"
    >>> criterion = Criterion(expression)
    >>> result = criterion.evaluate(dataset)

    Checking for attribute existence:
    >>> criterion = Criterion("PatientID.exists() and StudyDate.exists()")
    >>> result = criterion.evaluate(dataset)

    Using NOT operator:
    >>> criterion = Criterion("not PatientName.equals('Anonymous')")
    >>> result = criterion.evaluate(dataset)

    Parameters
    ----------
    expression : str
        Boolean expression string containing DICOM attribute functions
    registry : FunctionRegistry, optional
        Custom function registry. If None, uses the default registry with
        equals, contains, and exists functions.

    Raises
    ------
    ExpressionParseError
        If the expression syntax is invalid or cannot be parsed
    SymbolParseError
        If DICOM symbols in the expression have invalid format
    FunctionNotFoundError
        If the expression references unregistered functions

    See Also
    --------
    DicomSymbol : Individual DICOM attribute expressions
    FunctionRegistry : Registry for managing validation functions
    DicomFunction : Base class for creating custom validation functions
    """

    def __init__(
        self, expression: str, registry: Optional[FunctionRegistry] = None
    ) -> None:
        """Initialize Criterion with a boolean expression string.

        Parameters
        ----------
        expression : str
            Boolean expression string containing DICOM attribute functions
        registry : FunctionRegistry, optional
            Function registry to use for validation. If None, uses default registry.

        Raises
        ------
        ExpressionParseError
            If the expression cannot be parsed
        SymbolParseError
            If DICOM symbols in the expression are invalid
        """
        self._expression = expression.strip()
        self._registry = registry or default_registry
        self._algebra = BooleanAlgebra()

        # Extract and validate DICOM symbols from the expression
        self._dicom_symbols = self._extract_dicom_symbols(self._expression)

        # Create mapping from DICOM symbols to boolean.py symbols
        self._symbol_mapping: Dict[str, DicomSymbol] = {}
        boolean_symbols: Dict[str, Symbol] = {}

        for dicom_symbol in self._dicom_symbols:
            # Validate the DICOM symbol and convert to boolean symbol
            boolean_symbol = dicom_symbol.to_boolean_symbol(self._registry)
            symbol_key = str(boolean_symbol)

            self._symbol_mapping[symbol_key] = dicom_symbol
            boolean_symbols[symbol_key] = boolean_symbol

        # Replace DICOM symbols in expression with boolean.py symbol names
        boolean_expression = self._convert_to_boolean_expression(
            self._expression, self._dicom_symbols, boolean_symbols
        )

        # Parse the boolean expression using boolean.py
        try:
            self._parsed_expression = self._algebra.parse(
                boolean_expression, simplify=False
            )
        except Exception as e:
            raise ExpressionParseError(
                self._expression, f"Failed to parse boolean expression: {str(e)}"
            ) from e

    def evaluate(self, dataset: pydicom.Dataset) -> bool:
        """Evaluate the boolean expression against a DICOM dataset.

        This method evaluates the parsed boolean expression by checking each
        DICOM symbol against the provided dataset and combining the results
        according to the boolean logic defined in the expression.

        Parameters
        ----------
        dataset : pydicom.Dataset
            DICOM dataset to evaluate against. The dataset should contain
            the DICOM attributes referenced in the expression.

        Returns
        -------
        bool
            True if the boolean expression evaluates to True when applied
            to the dataset, False otherwise.

        Raises
        ------
        EvaluationError
            If expression evaluation fails due to dataset access errors,
            invalid attribute types, or other evaluation issues.

        Examples
        --------
        >>> from pydicom import Dataset
        >>> dataset = Dataset()
        >>> dataset.PatientName = "John Doe"
        >>> dataset.StudyDescription = "Brain MRI"
        >>>
        >>> criterion = Criterion("PatientName.equals('John Doe')")
        >>> result = criterion.evaluate(dataset)  # Returns True
        >>>
        >>> criterion = Criterion("StudyDescription.contains('CT')")
        >>> result = criterion.evaluate(dataset)  # Returns False
        """
        try:
            # Get all symbols from the parsed expression
            expression_symbols = self._parsed_expression.get_symbols()

            # Create a mapping of Symbol objects to their evaluated values
            symbol_values = {}

            for symbol in expression_symbols:
                symbol_key = str(symbol)

                # Find the corresponding DICOM symbol
                if symbol_key in self._symbol_mapping:
                    dicom_symbol = self._symbol_mapping[symbol_key]

                    # Evaluate the DICOM symbol against the dataset
                    dicom_result = dicom_symbol.evaluate(dataset, self._registry)

                    # Convert Python boolean to boolean.py TRUE/FALSE
                    if dicom_result:
                        symbol_values[symbol] = self._algebra.TRUE
                    else:
                        symbol_values[symbol] = self._algebra.FALSE
                else:
                    # This shouldn't happen if our implementation is correct
                    raise ValueError(
                        f"Symbol {symbol_key} not found in " f"symbol mapping"
                    )

            # Evaluate the boolean expression using the symbol values
            result = self._parsed_expression.subs(symbol_values)

            # Simplify the result to get TRUE or FALSE
            simplified_result = result.simplify()

            # Check if the result is TRUE
            return bool(simplified_result == self._algebra.TRUE)

        except Exception as e:
            from .exceptions import EvaluationError

            raise EvaluationError(
                expression=self._expression,
                details=f"Failed to evaluate expression against dataset: {str(e)}",
            ) from e

    def __str__(self) -> str:
        """Return string representation of the criterion."""
        return f"Criterion('{self._expression}')"

    def __repr__(self) -> str:
        """Return detailed string representation of the criterion."""
        return f"Criterion(expression='{self._expression}')"

    def _extract_dicom_symbols(self, expression: str) -> Set[DicomSymbol]:
        """Extract DICOM symbols from a boolean expression string.

        Parameters
        ----------
        expression : str
            The boolean expression containing DICOM symbols

        Returns
        -------
        Set[DicomSymbol]
            Set of unique DICOM symbols found in the expression

        Raises
        ------
        SymbolParseError
            If any DICOM symbol has invalid format
        """
        # Pattern to match DICOM symbols: attribute.function(args)
        # This pattern captures the full symbol including parentheses and arguments
        pattern = r"([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\))"

        matches = re.findall(pattern, expression)
        dicom_symbols = set()

        for match in matches:
            try:
                dicom_symbol = DicomSymbol.parse(match)
                dicom_symbols.add(dicom_symbol)
            except SymbolParseError as e:
                # Re-raise with more context about where the error occurred
                raise SymbolParseError(
                    match, f"Invalid DICOM symbol found in expression: '{expression}'"
                ) from e

        if not dicom_symbols:
            raise ExpressionParseError(
                expression,
                "No valid DICOM symbols found. "
                "Expected format: 'attribute.function(args)'",
            )

        return dicom_symbols

    def _convert_to_boolean_expression(
        self,
        original_expression: str,
        dicom_symbols: Set[DicomSymbol],
        boolean_symbols: Dict[str, Symbol],
    ) -> str:
        """Convert DICOM expression to boolean.py compatible expression.

        Parameters
        ----------
        original_expression : str
            Original expression with DICOM symbols
        dicom_symbols : Set[DicomSymbol]
            Set of DICOM symbols to replace
        boolean_symbols : Dict[str, Symbol]
            Mapping of symbol keys to boolean.py Symbol objects

        Returns
        -------
        str
            Expression with DICOM symbols replaced by boolean.py symbol names
        """
        boolean_expression = original_expression

        # We need to find the original symbol strings in the expression
        # Use regex to find all DICOM symbols and replace them
        pattern = r"([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\))"

        def replace_symbol(match):
            original_symbol_str = match.group(1)

            # Parse the symbol to find the corresponding DicomSymbol
            try:
                parsed_symbol = DicomSymbol.parse(original_symbol_str)

                # Find the corresponding boolean symbol
                for symbol_key, symbol in boolean_symbols.items():
                    if self._symbol_mapping[symbol_key] == parsed_symbol:
                        return str(symbol)

                # If not found, return original (shouldn't happen)
                return original_symbol_str

            except Exception:
                # If parsing fails, return original
                return original_symbol_str

        boolean_expression = re.sub(pattern, replace_symbol, boolean_expression)
        return boolean_expression
