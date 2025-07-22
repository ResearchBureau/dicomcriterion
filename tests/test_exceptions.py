"""Unit tests for DICOM Criterion exception classes."""

import pytest

from dicomcriterion.exceptions import (
    CriterionError,
    ExpressionParseError,
    SymbolParseError,
    FunctionNotFoundError,
    EvaluationError,
)


class TestCriterionError:
    """Test cases for the base CriterionError class."""

    def test_init_with_message_only(self):
        """Test initialization with just a message."""
        error = CriterionError("Something went wrong")

        assert error.message == "Something went wrong"
        assert error.details is None
        assert str(error) == "Something went wrong"

    def test_init_with_message_and_details(self):
        """Test initialization with message and details."""
        error = CriterionError("Something went wrong", "More context here")

        assert error.message == "Something went wrong"
        assert error.details == "More context here"
        assert str(error) == "Something went wrong: More context here"

    def test_inheritance_from_exception(self):
        """Test that CriterionError inherits from Exception."""
        error = CriterionError("Test error")
        assert isinstance(error, Exception)


class TestExpressionParseError:
    """Test cases for ExpressionParseError."""

    def test_init_with_expression_only(self):
        """Test initialization with just an expression."""
        expression = "invalid && syntax"
        error = ExpressionParseError(expression)

        assert error.expression == expression
        assert error.message == f"Failed to parse expression: '{expression}'"
        assert error.details is None
        assert str(error) == f"Failed to parse expression: '{expression}'"

    def test_init_with_expression_and_details(self):
        """Test initialization with expression and details."""
        expression = "invalid && syntax"
        details = "Unexpected token '&&'"
        error = ExpressionParseError(expression, details)

        assert error.expression == expression
        assert error.details == details
        expected_str = f"Failed to parse expression: '{expression}': {details}"
        assert str(error) == expected_str

    def test_inheritance_from_criterion_error(self):
        """Test that ExpressionParseError inherits from CriterionError."""
        error = ExpressionParseError("test")
        assert isinstance(error, CriterionError)
        assert isinstance(error, Exception)


class TestSymbolParseError:
    """Test cases for SymbolParseError."""

    def test_init_with_symbol_only(self):
        """Test initialization with just a symbol."""
        symbol = "invalid.symbol.format"
        error = SymbolParseError(symbol)

        assert error.symbol == symbol
        assert error.message == f"Invalid DICOM symbol format: '{symbol}'"
        assert "Expected format: 'attribute.function(args)'" in error.details
        assert "equals, contains, exists" in error.details

    def test_init_with_symbol_and_custom_details(self):
        """Test initialization with symbol and custom details."""
        symbol = "PatientName.invalid()"
        details = "Function 'invalid' is not supported"
        error = SymbolParseError(symbol, details)

        assert error.symbol == symbol
        assert error.details == details
        expected_str = f"Invalid DICOM symbol format: '{symbol}': {details}"
        assert str(error) == expected_str

    def test_inheritance_from_criterion_error(self):
        """Test that SymbolParseError inherits from CriterionError."""
        error = SymbolParseError("test")
        assert isinstance(error, CriterionError)
        assert isinstance(error, Exception)


class TestFunctionNotFoundError:
    """Test cases for FunctionNotFoundError."""

    def test_init_with_function_name_only(self):
        """Test initialization with just a function name."""
        function_name = "unknown_function"
        error = FunctionNotFoundError(function_name)

        assert error.function_name == function_name
        assert error.available_functions == []
        assert error.message == f"Function '{function_name}' is not registered"
        assert error.details == "No functions are currently registered"

    def test_init_with_function_name_and_available_functions(self):
        """Test initialization with function name and available functions."""
        function_name = "unknown_function"
        available_functions = ["equals", "contains", "exists"]
        error = FunctionNotFoundError(function_name, available_functions)

        assert error.function_name == function_name
        assert error.available_functions == available_functions
        assert error.message == f"Function '{function_name}' is not registered"
        assert error.details == "Available functions: equals, contains, exists"

    def test_init_with_empty_available_functions_list(self):
        """Test initialization with empty available functions list."""
        function_name = "unknown_function"
        available_functions = []
        error = FunctionNotFoundError(function_name, available_functions)

        assert error.available_functions == []
        assert error.details == "No functions are currently registered"

    def test_inheritance_from_criterion_error(self):
        """Test that FunctionNotFoundError inherits from CriterionError."""
        error = FunctionNotFoundError("test")
        assert isinstance(error, CriterionError)
        assert isinstance(error, Exception)


