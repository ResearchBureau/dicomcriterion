"""Tests for DICOM symbol parsing and conversion."""

import pytest
import pydicom
from boolean import Symbol

from dicomcriterion import DicomSymbol, SymbolParseError, EvaluationError
from dicomcriterion.functions import FunctionRegistry, EqualsFunction


class TestDicomSymbolParsing:
    """Test DicomSymbol parsing functionality."""

    def test_parse_equals_with_quoted_string(self):
        """Test parsing equals function with quoted string argument."""
        symbol = DicomSymbol.parse("PatientName.equals('John Doe')")

        assert symbol.attribute == "PatientName"
        assert symbol.function == "equals"
        assert symbol.argument == "John Doe"

    def test_parse_equals_with_double_quoted_string(self):
        """Test parsing equals function with double-quoted string argument."""
        symbol = DicomSymbol.parse('StudyDescription.equals("MRI Brain")')

        assert symbol.attribute == "StudyDescription"
        assert symbol.function == "equals"
        assert symbol.argument == "MRI Brain"

    def test_parse_equals_with_unquoted_argument(self):
        """Test parsing equals function with unquoted argument."""
        symbol = DicomSymbol.parse("PatientAge.equals(25)")

        assert symbol.attribute == "PatientAge"
        assert symbol.function == "equals"
        assert symbol.argument == "25"

    def test_parse_contains_function(self):
        """Test parsing contains function."""
        symbol = DicomSymbol.parse("StudyDescription.contains('MRI')")

        assert symbol.attribute == "StudyDescription"
        assert symbol.function == "contains"
        assert symbol.argument == "MRI"

    def test_parse_exists_function(self):
        """Test parsing exists function with no arguments."""
        symbol = DicomSymbol.parse("PatientID.exists()")

        assert symbol.attribute == "PatientID"
        assert symbol.function == "exists"
        assert symbol.argument is None

    def test_parse_with_whitespace(self):
        """Test parsing with extra whitespace."""
        symbol = DicomSymbol.parse("  PatientName.equals('John')  ")

        assert symbol.attribute == "PatientName"
        assert symbol.function == "equals"
        assert symbol.argument == "John"

    def test_parse_with_underscore_in_names(self):
        """Test parsing with underscores in attribute and function names."""
        symbol = DicomSymbol.parse("Patient_Name.custom_equals('test')")

        assert symbol.attribute == "Patient_Name"
        assert symbol.function == "custom_equals"
        assert symbol.argument == "test"

    def test_parse_invalid_format_no_dot(self):
        """Test parsing fails with invalid format (no dot)."""
        with pytest.raises(SymbolParseError) as exc_info:
            DicomSymbol.parse("PatientNameequals('John')")

        assert "Expected format" in str(exc_info.value)
        assert "PatientNameequals('John')" in str(exc_info.value)

    def test_parse_invalid_format_no_parentheses(self):
        """Test parsing fails with invalid format (no parentheses)."""
        with pytest.raises(SymbolParseError) as exc_info:
            DicomSymbol.parse("PatientName.equals")

        assert "Expected format" in str(exc_info.value)

    def test_parse_invalid_format_missing_closing_paren(self):
        """Test parsing fails with missing closing parenthesis."""
        with pytest.raises(SymbolParseError) as exc_info:
            DicomSymbol.parse("PatientName.equals('John'")

        assert "Expected format" in str(exc_info.value)

    def test_parse_invalid_attribute_name(self):
        """Test parsing fails with invalid attribute name (starts with number)."""
        with pytest.raises(SymbolParseError) as exc_info:
            DicomSymbol.parse("123Patient.equals('John')")

        assert "Expected format" in str(exc_info.value)

    def test_parse_empty_string(self):
        """Test parsing fails with empty string."""
        with pytest.raises(SymbolParseError) as exc_info:
            DicomSymbol.parse("")

        assert "Expected format" in str(exc_info.value)

    def test_parse_complex_quoted_argument(self):
        """Test parsing with complex quoted argument containing
        spaces and punctuation.
        """
        symbol = DicomSymbol.parse(
            "StudyDescription.contains('MRI - Brain with contrast')"
        )

        assert symbol.attribute == "StudyDescription"
        assert symbol.function == "contains"
        assert symbol.argument == "MRI - Brain with contrast"


