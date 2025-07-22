"""Unit tests for the Criterion class."""

import pytest
from pydicom import Dataset

from dicomcriterion import (
    Criterion,
    ExpressionParseError,
    SymbolParseError,
    EvaluationError,
)
from dicomcriterion.functions import FunctionRegistry, EqualsFunction


class TestCriterionConstructor:
    """Test cases for the Criterion class constructor."""

    def test_init_with_simple_expression(self):
        """Test initialization with a simple DICOM expression."""
        expression = "PatientName.equals('John Doe')"
        criterion = Criterion(expression)

        assert criterion._expression == expression
        assert len(criterion._dicom_symbols) == 1
        assert criterion._registry is not None
        assert criterion._parsed_expression is not None

    def test_init_with_complex_boolean_expression(self):
        """Test initialization with complex boolean operators."""
        expression = "PatientName.equals('John') and StudyDescription.contains('MRI')"
        criterion = Criterion(expression)

        assert criterion._expression == expression
        assert len(criterion._dicom_symbols) == 2

        # Check that both symbols were extracted
        symbol_strs = {str(s) for s in criterion._dicom_symbols}
        assert "PatientName.equals('John')" in symbol_strs
        assert "StudyDescription.contains('MRI')" in symbol_strs

    def test_init_with_or_operator(self):
        """Test initialization with OR boolean operator."""
        expression = "PatientID.exists() or PatientName.equals('Unknown')"
        criterion = Criterion(expression)

        assert len(criterion._dicom_symbols) == 2
        symbol_strs = {str(s) for s in criterion._dicom_symbols}
        assert "PatientID.exists()" in symbol_strs
        assert "PatientName.equals('Unknown')" in symbol_strs

    def test_init_with_not_operator(self):
        """Test initialization with NOT boolean operator."""
        expression = "not PatientName.equals('Anonymous')"
        criterion = Criterion(expression)

        assert len(criterion._dicom_symbols) == 1
        symbol_strs = {str(s) for s in criterion._dicom_symbols}
        assert "PatientName.equals('Anonymous')" in symbol_strs

    def test_init_with_parentheses(self):
        """Test initialization with parentheses for grouping."""
        expression = (
            "(PatientName.equals('John') or PatientName.equals('Jane')) "
            "and StudyDate.exists()"
        )
        criterion = Criterion(expression)

        assert len(criterion._dicom_symbols) == 3
        symbol_strs = {str(s) for s in criterion._dicom_symbols}
        assert "PatientName.equals('John')" in symbol_strs
        assert "PatientName.equals('Jane')" in symbol_strs
        assert "StudyDate.exists()" in symbol_strs

    def test_init_with_nested_parentheses(self):
        """Test initialization with nested parentheses."""
        expression = (
            "((PatientName.equals('A') or PatientName.equals('B')) "
            "and StudyID.exists()) or PatientID.contains('123')"
        )
        criterion = Criterion(expression)

        assert len(criterion._dicom_symbols) == 4

    def test_init_with_all_function_types(self):
        """Test initialization with all supported function types."""
        expression = (
            "PatientName.equals('John') and "
            "StudyDescription.contains('MRI') and PatientID.exists()"
        )
        criterion = Criterion(expression)

        assert len(criterion._dicom_symbols) == 3

        # Verify each function type is present
        functions_used = {s.function for s in criterion._dicom_symbols}
        assert "equals" in functions_used
        assert "contains" in functions_used
        assert "exists" in functions_used

    def test_init_with_custom_registry(self):
        """Test initialization with a custom function registry."""
        custom_registry = FunctionRegistry()
        custom_registry.register("equals", EqualsFunction)

        expression = "PatientName.equals('John')"
        criterion = Criterion(expression, registry=custom_registry)

        assert criterion._registry is custom_registry

    def test_init_with_whitespace_in_expression(self):
        """Test initialization handles whitespace correctly."""
        expression = "  PatientName.equals('John')  and  StudyID.exists()  "
        criterion = Criterion(expression)

        assert (
            criterion._expression == "PatientName.equals('John')  and  "
            "StudyID.exists()"
        )
        assert len(criterion._dicom_symbols) == 2

    def test_init_with_double_quotes(self):
        """Test initialization with double-quoted arguments."""
        expression = 'PatientName.equals("John Doe")'
        criterion = Criterion(expression)

        assert len(criterion._dicom_symbols) == 1
        symbol = next(iter(criterion._dicom_symbols))
        assert symbol.argument == "John Doe"

    def test_init_with_unquoted_arguments(self):
        """Test initialization with unquoted arguments."""
        expression = "PatientAge.equals(25)"
        criterion = Criterion(expression)

        assert len(criterion._dicom_symbols) == 1
        symbol = next(iter(criterion._dicom_symbols))
        assert symbol.argument == "25"