class TestEvaluationError:
    """Test cases for EvaluationError."""

    def test_init_with_no_parameters(self):
        """Test initialization with no parameters."""
        error = EvaluationError()

        assert error.expression is None
        assert error.attribute is None
        assert error.message == "Expression evaluation failed"
        assert error.details is None

    def test_init_with_expression_only(self):
        """Test initialization with just an expression."""
        expression = "PatientName.equals('John')"
        error = EvaluationError(expression=expression)

        assert error.expression == expression
        assert error.attribute is None
        assert error.message == f"Failed to evaluate expression '{expression}'"

    def test_init_with_attribute_only(self):
        """Test initialization with just an attribute."""
        attribute = "PatientName"
        error = EvaluationError(attribute=attribute)

        assert error.expression is None
        assert error.attribute == attribute
        assert error.message == f"Failed to access DICOM attribute '{attribute}'"

    def test_init_with_expression_and_attribute(self):
        """Test initialization with both expression and attribute."""
        expression = "PatientName.equals('John')"
        attribute = "PatientName"
        error = EvaluationError(expression=expression, attribute=attribute)

        assert error.expression == expression
        assert error.attribute == attribute
        expected_message = (
            f"Failed to evaluate expression '{expression}' "
            f"for attribute '{attribute}'"
        )
        assert error.message == expected_message

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters including details."""
        expression = "PatientName.equals('John')"
        attribute = "PatientName"
        details = "Attribute not found in dataset"
        error = EvaluationError(
            expression=expression, attribute=attribute, details=details
        )

        assert error.expression == expression
        assert error.attribute == attribute
        assert error.details == details
        expected_str = (
            f"Failed to evaluate expression '{expression}' "
            f"for attribute '{attribute}': {details}"
        )
        assert str(error) == expected_str

    def test_inheritance_from_criterion_error(self):
        """Test that EvaluationError inherits from CriterionError."""
        error = EvaluationError()
        assert isinstance(error, CriterionError)
        assert isinstance(error, Exception)


class TestExceptionHierarchy:
    """Test cases for the overall exception hierarchy."""

    def test_all_exceptions_inherit_from_criterion_error(self):
        """Test that all custom exceptions inherit from CriterionError."""
        exceptions = [
            ExpressionParseError("test"),
            SymbolParseError("test"),
            FunctionNotFoundError("test"),
            EvaluationError(),
        ]

        for exception in exceptions:
            assert isinstance(exception, CriterionError)
            assert isinstance(exception, Exception)

    def test_exception_catching_with_base_class(self):
        """Test that all exceptions can be caught with CriterionError."""
        exceptions = [
            ExpressionParseError("test"),
            SymbolParseError("test"),
            FunctionNotFoundError("test"),
            EvaluationError(),
        ]

        for exception in exceptions:
            try:
                raise exception
            except CriterionError:
                # Should catch all custom exceptions
                pass
            except Exception:
                pytest.fail(
                    f"Exception {type(exception)} not " f"caught by CriterionError"
                )


class TestErrorMessageClarity:
    """Test cases for error message clarity and usefulness."""

    def test_expression_parse_error_messages_are_clear(self):
        """Test that ExpressionParseError messages are clear and helpful."""
        error = ExpressionParseError(
            "invalid && syntax",
            "Boolean operator '&&' is not supported, use 'and' instead",
        )

        message = str(error)
        assert "Failed to parse expression" in message
        assert "invalid && syntax" in message
        assert "use 'and' instead" in message

    def test_symbol_parse_error_provides_format_guidance(self):
        """Test that SymbolParseError provides format guidance."""
        error = SymbolParseError("invalid_symbol")

        message = str(error)
        assert "Invalid DICOM symbol format" in message
        assert "Expected format" in message
        assert "attribute.function(args)" in message
        assert "equals, contains, exists" in message

    def test_function_not_found_error_lists_available_functions(self):
        """Test that FunctionNotFoundError lists available alternatives."""
        error = FunctionNotFoundError("invalid", ["equals", "contains", "exists"])

        message = str(error)
        assert "Function 'invalid' is not registered" in message
        assert "Available functions: equals, contains, exists" in message

    def test_evaluation_error_provides_context(self):
        """Test that EvaluationError provides helpful context."""
        error = EvaluationError(
            expression="PatientName.equals('John')",
            attribute="PatientName",
            details="Attribute value is not a string",
        )

        message = str(error)
        assert "Failed to evaluate expression" in message
        assert "PatientName.equals('John')" in message
        assert "PatientName" in message
        assert "not a string" in message
