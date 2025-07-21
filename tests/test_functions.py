"""Tests for DICOM function interface and registry."""

import pytest
import pydicom
from pydicom.dataset import Dataset
from pydicom.dataelem import DataElement
from pydicom.valuerep import VR

from dicom_criterion.exceptions import EvaluationError, FunctionNotFoundError
from dicom_criterion.functions import (
    DicomFunction,
    EqualsFunction,
    ContainsFunction,
    ExistsFunction,
    FunctionRegistry,
)


class MockDicomFunction(DicomFunction):
    """Mock DICOM function for testing."""

    def evaluate(
        self, dataset: pydicom.Dataset, attribute: str, argument: str = None
    ) -> bool:
        """Mock evaluation that always returns True."""
        return True


class AnotherMockFunction(DicomFunction):
    """Another mock DICOM function for testing."""

    def evaluate(
        self, dataset: pydicom.Dataset, attribute: str, argument: str = None
    ) -> bool:
        """Mock evaluation that always returns False."""
        return False


class InvalidFunction:
    """Invalid function class that doesn't inherit from DicomFunction."""

    def evaluate(self, dataset, attribute, argument=None):
        """Mock evaluate method."""
        return True


class TestDicomFunction:
    """Test cases for DicomFunction abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that DicomFunction cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            DicomFunction()

    def test_concrete_implementation_works(self):
        """Test that concrete implementations can be instantiated."""
        func = MockDicomFunction()
        assert isinstance(func, DicomFunction)

    def test_concrete_implementation_has_evaluate_method(self):
        """Test that concrete implementations have evaluate method."""
        func = MockDicomFunction()
        assert hasattr(func, "evaluate")
        assert callable(func.evaluate)


class TestFunctionRegistry:
    """Test cases for FunctionRegistry class."""

    def test_empty_registry_initialization(self):
        """Test that registry initializes empty."""
        registry = FunctionRegistry()
        assert registry.get_registered_names() == []

    def test_register_valid_function(self):
        """Test registering a valid DICOM function."""
        registry = FunctionRegistry()
        registry.register("mock", MockDicomFunction)

        assert registry.is_registered("mock")
        assert "mock" in registry.get_registered_names()

    def test_register_invalid_function_raises_error(self):
        """Test that registering invalid function raises TypeError."""
        registry = FunctionRegistry()

        with pytest.raises(TypeError, match="must be a subclass of DicomFunction"):
            registry.register("invalid", InvalidFunction)

    def test_get_function_returns_instance(self):
        """Test that get_function returns function instance."""
        registry = FunctionRegistry()
        registry.register("mock", MockDicomFunction)

        func = registry.get_function("mock")
        assert isinstance(func, MockDicomFunction)
        assert isinstance(func, DicomFunction)

    def test_get_function_creates_new_instance_each_time(self):
        """Test that get_function creates new instances."""
        registry = FunctionRegistry()
        registry.register("mock", MockDicomFunction)

        func1 = registry.get_function("mock")
        func2 = registry.get_function("mock")

        assert func1 is not func2
        assert type(func1) == type(func2)

    def test_get_unregistered_function_raises_error(self):
        """Test that getting unregistered function raises error."""
        registry = FunctionRegistry()

        with pytest.raises(FunctionNotFoundError) as exc_info:
            registry.get_function("nonexistent")

        assert exc_info.value.function_name == "nonexistent"
        assert exc_info.value.available_functions == []

    def test_get_unregistered_function_shows_available_functions(self):
        """Test that error shows available functions when some exist."""
        registry = FunctionRegistry()
        registry.register("mock1", MockDicomFunction)
        registry.register("mock2", AnotherMockFunction)

        with pytest.raises(FunctionNotFoundError) as exc_info:
            registry.get_function("nonexistent")

        assert exc_info.value.function_name == "nonexistent"
        assert set(exc_info.value.available_functions) == {"mock1", "mock2"}

    def test_is_registered_with_registered_function(self):
        """Test is_registered returns True for registered functions."""
        registry = FunctionRegistry()
        registry.register("mock", MockDicomFunction)

        assert registry.is_registered("mock") is True

    def test_is_registered_with_unregistered_function(self):
        """Test is_registered returns False for unregistered functions."""
        registry = FunctionRegistry()

        assert registry.is_registered("nonexistent") is False

    def test_get_registered_names_with_multiple_functions(self):
        """Test get_registered_names returns all registered names."""
        registry = FunctionRegistry()
        registry.register("func1", MockDicomFunction)
        registry.register("func2", AnotherMockFunction)

        names = registry.get_registered_names()
        assert set(names) == {"func1", "func2"}

    def test_register_overwrites_existing_function(self):
        """Test that registering same name overwrites previous function."""
        registry = FunctionRegistry()
        registry.register("func", MockDicomFunction)
        registry.register("func", AnotherMockFunction)

        func = registry.get_function("func")
        assert isinstance(func, AnotherMockFunction)
        assert not isinstance(func, MockDicomFunction)


class TestEqualsFunction:
    """Test cases for EqualsFunction class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.func = EqualsFunction()
        self.dataset = Dataset()

    def test_equals_function_is_dicom_function(self):
        """Test that EqualsFunction is a DicomFunction."""
        assert isinstance(self.func, DicomFunction)

    def test_equals_with_no_argument_raises_error(self):
        """Test that equals without argument raises EvaluationError."""
        with pytest.raises(EvaluationError) as exc_info:
            self.func.evaluate(self.dataset, "PatientName")

        assert "equals() function requires an argument" in str(exc_info.value)
        assert exc_info.value.attribute == "PatientName"

    def test_equals_with_missing_attribute_returns_false(self):
        """Test that equals with missing attribute returns False."""
        result = self.func.evaluate(self.dataset, "PatientName", "John Doe")
        assert result is False

    def test_equals_with_matching_string_attribute(self):
        """Test equals with matching string attribute."""
        self.dataset.PatientName = "John Doe"

        result = self.func.evaluate(self.dataset, "PatientName", "John Doe")
        assert result is True

    def test_equals_with_non_matching_string_attribute(self):
        """Test equals with non-matching string attribute."""
        self.dataset.PatientName = "John Doe"

        result = self.func.evaluate(self.dataset, "PatientName", "Jane Smith")
        assert result is False

    def test_equals_case_insensitive_comparison(self):
        """Test that equals comparison is case-insensitive."""
        self.dataset.PatientName = "John Doe"

        result = self.func.evaluate(self.dataset, "PatientName", "john doe")
        assert result is True

        result = self.func.evaluate(self.dataset, "PatientName", "JOHN DOE")
        assert result is True

    def test_equals_with_whitespace_handling(self):
        """Test that equals handles whitespace correctly."""
        self.dataset.PatientName = "  John Doe  "

        result = self.func.evaluate(self.dataset, "PatientName", "John Doe")
        assert result is True

        result = self.func.evaluate(self.dataset, "PatientName", "  John Doe  ")
        assert result is True

    def test_equals_with_numeric_values(self):
        """Test equals with numeric DICOM values."""
        self.dataset.PatientAge = "025Y"

        result = self.func.evaluate(self.dataset, "PatientAge", "025Y")
        assert result is True

        result = self.func.evaluate(self.dataset, "PatientAge", "030Y")
        assert result is False

    def test_equals_with_data_element_access(self):
        """Test equals accessing attribute via dataset indexing."""
        # Create a DataElement directly
        data_elem = DataElement(0x00100010, VR.PN, "John Doe")
        self.dataset[0x00100010] = data_elem

        result = self.func.evaluate(self.dataset, 0x00100010, "John Doe")
        assert result is True

    def test_equals_with_none_value(self):
        """Test equals with None DICOM value."""
        self.dataset.PatientName = None

        result = self.func.evaluate(self.dataset, "PatientName", "none")
        assert result is True

        result = self.func.evaluate(self.dataset, "PatientName", "null")
        assert result is True

        result = self.func.evaluate(self.dataset, "PatientName", "")
        assert result is True

        result = self.func.evaluate(self.dataset, "PatientName", "John Doe")
        assert result is False

    def test_equals_with_integer_conversion(self):
        """Test equals with integer values converted to string."""
        self.dataset.SeriesNumber = 1

        result = self.func.evaluate(self.dataset, "SeriesNumber", "1")
        assert result is True

        result = self.func.evaluate(self.dataset, "SeriesNumber", "2")
        assert result is False

    def test_equals_with_float_conversion(self):
        """Test equals with float values converted to string."""
        self.dataset.SliceThickness = 5.0

        result = self.func.evaluate(self.dataset, "SliceThickness", "5.0")
        assert result is True

        result = self.func.evaluate(self.dataset, "SliceThickness", "5")
        assert result is False  # String comparison, not numeric

    def test_equals_with_list_values(self):
        """Test equals with list/sequence DICOM values."""
        self.dataset.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

        result = self.func.evaluate(
            self.dataset, "ImageOrientationPatient", "[1.0, 0.0, 0.0, 0.0, 1.0, 0.0]"
        )
        assert result is True

    def test_equals_error_handling(self):
        """Test that evaluation errors are properly handled."""
        # Create a dataset that will cause an error during access
        class ErrorDataset(Dataset):
            def __getattr__(self, name):
                if name == "PatientName":
                    raise ValueError("Simulated error")
                return super().__getattr__(name)

        error_dataset = ErrorDataset()

        with pytest.raises(EvaluationError) as exc_info:
            self.func.evaluate(error_dataset, "PatientName", "John Doe")

        assert "Failed to evaluate equals function" in str(exc_info.value)
        assert exc_info.value.attribute == "PatientName"