class TestCriterionConstructorErrors:
    """Test cases for Criterion constructor error handling."""

    def test_init_with_empty_expression(self):
        """Test initialization with empty expression raises error."""
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("")

        assert "No valid DICOM symbols found" in str(exc_info.value)

    def test_init_with_whitespace_only_expression(self):
        """Test initialization with whitespace-only expression raises error."""
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("   ")

        assert "No valid DICOM symbols found" in str(exc_info.value)

    def test_init_with_invalid_symbol_format(self):
        """Test initialization with invalid symbol format raises error."""
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("PatientName.invalid_format")

        assert "No valid DICOM symbols found" in str(exc_info.value)

    def test_init_with_missing_function_parentheses(self):
        """Test initialization with missing function parentheses raises error."""
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("PatientName.equals")

        assert "No valid DICOM symbols found" in str(exc_info.value)

    def test_init_with_unregistered_function(self):
        """Test initialization with unregistered function raises error."""
        with pytest.raises(SymbolParseError) as exc_info:
            Criterion("PatientName.unknown_function('test')")

        assert "Function 'unknown_function' is not registered" in str(exc_info.value)

    def test_init_with_invalid_boolean_syntax(self):
        """Test initialization with invalid boolean syntax raises error."""
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("PatientName.equals('John') and and StudyID.exists()")

        assert "Failed to parse boolean expression" in str(exc_info.value)

    def test_init_with_mismatched_parentheses(self):
        """Test initialization with mismatched parentheses raises error."""
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("(PatientName.equals('John') and StudyID.exists()")

        assert "Failed to parse boolean expression" in str(exc_info.value)

    def test_init_with_invalid_attribute_name(self):
        """Test initialization with invalid attribute name raises error."""
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("123.equals('test')")

        assert "No valid DICOM symbols found" in str(exc_info.value)

    def test_init_with_invalid_function_name(self):
        """Test initialization with invalid function name raises error."""
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("PatientName.123invalid('test')")

        assert "No valid DICOM symbols found" in str(exc_info.value)


class TestCriterionStringRepresentation:
    """Test cases for Criterion string representation methods."""

    def test_str_representation(self):
        """Test __str__ method returns expected format."""
        expression = "PatientName.equals('John')"
        criterion = Criterion(expression)

        assert str(criterion) == f"Criterion('{expression}')"

    def test_repr_representation(self):
        """Test __repr__ method returns expected format."""
        expression = "PatientName.equals('John')"
        criterion = Criterion(expression)

        assert repr(criterion) == f"Criterion(expression='{expression}')"

    def test_str_with_complex_expression(self):
        """Test string representation with complex expression."""
        expression = "PatientName.equals('John') and StudyID.exists()"
        criterion = Criterion(expression)

        assert str(criterion) == f"Criterion('{expression}')"