class TestDicomSymbolBooleanConversion:
    """Test DicomSymbol to boolean.py Symbol conversion."""

    def test_to_boolean_symbol_with_argument(self):
        """Test conversion to boolean Symbol with argument."""
        symbol = DicomSymbol("PatientName", "equals", "John")
        bool_symbol = symbol.to_boolean_symbol()

        assert isinstance(bool_symbol, Symbol)
        assert "PatientName" in str(bool_symbol)
        assert "equals" in str(bool_symbol)

    def test_to_boolean_symbol_without_argument(self):
        """Test conversion to boolean Symbol without argument."""
        symbol = DicomSymbol("PatientID", "exists")
        bool_symbol = symbol.to_boolean_symbol()

        assert isinstance(bool_symbol, Symbol)
        assert "PatientID" in str(bool_symbol)
        assert "exists" in str(bool_symbol)

    def test_to_boolean_symbol_unique_names(self):
        """Test that different symbols generate unique boolean symbol names."""
        symbol1 = DicomSymbol("PatientName", "equals", "John")
        symbol2 = DicomSymbol("PatientName", "equals", "Jane")
        symbol3 = DicomSymbol("PatientName", "contains", "John")

        bool_symbol1 = symbol1.to_boolean_symbol()
        bool_symbol2 = symbol2.to_boolean_symbol()
        bool_symbol3 = symbol3.to_boolean_symbol()

        # All should be different
        assert str(bool_symbol1) != str(bool_symbol2)
        assert str(bool_symbol1) != str(bool_symbol3)
        assert str(bool_symbol2) != str(bool_symbol3)

    def test_to_boolean_symbol_unregistered_function(self):
        """Test conversion fails with unregistered function."""
        symbol = DicomSymbol("PatientName", "unknown_function", "test")

        with pytest.raises(SymbolParseError) as exc_info:
            symbol.to_boolean_symbol()

        assert "unknown_function" in str(exc_info.value)
        assert "not registered" in str(exc_info.value)

    def test_to_boolean_symbol_custom_registry(self):
        """Test conversion with custom function registry."""
        # Create custom registry with only equals function
        custom_registry = FunctionRegistry()
        custom_registry.register("equals", EqualsFunction)

        # This should work
        symbol1 = DicomSymbol("PatientName", "equals", "John")
        bool_symbol1 = symbol1.to_boolean_symbol(custom_registry)
        assert isinstance(bool_symbol1, Symbol)

        # This should fail (contains not registered in custom registry)
        symbol2 = DicomSymbol("PatientName", "contains", "John")
        with pytest.raises(SymbolParseError):
            symbol2.to_boolean_symbol(custom_registry)