class TestContainsFunction:
    """Test cases for ContainsFunction class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.func = ContainsFunction()
        self.dataset = Dataset()

    def test_contains_function_is_dicom_function(self):
        """Test that ContainsFunction is a DicomFunction."""
        assert isinstance(self.func, DicomFunction)

    def test_contains_with_no_argument_raises_error(self):
        """Test that contains without argument raises EvaluationError."""
        with pytest.raises(EvaluationError) as exc_info:
            self.func.evaluate(self.dataset, "StudyDescription")

        assert "contains() function requires an argument" in str(exc_info.value)
        assert exc_info.value.attribute == "StudyDescription"

    def test_contains_with_missing_attribute_returns_false(self):
        """Test that contains with missing attribute returns False."""
        result = self.func.evaluate(self.dataset, "StudyDescription", "MRI")
        assert result is False

    def test_contains_with_matching_substring(self):
        """Test contains with matching substring."""
        self.dataset.StudyDescription = "Brain MRI with contrast"

        result = self.func.evaluate(self.dataset, "StudyDescription", "MRI")
        assert result is True

        result = self.func.evaluate(self.dataset, "StudyDescription", "Brain")
        assert result is True

        result = self.func.evaluate(self.dataset, "StudyDescription", "contrast")
        assert result is True

    def test_contains_with_non_matching_substring(self):
        """Test contains with non-matching substring."""
        self.dataset.StudyDescription = "Brain MRI with contrast"

        result = self.func.evaluate(self.dataset, "StudyDescription", "CT")
        assert result is False

        result = self.func.evaluate(self.dataset, "StudyDescription", "ultrasound")
        assert result is False

    def test_contains_case_insensitive_search(self):
        """Test that contains search is case-insensitive."""
        self.dataset.StudyDescription = "Brain MRI with contrast"

        result = self.func.evaluate(self.dataset, "StudyDescription", "mri")
        assert result is True

        result = self.func.evaluate(self.dataset, "StudyDescription", "BRAIN")
        assert result is True

        result = self.func.evaluate(self.dataset, "StudyDescription", "CoNtRaSt")
        assert result is True

    def test_contains_with_partial_word_match(self):
        """Test contains with partial word matching."""
        self.dataset.PatientName = "John Doe"

        result = self.func.evaluate(self.dataset, "PatientName", "Joh")
        assert result is True

        result = self.func.evaluate(self.dataset, "PatientName", "oe")
        assert result is True

        result = self.func.evaluate(self.dataset, "PatientName", "n D")
        assert result is True

    def test_contains_with_empty_string_argument(self):
        """Test contains with empty string argument."""
        self.dataset.StudyDescription = "Brain MRI"

        # Empty string is contained in any string
        result = self.func.evaluate(self.dataset, "StudyDescription", "")
        assert result is True

    def test_contains_with_numeric_values(self):
        """Test contains with numeric DICOM values."""
        self.dataset.PatientAge = "025Y"

        result = self.func.evaluate(self.dataset, "PatientAge", "25")
        assert result is True

        result = self.func.evaluate(self.dataset, "PatientAge", "Y")
        assert result is True

        result = self.func.evaluate(self.dataset, "PatientAge", "30")
        assert result is False

    def test_contains_with_data_element_access(self):
        """Test contains accessing attribute via dataset indexing."""
        # Create a DataElement directly
        data_elem = DataElement(0x00081030, VR.LO, "Brain MRI with contrast")
        self.dataset[0x00081030] = data_elem

        result = self.func.evaluate(self.dataset, 0x00081030, "MRI")
        assert result is True

        result = self.func.evaluate(self.dataset, 0x00081030, "CT")
        assert result is False

    def test_contains_with_none_value_returns_false(self):
        """Test contains with None DICOM value returns False."""
        self.dataset.StudyDescription = None

        result = self.func.evaluate(self.dataset, "StudyDescription", "MRI")
        assert result is False

        result = self.func.evaluate(self.dataset, "StudyDescription", "")
        assert result is False

    def test_contains_with_integer_conversion(self):
        """Test contains with integer values converted to string."""
        self.dataset.SeriesNumber = 123

        result = self.func.evaluate(self.dataset, "SeriesNumber", "12")
        assert result is True

        result = self.func.evaluate(self.dataset, "SeriesNumber", "23")
        assert result is True

        result = self.func.evaluate(self.dataset, "SeriesNumber", "45")
        assert result is False

    def test_contains_with_float_conversion(self):
        """Test contains with float values converted to string."""
        self.dataset.SliceThickness = 5.25

        result = self.func.evaluate(self.dataset, "SliceThickness", "5.2")
        assert result is True

        result = self.func.evaluate(self.dataset, "SliceThickness", ".25")
        assert result is True

        result = self.func.evaluate(self.dataset, "SliceThickness", "3.0")
        assert result is False

    def test_contains_with_list_values(self):
        """Test contains with list/sequence DICOM values."""
        self.dataset.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

        result = self.func.evaluate(self.dataset, "ImageOrientationPatient", "1.0")
        assert result is True

        result = self.func.evaluate(self.dataset, "ImageOrientationPatient", "0.0")
        assert result is True

        result = self.func.evaluate(self.dataset, "ImageOrientationPatient", "2.0")
        assert result is False

    def test_contains_with_special_characters(self):
        """Test contains with special characters in strings."""
        self.dataset.StudyDescription = "T1-weighted MRI (post-contrast)"

        result = self.func.evaluate(self.dataset, "StudyDescription", "T1-")
        assert result is True

        result = self.func.evaluate(self.dataset, "StudyDescription", "(post")
        assert result is True

        result = self.func.evaluate(self.dataset, "StudyDescription", "contrast)")
        assert result is True

    def test_contains_error_handling(self):
        """Test that evaluation errors are properly handled."""
        # Create a dataset that will cause an error during access
        class ErrorDataset(Dataset):
            def __getattr__(self, name):
                if name == "StudyDescription":
                    raise ValueError("Simulated error")
                return super().__getattr__(name)

        error_dataset = ErrorDataset()

        with pytest.raises(EvaluationError) as exc_info:
            self.func.evaluate(error_dataset, "StudyDescription", "MRI")

        assert "Failed to evaluate contains function" in str(exc_info.value)
        assert exc_info.value.attribute == "StudyDescription"


class TestExistsFunction:
    """Test cases for ExistsFunction class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.func = ExistsFunction()
        self.dataset = Dataset()

    def test_exists_function_is_dicom_function(self):
        """Test that ExistsFunction is a DicomFunction."""
        assert isinstance(self.func, DicomFunction)

    def test_exists_with_missing_attribute_returns_false(self):
        """Test that exists with missing attribute returns False."""
        result = self.func.evaluate(self.dataset, "PatientName")
        assert result is False

    def test_exists_with_existing_string_attribute(self):
        """Test exists with existing string attribute."""
        self.dataset.PatientName = "John Doe"

        result = self.func.evaluate(self.dataset, "PatientName")
        assert result is True

    def test_exists_with_existing_none_attribute(self):
        """Test exists with existing attribute that has None value."""
        self.dataset.PatientName = None

        # Attribute exists even if value is None
        result = self.func.evaluate(self.dataset, "PatientName")
        assert result is True

    def test_exists_with_existing_empty_string_attribute(self):
        """Test exists with existing attribute that has empty string value."""
        self.dataset.StudyDescription = ""

        result = self.func.evaluate(self.dataset, "StudyDescription")
        assert result is True

    def test_exists_with_numeric_attribute(self):
        """Test exists with numeric DICOM attributes."""
        self.dataset.SeriesNumber = 1
        self.dataset.SliceThickness = 5.0

        result = self.func.evaluate(self.dataset, "SeriesNumber")
        assert result is True

        result = self.func.evaluate(self.dataset, "SliceThickness")
        assert result is True

    def test_exists_with_list_attribute(self):
        """Test exists with list/sequence DICOM attributes."""
        self.dataset.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

        result = self.func.evaluate(self.dataset, "ImageOrientationPatient")
        assert result is True

    def test_exists_with_data_element_access(self):
        """Test exists accessing attribute via dataset indexing."""
        # Create a DataElement directly
        data_elem = DataElement(0x00100010, VR.PN, "John Doe")
        self.dataset[0x00100010] = data_elem

        result = self.func.evaluate(self.dataset, 0x00100010)
        assert result is True

        # Test with non-existent tag
        result = self.func.evaluate(self.dataset, 0x00100020)
        assert result is False

    def test_exists_with_data_element_none_value(self):
        """Test exists with DataElement that has None value."""
        # Create a DataElement with None value
        data_elem = DataElement(0x00100010, VR.PN, None)
        self.dataset[0x00100010] = data_elem

        result = self.func.evaluate(self.dataset, 0x00100010)
        assert result is True

    def test_exists_ignores_argument(self):
        """Test that exists function ignores any provided argument."""
        self.dataset.PatientName = "John Doe"

        # Should work the same regardless of argument
        result1 = self.func.evaluate(self.dataset, "PatientName")
        result2 = self.func.evaluate(self.dataset, "PatientName", "ignored")
        result3 = self.func.evaluate(self.dataset, "PatientName", None)

        assert result1 is True
        assert result2 is True
        assert result3 is True

    def test_exists_with_multiple_attributes(self):
        """Test exists with multiple different attributes."""
        self.dataset.PatientName = "John Doe"
        self.dataset.PatientAge = "30Y"
        self.dataset.StudyDescription = "Brain MRI"

        assert self.func.evaluate(self.dataset, "PatientName") is True
        assert self.func.evaluate(self.dataset, "PatientAge") is True
        assert self.func.evaluate(self.dataset, "StudyDescription") is True
        assert self.func.evaluate(self.dataset, "NonExistentAttribute") is False

    def test_exists_with_zero_values(self):
        """Test exists with attributes that have zero values."""
        self.dataset.SeriesNumber = 0
        self.dataset.SliceThickness = 0.0

        # Zero values should still count as existing
        result1 = self.func.evaluate(self.dataset, "SeriesNumber")
        result2 = self.func.evaluate(self.dataset, "SliceThickness")

        assert result1 is True
        assert result2 is True

    def test_exists_with_boolean_values(self):
        """Test exists with boolean DICOM values."""
        # Some DICOM attributes can have boolean-like values
        self.dataset.PatientSex = "M"  # This could be considered boolean-like

        result = self.func.evaluate(self.dataset, "PatientSex")
        assert result is True

    def test_exists_case_sensitivity_attribute_names(self):
        """Test that exists is case-sensitive for attribute names."""
        self.dataset.PatientName = "John Doe"

        # Correct case should work
        assert self.func.evaluate(self.dataset, "PatientName") is True

        # Wrong case should not work (DICOM attribute names are case-sensitive)
        assert self.func.evaluate(self.dataset, "patientname") is False
        assert self.func.evaluate(self.dataset, "PATIENTNAME") is False

    def test_exists_error_handling(self):
        """Test that evaluation errors are properly handled."""
        # Create a dataset that will cause an error during access
        class ErrorDataset(Dataset):
            def __contains__(self, key):
                if key == "PatientName":
                    raise ValueError("Simulated error")
                return super().__contains__(key)

        error_dataset = ErrorDataset()

        with pytest.raises(EvaluationError) as exc_info:
            self.func.evaluate(error_dataset, "PatientName")

        assert "Failed to evaluate exists function" in str(exc_info.value)
        assert exc_info.value.attribute == "PatientName"
