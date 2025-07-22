"""DICOM symbol parsing and conversion for boolean expressions."""

import re
from dataclasses import dataclass
from typing import Optional

import pydicom
from boolean import Symbol

from .exceptions import SymbolParseError, EvaluationError
from .functions import FunctionRegistry, default_registry


@dataclass(frozen=True)
class DicomSymbol:
    """Data class representing a parsed DICOM attribute expression.

    This class represents a DICOM attribute expression in the format:
    attribute.function(argument) or attribute.function()

    DicomSymbol objects are immutable and hashable, making them suitable
    for use in sets and as dictionary keys. They encapsulate the parsing
    and evaluation logic for individual DICOM attribute validation expressions.

    Attributes
    ----------
    attribute : str
        The DICOM attribute name (e.g., 'PatientName', 'StudyDescription')
    function : str
        The validation function name (e.g., 'equals', 'contains', 'exists')
    argument : str, optional
        The function argument, if any (None for functions like exists())

    Examples
    --------
    Equality check with argument:
    >>> symbol = DicomSymbol.parse("PatientName.equals('John Doe')")
    >>> symbol.attribute  # 'PatientName'
    >>> symbol.function   # 'equals'
    >>> symbol.argument   # 'John Doe'

    Substring search:
    >>> symbol = DicomSymbol.parse("StudyDescription.contains('MRI')")
    >>> result = symbol.evaluate(dataset)

    Existence check without argument:
    >>> symbol = DicomSymbol.parse("PatientID.exists()")
    >>> symbol.argument   # None

    See Also
    --------
    Criterion : Main class for boolean expression evaluation
    DicomFunction : Base class for validation functions
    """

    attribute: str
    function: str
    argument: Optional[str] = None

    @classmethod
    def parse(cls, symbol_str: str) -> "DicomSymbol":
        """Parse a DICOM symbol string into a DicomSymbol object.

        This method parses DICOM attribute expressions in the format
        'attribute.function(argument)' or 'attribute.function()' and
        returns a DicomSymbol object representing the parsed expression.

        Parameters
        ----------
        symbol_str : str
            The symbol string to parse (e.g., "PatientName.equals('John')")

        Returns
        -------
        DicomSymbol
            Parsed symbol object containing the attribute, function, and argument

        Raises
        ------
        SymbolParseError
            If the symbol format is invalid or doesn't match the expected pattern

        Examples
        --------
        >>> symbol = DicomSymbol.parse("PatientName.equals('John Doe')")
        >>> symbol.attribute  # 'PatientName'
        >>> symbol.function   # 'equals'
        >>> symbol.argument   # 'John Doe'

        >>> symbol = DicomSymbol.parse("PatientID.exists()")
        >>> symbol.argument   # None
        """
        # Remove whitespace
        symbol_str = symbol_str.strip()

        # Pattern to match: attribute.function(argument) or attribute.function()
        # This handles quoted strings, unquoted strings, and no arguments
        pattern = r"^([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]*)\)$"

        match = re.match(pattern, symbol_str)
        if not match:
            raise SymbolParseError(
                symbol_str,
                "Expected format: 'attribute.function(args)' where attribute "
                "and function are valid identifiers",
            )

        attribute, function, arg_str = match.groups()

        # Parse the argument
        argument = None
        if arg_str.strip():
            arg_str = arg_str.strip()

            # Handle quoted strings (single or double quotes)
            if (arg_str.startswith("'") and arg_str.endswith("'")) or (
                arg_str.startswith('"') and arg_str.endswith('"')
            ):
                argument = arg_str[1:-1]  # Remove quotes
            else:
                # Handle unquoted arguments
                argument = arg_str

        return cls(attribute=attribute, function=function, argument=argument)

    def to_boolean_symbol(self, registry: Optional[FunctionRegistry] = None) -> Symbol:
        """Convert DicomSymbol to a boolean.py Symbol.

        This method creates a boolean.py Symbol object that can be used
        in boolean expressions. It validates that the function is registered
        and creates a unique symbol name for the boolean algebra operations.

        Parameters
        ----------
        registry : FunctionRegistry, optional
            Function registry to validate function names.
            If None, uses the default registry.

        Returns
        -------
        Symbol
            A boolean.py Symbol object representing this DICOM symbol

        Raises
        ------
        SymbolParseError
            If the function is not registered in the registry

        Examples
        --------
        >>> symbol = DicomSymbol.parse("PatientName.equals('John')")
        >>> bool_symbol = symbol.to_boolean_symbol()
        >>> str(bool_symbol)  # 'PatientName__equals__12345'
        """
        if registry is None:
            registry = default_registry

        # Validate that the function exists in the registry
        if not registry.is_registered(self.function):
            available = registry.get_registered_names()
            raise SymbolParseError(
                f"{self.attribute}.{self.function}",
                f"Function '{self.function}' is not registered. "
                f"Available functions: {', '.join(available)}",
            )

        # Create a unique symbol name for boolean.py
        # Format: attribute__function__argument_hash
        if self.argument:
            # Create a simple hash of the argument for
            # uniqueness (use abs to avoid negative)
            arg_hash = str(abs(hash(self.argument)))
            symbol_name = f"{self.attribute}__{self.function}__{arg_hash}"
        else:
            symbol_name = f"{self.attribute}__{self.function}"

        return Symbol(symbol_name)

    def evaluate(
        self, dataset: pydicom.Dataset, registry: Optional[FunctionRegistry] = None
    ) -> bool:
        """Evaluate this DICOM symbol against a dataset.

        This method evaluates the DICOM symbol by applying the specified
        function to the specified attribute in the given dataset.

        Parameters
        ----------
        dataset : pydicom.Dataset
            The DICOM dataset to evaluate against
        registry : FunctionRegistry, optional
            Function registry to get the function implementation.
            If None, uses the default registry.

        Returns
        -------
        bool
            Result of evaluating the function against the dataset

        Raises
        ------
        EvaluationError
            If evaluation fails due to dataset access errors or function errors

        Examples
        --------
        >>> from pydicom import Dataset
        >>> dataset = Dataset()
        >>> dataset.PatientName = "John Doe"
        >>>
        >>> symbol = DicomSymbol.parse("PatientName.equals('John Doe')")
        >>> result = symbol.evaluate(dataset)  # Returns True
        """
        if registry is None:
            registry = default_registry

        try:
            # Get the function implementation
            func_instance = registry.get_function(self.function)

            # Evaluate the function
            return func_instance.evaluate(dataset, self.attribute, self.argument)

        except Exception as e:
            raise EvaluationError(
                expression=str(self),
                attribute=self.attribute,
                details=f"Failed to evaluate DICOM symbol: {str(e)}",
            ) from e

    def __str__(self) -> str:
        """Return string representation of the symbol.

        Returns
        -------
        str
            String representation in the format 'attribute.function(argument)'
        """
        if self.argument is not None:
            # Add quotes back for string arguments
            if isinstance(self.argument, str) and not self.argument.isdigit():
                return f"{self.attribute}.{self.function}('{self.argument}')"
            else:
                return f"{self.attribute}.{self.function}({self.argument})"
        else:
            return f"{self.attribute}.{self.function}()"

    def __repr__(self) -> str:
        """Return detailed string representation of the symbol.

        Returns
        -------
        str
            Detailed representation showing all attributes
        """
        return (
            f"DicomSymbol(attribute='{self.attribute}', "
            f"function='{self.function}', argument={repr(self.argument)})"
        )
