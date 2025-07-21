"""Exception classes for DICOM Criterion library."""

from typing import Optional


class CriterionError(Exception):
    """Base exception for Criterion-related errors.

    This is the base class for all exceptions raised by the DICOM Criterion
    library. It provides a consistent interface for error handling and
    meaningful error messages.
    """

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        """Initialize the exception with a message and optional details.

        Parameters
        ----------
        message : str
            The main error message describing what went wrong.
        details : str, optional
            Additional details about the error context.
        """
        self.message = message
        self.details = details

        if details:
            super().__init__(f"{message}: {details}")
        else:
            super().__init__(message)


class ExpressionParseError(CriterionError):
    """Raised when expression cannot be parsed.

    This exception is raised when the boolean expression string provided
    to the Criterion class cannot be parsed due to invalid syntax.
    """

    def __init__(self, expression: str, details: Optional[str] = None) -> None:
        """Initialize with the invalid expression and error details.

        Parameters
        ----------
        expression : str
            The expression string that failed to parse.
        details : str, optional
            Specific details about why parsing failed.
        """
        self.expression = expression
        message = f"Failed to parse expression: '{expression}'"
        super().__init__(message, details)


class SymbolParseError(CriterionError):
    """Raised when DICOM symbol format is invalid.

    This exception is raised when a DICOM attribute symbol in the expression
    does not follow the expected format (e.g., 'attribute.function(args)').
    """

    def __init__(self, symbol: str, details: Optional[str] = None) -> None:
        """Initialize with the invalid symbol and error details.

        Parameters
        ----------
        symbol : str
            The symbol string that failed to parse.
        details : str, optional
            Specific details about the expected format.
        """
        self.symbol = symbol
        message = f"Invalid DICOM symbol format: '{symbol}'"
        if not details:
            details = (
                "Expected format: 'attribute.function(args)' where function "
                "is one of: equals, contains, exists"
            )
        super().__init__(message, details)


class FunctionNotFoundError(CriterionError):
    """Raised when referenced function is not registered.

    This exception is raised when an expression references a DICOM function
    that is not available in the function registry.
    """

    def __init__(
        self, function_name: str, available_functions: Optional[list[str]] = None
    ) -> None:
        """Initialize with the missing function name and available options.

        Parameters
        ----------
        function_name : str
            The name of the function that was not found.
        available_functions : list, optional
            List of available function names.
        """
        self.function_name = function_name
        self.available_functions = available_functions or []

        message = f"Function '{function_name}' is not registered"

        if self.available_functions:
            details = f"Available functions: {', '.join(self.available_functions)}"
        else:
            details = "No functions are currently registered"

        super().__init__(message, details)


class EvaluationError(CriterionError):
    """Raised when expression evaluation fails.

    This exception is raised when an error occurs during the evaluation
    of a boolean expression against a DICOM dataset.
    """

    def __init__(
        self,
        expression: Optional[str] = None,
        attribute: Optional[str] = None,
        details: Optional[str] = None,
    ) -> None:
        """Initialize with evaluation context and error details.

        Parameters
        ----------
        expression : str, optional
            The expression being evaluated when the error occurred.
        attribute : str, optional
            The DICOM attribute being accessed when the error occurred.
        details : str, optional
            Specific details about what went wrong during evaluation.
        """
        self.expression = expression
        self.attribute = attribute

        if expression and attribute:
            message = (
                f"Failed to evaluate expression '{expression}' "
                f"for attribute '{attribute}'"
            )
        elif expression:
            message = f"Failed to evaluate expression '{expression}'"
        elif attribute:
            message = f"Failed to access DICOM attribute '{attribute}'"
        else:
            message = "Expression evaluation failed"

        super().__init__(message, details)