class TestCriterionEvaluate:
    """Test cases for the Criterion evaluate method."""

    def test_evaluate_simple_equals_true(self):
        """Test evaluation with simple equals expression that should return True."""
        criterion = Criterion("PatientName.equals('John Doe')")

        # Create a dataset with matching PatientName
        dataset = Dataset()
        dataset.PatientName = "John Doe"

        result = criterion.evaluate(dataset)
        assert result is True

    def test_evaluate_simple_equals_false(self):
        """Test evaluation with simple equals expression that should return False."""
        criterion = Criterion("PatientName.equals('John Doe')")

        # Create a dataset with non-matching PatientName
        dataset = Dataset()
        dataset.PatientName = "Jane Smith"

        result = criterion.evaluate(dataset)
        assert result is False

    def test_evaluate_simple_contains_true(self):
        """Test evaluation with simple contains expression that should return True."""
        criterion = Criterion("StudyDescription.contains('MRI')")

        # Create a dataset with matching StudyDescription
        dataset = Dataset()
        dataset.StudyDescription = "Brain MRI with contrast"

        result = criterion.evaluate(dataset)
        assert result is True

    def test_evaluate_simple_contains_false(self):
        """Test evaluation with simple contains expression that
        should return False.
        """
        criterion = Criterion("StudyDescription.contains('MRI')")

        # Create a dataset with non-matching StudyDescription
        dataset = Dataset()
        dataset.StudyDescription = "CT scan of chest"

        result = criterion.evaluate(dataset)
        assert result is False

    def test_evaluate_simple_exists_true(self):
        """Test evaluation with simple exists expression that should return True."""
        criterion = Criterion("PatientID.exists()")

        # Create a dataset with PatientID present
        dataset = Dataset()
        dataset.PatientID = "12345"

        result = criterion.evaluate(dataset)
        assert result is True

    def test_evaluate_simple_exists_false(self):
        """Test evaluation with simple exists expression that should return False."""
        criterion = Criterion("PatientID.exists()")

        # Create a dataset without PatientID
        dataset = Dataset()
        dataset.PatientName = "John Doe"  # Different attribute

        result = criterion.evaluate(dataset)
        assert result is False

    def test_evaluate_and_expression_both_true(self):
        """Test evaluation with AND expression where both conditions are true."""
        criterion = Criterion("PatientName.equals('John') and StudyID.exists()")

        # Create a dataset that satisfies both conditions
        dataset = Dataset()
        dataset.PatientName = "John"
        dataset.StudyID = "STUDY123"

        result = criterion.evaluate(dataset)
        assert result is True

    def test_evaluate_and_expression_one_false(self):
        """Test evaluation with AND expression where one condition is false."""
        criterion = Criterion("PatientName.equals('John') and StudyID.exists()")

        # Create a dataset that satisfies only the first condition
        dataset = Dataset()
        dataset.PatientName = "John"
        # StudyID is missing

        result = criterion.evaluate(dataset)
        assert result is False

    def test_evaluate_or_expression_one_true(self):
        """Test evaluation with OR expression where one condition is true."""
        criterion = Criterion(
            "PatientName.equals('John') or PatientName.equals('Jane')"
        )

        # Create a dataset that satisfies the first condition
        dataset = Dataset()
        dataset.PatientName = "John"

        result = criterion.evaluate(dataset)
        assert result is True

    def test_evaluate_or_expression_both_false(self):
        """Test evaluation with OR expression where both conditions are false."""
        criterion = Criterion(
            "PatientName.equals('John') or PatientName.equals('Jane')"
        )

        # Create a dataset that satisfies neither condition
        dataset = Dataset()
        dataset.PatientName = "Bob"

        result = criterion.evaluate(dataset)
        assert result is False

    def test_evaluate_not_expression_true(self):
        """Test evaluation with NOT expression that should return True."""
        criterion = Criterion("not PatientName.equals('Anonymous')")

        # Create a dataset with different PatientName
        dataset = Dataset()
        dataset.PatientName = "John Doe"

        result = criterion.evaluate(dataset)
        assert result is True

    def test_evaluate_not_expression_false(self):
        """Test evaluation with NOT expression that should return False."""
        criterion = Criterion("not PatientName.equals('Anonymous')")

        # Create a dataset with matching PatientName
        dataset = Dataset()
        dataset.PatientName = "Anonymous"

        result = criterion.evaluate(dataset)
        assert result is False

    def test_evaluate_complex_expression(self):
        """Test evaluation with complex nested expression."""
        criterion = Criterion(
            "(PatientName.equals('John') or PatientName.equals('Jane')) "
            "and StudyDescription.contains('MRI')"
        )

        # Create a dataset that satisfies the complex condition
        dataset = Dataset()
        dataset.PatientName = "Jane"
        dataset.StudyDescription = "Brain MRI scan"

        result = criterion.evaluate(dataset)
        assert result is True

    def test_evaluate_complex_expression_false(self):
        """Test evaluation with complex nested expression that should return False."""
        criterion = Criterion(
            "(PatientName.equals('John') or PatientName.equals('Jane')) "
            "and StudyDescription.contains('MRI')"
        )

        # Create a dataset that doesn't satisfy the AND condition
        dataset = Dataset()
        dataset.PatientName = "Jane"  # Satisfies first part
        dataset.StudyDescription = "CT scan"  # Doesn't satisfy second part

        result = criterion.evaluate(dataset)
        assert result is False

    def test_evaluate_with_missing_attributes(self):
        """Test evaluation with dataset missing some attributes."""
        criterion = Criterion(
            "PatientName.equals('John') and MissingAttribute.exists()"
        )

        # Create a dataset with only one of the required attributes
        dataset = Dataset()
        dataset.PatientName = "John"
        # MissingAttribute is not present

        result = criterion.evaluate(dataset)
        assert result is False

    def test_evaluate_all_function_types(self):
        """Test evaluation with all supported function types."""
        criterion = Criterion(
            "PatientName.equals('John') and StudyDescription.contains('MRI')"
            " and PatientID.exists()"
        )

        # Create a dataset that satisfies all conditions
        dataset = Dataset()
        dataset.PatientName = "John"
        dataset.StudyDescription = "Brain MRI with contrast"
        dataset.PatientID = "12345"

        result = criterion.evaluate(dataset)
        assert result is True

    def test_evaluate_case_insensitive_equals(self):
        """Test that equals function is case-insensitive."""
        criterion = Criterion("PatientName.equals('john doe')")

        # Create a dataset with different case
        dataset = Dataset()
        dataset.PatientName = "John Doe"

        result = criterion.evaluate(dataset)
        assert result is True

    def test_evaluate_case_insensitive_contains(self):
        """Test that contains function is case-insensitive."""
        criterion = Criterion("StudyDescription.contains('mri')")

        # Create a dataset with different case
        dataset = Dataset()
        dataset.StudyDescription = "Brain MRI scan"

        result = criterion.evaluate(dataset)
        assert result is True