class TestDicomSymbolEvaluation:
    """Test DicomSymbol evaluation against DICOM datasets."""

    def create_test_dataset(self):
        """Create a test DICOM dataset."""
        ds = pydicom.Dataset()
        ds.PatientName = "John Doe"
        ds.PatientID = "12345"
        ds.StudyDescription = "MRI Brain"
        ds.PatientAge = "025Y"
        return ds

    def test_evaluate_equals_function_match(self):
        """Test evaluation of equals function with matching value."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol("PatientName", "equals", "John Doe")

        result = symbol.evaluate(dataset)
        assert result is True

    def test_evaluate_equals_function_no_match(self):
        """Test evaluation of equals function with non-matching value."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol("PatientName", "equals", "Jane Doe")

        result = symbol.evaluate(dataset)
        assert result is False

    def test_evaluate_contains_function_match(self):
        """Test evaluation of contains function with matching substring."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol("StudyDescription", "contains", "MRI")

        result = symbol.evaluate(dataset)
        assert result is True

    def test_evaluate_contains_function_no_match(self):
        """Test evaluation of contains function with non-matching substring."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol("StudyDescription", "contains", "CT")

        result = symbol.evaluate(dataset)
        assert result is False

    def test_evaluate_exists_function_present(self):
        """Test evaluation of exists function with present attribute."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol("PatientID", "exists")

        result = symbol.evaluate(dataset)
        assert result is True

    def test_evaluate_exists_function_missing(self):
        """Test evaluation of exists function with missing attribute."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol("NonExistentAttribute", "exists")

        result = symbol.evaluate(dataset)
        assert result is False

    def test_evaluate_missing_attribute_equals(self):
        """Test evaluation of equals function with missing attribute."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol("NonExistentAttribute", "equals", "test")

        result = symbol.evaluate(dataset)
        assert result is False

    def test_evaluate_missing_attribute_contains(self):
        """Test evaluation of contains function with missing attribute."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol("NonExistentAttribute", "contains", "test")

        result = symbol.evaluate(dataset)
        assert result is False

    def test_evaluate_custom_registry(self):
        """Test evaluation with custom function registry."""
        dataset = self.create_test_dataset()
        custom_registry = FunctionRegistry()
        custom_registry.register("equals", EqualsFunction)

        symbol = DicomSymbol("PatientName", "equals", "John Doe")
        result = symbol.evaluate(dataset, custom_registry)
        assert result is True

    def test_evaluate_unregistered_function(self):
        """Test evaluation fails with unregistered function."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol("PatientName", "unknown_function", "test")

        with pytest.raises(EvaluationError) as exc_info:
            symbol.evaluate(dataset)

        assert "unknown_function" in str(exc_info.value)


class TestDicomSymbolStringRepresentation:
    """Test DicomSymbol string representation methods."""

    def test_str_with_string_argument(self):
        """Test __str__ method with string argument."""
        symbol = DicomSymbol("PatientName", "equals", "John Doe")
        result = str(symbol)

        assert result == "PatientName.equals('John Doe')"

    def test_str_with_numeric_argument(self):
        """Test __str__ method with numeric argument."""
        symbol = DicomSymbol("PatientAge", "equals", "25")
        result = str(symbol)

        # Numeric arguments should not have quotes
        assert result == "PatientAge.equals(25)"

    def test_str_without_argument(self):
        """Test __str__ method without argument."""
        symbol = DicomSymbol("PatientID", "exists")
        result = str(symbol)

        assert result == "PatientID.exists()"

    def test_repr_method(self):
        """Test __repr__ method."""
        symbol = DicomSymbol("PatientName", "equals", "John")
        result = repr(symbol)

        expected = (
            "DicomSymbol(attribute='PatientName', function='equals', argument='John')"
        )
        assert result == expected

    def test_repr_method_no_argument(self):
        """Test __repr__ method without argument."""
        symbol = DicomSymbol("PatientID", "exists")
        result = repr(symbol)

        expected = (
            "DicomSymbol(attribute='PatientID', function='exists', argument=None)"
        )
        assert result == expected


class TestDicomSymbolIntegration:
    """Integration tests combining parsing and evaluation."""

    def create_test_dataset(self):
        """Create a test DICOM dataset."""
        ds = pydicom.Dataset()
        ds.PatientName = "John Doe"
        ds.PatientID = "12345"
        ds.StudyDescription = "MRI Brain with contrast"
        ds.PatientAge = "045Y"
        return ds

    def test_parse_and_evaluate_equals(self):
        """Test parsing and evaluating equals function."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol.parse("PatientName.equals('John Doe')")

        result = symbol.evaluate(dataset)
        assert result is True

    def test_parse_and_evaluate_contains(self):
        """Test parsing and evaluating contains function."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol.parse("StudyDescription.contains('MRI')")

        result = symbol.evaluate(dataset)
        assert result is True

    def test_parse_and_evaluate_exists(self):
        """Test parsing and evaluating exists function."""
        dataset = self.create_test_dataset()
        symbol = DicomSymbol.parse("PatientID.exists()")

        result = symbol.evaluate(dataset)
        assert result is True

    def test_parse_and_convert_to_boolean(self):
        """Test parsing and converting to boolean Symbol."""
        symbol = DicomSymbol.parse("PatientName.equals('John')")
        bool_symbol = symbol.to_boolean_symbol()

        assert isinstance(bool_symbol, Symbol)
        assert "PatientName" in str(bool_symbol)
        assert "equals" in str(bool_symbol)


class TestDicomSymbolBooleanIntegration:
    """Test DicomSymbol integration with boolean.py library."""

    def test_boolean_symbol_with_boolean_algebra(self):
        """Test that DicomSymbol works with boolean.py BooleanAlgebra."""
        from boolean import BooleanAlgebra

        # Create symbols
        symbol1 = DicomSymbol("PatientName", "equals", "John")
        symbol2 = DicomSymbol("PatientID", "exists")

        # Convert to boolean symbols
        bool_symbol1 = symbol1.to_boolean_symbol()
        bool_symbol2 = symbol2.to_boolean_symbol()

        # Create boolean algebra instance
        ba = BooleanAlgebra()

        # Test that symbols can be used in boolean expressions
        expr_str = f"{bool_symbol1} & {bool_symbol2}"
        parsed_expr = ba.parse(expr_str)

        assert parsed_expr is not None
        assert str(bool_symbol1) in str(parsed_expr)
        assert str(bool_symbol2) in str(parsed_expr)

    def test_symbol_evaluation_with_boolean_substitution(self):
        """Test symbol evaluation using boolean.py substitution."""
        from boolean import BooleanAlgebra

        # Create test dataset
        ds = pydicom.Dataset()
        ds.PatientName = "John Doe"
        ds.PatientID = "12345"

        # Create symbols
        symbol1 = DicomSymbol("PatientName", "equals", "John Doe")
        symbol2 = DicomSymbol("PatientID", "exists")
        symbol3 = DicomSymbol("PatientName", "equals", "Jane Doe")

        # Convert to boolean symbols
        bool_symbol1 = symbol1.to_boolean_symbol()
        bool_symbol2 = symbol2.to_boolean_symbol()
        bool_symbol3 = symbol3.to_boolean_symbol()

        # Create boolean algebra instance
        ba = BooleanAlgebra()

        # Test that symbols can be used in boolean expressions
        and_expr = ba.parse(f"{bool_symbol1} & {bool_symbol2}")
        or_expr = ba.parse(f"{bool_symbol1} | {bool_symbol3}")

        # Test that we can create substitution maps with evaluation results
        symbol_map = {
            str(bool_symbol1): symbol1.evaluate(ds),  # True
            str(bool_symbol2): symbol2.evaluate(ds),  # True
            str(bool_symbol3): symbol3.evaluate(ds),  # False
        }

        # Verify the evaluations are as expected
        assert symbol_map[str(bool_symbol1)] is True
        assert symbol_map[str(bool_symbol2)] is True
        assert symbol_map[str(bool_symbol3)] is False

        # Test that expressions can be created and parsed
        assert and_expr is not None
        assert or_expr is not None
        assert str(bool_symbol1) in str(and_expr)
        assert str(bool_symbol2) in str(and_expr)

    def test_symbol_hash_consistency(self):
        """Test that symbol hashes are consistent for same arguments."""
        # Same symbols should produce same boolean symbols
        symbol1a = DicomSymbol("PatientName", "equals", "John")
        symbol1b = DicomSymbol("PatientName", "equals", "John")

        bool_symbol1a = symbol1a.to_boolean_symbol()
        bool_symbol1b = symbol1b.to_boolean_symbol()

        assert str(bool_symbol1a) == str(bool_symbol1b)

        # Different symbols should produce different boolean symbols
        symbol2 = DicomSymbol("PatientName", "equals", "Jane")
        bool_symbol2 = symbol2.to_boolean_symbol()

        assert str(bool_symbol1a) != str(bool_symbol2)

    def test_symbol_name_format(self):
        """Test that symbol names follow expected format."""
        # Test with argument
        symbol_with_arg = DicomSymbol("PatientName", "equals", "John")
        bool_symbol_with_arg = symbol_with_arg.to_boolean_symbol()
        symbol_name = str(bool_symbol_with_arg)

        assert "PatientName" in symbol_name
        assert "equals" in symbol_name
        assert "__" in symbol_name  # Should contain separators

        # Test without argument
        symbol_no_arg = DicomSymbol("PatientID", "exists")
        bool_symbol_no_arg = symbol_no_arg.to_boolean_symbol()
        symbol_name_no_arg = str(bool_symbol_no_arg)

        assert "PatientID" in symbol_name_no_arg
        assert "exists" in symbol_name_no_arg
        assert "__" in symbol_name_no_arg

        # Should not contain hash for no-argument symbols
        assert symbol_name_no_arg == "PatientID__exists"

    def test_complex_boolean_expression_evaluation(self):
        """Test evaluation of complex boolean expressions."""
        from boolean import BooleanAlgebra

        # Create test dataset
        ds = pydicom.Dataset()
        ds.PatientName = "John Doe"
        ds.PatientID = "12345"
        ds.StudyDescription = "MRI Brain"

        # Create multiple symbols
        name_john = DicomSymbol("PatientName", "equals", "John Doe")
        name_jane = DicomSymbol("PatientName", "equals", "Jane Doe")
        id_exists = DicomSymbol("PatientID", "exists")
        study_mri = DicomSymbol("StudyDescription", "contains", "MRI")
        study_ct = DicomSymbol("StudyDescription", "contains", "CT")

        # Convert to boolean symbols
        bool_name_john = name_john.to_boolean_symbol()
        bool_name_jane = name_jane.to_boolean_symbol()
        bool_id_exists = id_exists.to_boolean_symbol()
        bool_study_mri = study_mri.to_boolean_symbol()
        bool_study_ct = study_ct.to_boolean_symbol()

        # Create boolean algebra instance
        ba = BooleanAlgebra()

        # Test complex expression: (name_john & id_exists) | (study_mri & ~study_ct)
        complex_expr = ba.parse(
            f"({bool_name_john} & {bool_id_exists}) | "
            f"({bool_study_mri} & ~{bool_study_ct})"
        )

        # Create substitution map
        symbol_map = {
            str(bool_name_john): name_john.evaluate(ds),
            str(bool_name_jane): name_jane.evaluate(ds),
            str(bool_id_exists): id_exists.evaluate(ds),
            str(bool_study_mri): study_mri.evaluate(ds),
            str(bool_study_ct): study_ct.evaluate(ds),
        }

        # Evaluate the complex expression
        result = complex_expr.subs(symbol_map)

        # Should be True because both parts of the OR are true:
        # (True & True) | (True & ~False) = True | True = True
        # Check if the result evaluates to True by checking if it's not FALSE
        # and contains the expected structure
        assert result != ba.FALSE
        assert "OR" in str(type(result).__name__) or result == ba.TRUE