class TestCriterionEvaluateErrors:
    """Test cases for Criterion evaluate method error handling."""

    def test_evaluate_with_invalid_dataset(self):
        """Test evaluation with invalid dataset raises error."""
        criterion = Criterion("PatientName.equals('John')")

        # This should raise an EvaluationError
        with pytest.raises((EvaluationError, AttributeError)):
            criterion.evaluate(None)

    def test_evaluate_with_function_error(self):
        """Test evaluation when function evaluation fails."""
        from dicomcriterion.functions import FunctionRegistry, DicomFunction
        from dicomcriterion.exceptions import EvaluationError

        # Create a custom function that always raises an error
        class ErrorFunction(DicomFunction):
            def evaluate(self, dataset, attribute, argument=None):
                raise ValueError("Test error")

        # Create a custom registry with the error function
        custom_registry = FunctionRegistry()
        custom_registry.register("error_func", ErrorFunction)

        # This would require modifying the expression parsing to accept
        # custom functions For now, we'll test with a standard function
        # but invalid dataset structure
        criterion = Criterion("PatientName.equals('John')")

        # Create an invalid dataset that will cause function evaluation to fail
        class InvalidDataset:
            def __getattr__(self, name):
                raise ValueError("Invalid dataset access")

        with pytest.raises(EvaluationError):
            criterion.evaluate(InvalidDataset())


class TestCriterionInternalMethods:
    """Test cases for Criterion internal helper methods."""

    def test_extract_dicom_symbols_single_symbol(self):
        """Test _extract_dicom_symbols with single symbol."""
        criterion = Criterion("PatientName.equals('John')")
        symbols = criterion._extract_dicom_symbols("PatientName.equals('John')")

        assert len(symbols) == 1
        symbol = next(iter(symbols))
        assert symbol.attribute == "PatientName"
        assert symbol.function == "equals"
        assert symbol.argument == "John"

    def test_extract_dicom_symbols_multiple_symbols(self):
        """Test _extract_dicom_symbols with multiple symbols."""
        expression = "PatientName.equals('John') and StudyID.exists()"
        criterion = Criterion(expression)
        symbols = criterion._extract_dicom_symbols(expression)

        assert len(symbols) == 2

        # Convert to list for easier testing
        symbol_list = list(symbols)
        attributes = {s.attribute for s in symbol_list}
        functions = {s.function for s in symbol_list}

        assert "PatientName" in attributes
        assert "StudyID" in attributes
        assert "equals" in functions
        assert "exists" in functions

    def test_convert_to_boolean_expression(self):
        """Test _convert_to_boolean_expression method."""
        expression = "PatientName.equals('John') and StudyID.exists()"
        criterion = Criterion(expression)

        # Create a proper boolean symbols mapping like the constructor does
        boolean_symbols = {}
        for dicom_symbol in criterion._dicom_symbols:
            boolean_symbol = dicom_symbol.to_boolean_symbol(criterion._registry)
            symbol_key = str(boolean_symbol)
            boolean_symbols[symbol_key] = boolean_symbol

        # The boolean expression should have DICOM symbols replaced
        # with boolean symbol names
        boolean_expr = criterion._convert_to_boolean_expression(
            expression, criterion._dicom_symbols, boolean_symbols
        )

        # The result should be different from the original (symbols replaced)
        # Exact format depends on boolean.py symbol naming, so we just
        # check it's different
        assert boolean_expr != expression

        # Check that the boolean expression contains symbol names, not DICOM symbols
        assert "PatientName__equals" in boolean_expr
        assert "StudyID__exists" in boolean_expr
        assert "PatientName.equals('John')" not in boolean_expr
        assert "StudyID.exists()" not in boolean_expr
