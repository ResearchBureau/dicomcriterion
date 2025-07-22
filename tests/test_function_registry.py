"""Tests for the DICOM function registry system."""

import pytest
import pydicom

from dicomcriterion.exceptions import EvaluationError, FunctionNotFoundError
from dicomcriterion.functions import (
    DicomFunction,
    FunctionRegistry,
    EqualsFunction,
    ContainsFunction,
    ExistsFunction,
    default_registry,
)


class MockFunction(DicomFunction):
    """Mock DICOM function for testing purposes."""

    def evaluate(self, dataset, attribute, argument=None):
        """Mock evaluation that always returns True."""
        return True


class TestFunctionRegistry:
    """Test cases for the FunctionRegistry class."""

    def test_init_creates_empty_registry(self):
        """Test that a new registry starts empty."""
        registry = FunctionRegistry()
        assert registry.get_registered_names() == []

    def test_register_valid_function(self):
        """Test registering a valid DICOM function."""
        registry = FunctionRegistry()
        registry.register("mock", MockFunction)

        assert registry.is_registered("mock")
        assert "mock" in registry.get_registered_names()

    def test_register_invalid_function_raises_type_error(self):
        """Test that registering non-DicomFunction raises TypeError."""
        registry = FunctionRegistry()

        class NotADicomFunction:
            pass

        with pytest.raises(TypeError) as exc_info:
            registry.register("invalid", NotADicomFunction)

        assert "must be a subclass of DicomFunction" in str(exc_info.value)
        assert "NotADicomFunction" in str(exc_info.value)

    def test_get_function_returns_instance(self):
        """Test that get_function returns a function instance."""
        registry = FunctionRegistry()
        registry.register("mock", MockFunction)

        func = registry.get_function("mock")
        assert isinstance(func, MockFunction)
        assert isinstance(func, DicomFunction)

    def test_get_function_not_found_raises_error(self):
        """Test that getting unregistered function raises error."""
        registry = FunctionRegistry()
        registry.register("exists", ExistsFunction)

        with pytest.raises(FunctionNotFoundError) as exc_info:
            registry.get_function("nonexistent")

        error = exc_info.value
        assert error.function_name == "nonexistent"
        assert "exists" in error.available_functions

    def test_is_registered_returns_correct_status(self):
        """Test that is_registered returns correct boolean values."""
        registry = FunctionRegistry()

        assert not registry.is_registered("mock")

        registry.register("mock", MockFunction)
        assert registry.is_registered("mock")
        assert not registry.is_registered("other")

    def test_get_registered_names_returns_all_names(self):
        """Test that get_registered_names returns all registered names."""
        registry = FunctionRegistry()

        # Empty registry
        assert registry.get_registered_names() == []

        # Add functions
        registry.register("mock", MockFunction)
        registry.register("equals", EqualsFunction)

        names = registry.get_registered_names()
        assert len(names) == 2
        assert "mock" in names
        assert "equals" in names

    def test_register_overwrites_existing_function(self):
        """Test that registering same name overwrites previous function."""
        registry = FunctionRegistry()

        # Register first function
        registry.register("test", MockFunction)
        func1 = registry.get_function("test")
        assert isinstance(func1, MockFunction)

        # Register different function with same name
        registry.register("test", EqualsFunction)
        func2 = registry.get_function("test")
        assert isinstance(func2, EqualsFunction)
        assert not isinstance(func2, MockFunction)

    def test_multiple_function_registration(self):
        """Test registering multiple functions works correctly."""
        registry = FunctionRegistry()

        registry.register("equals", EqualsFunction)
        registry.register("contains", ContainsFunction)
        registry.register("exists", ExistsFunction)

        assert len(registry.get_registered_names()) == 3
        assert registry.is_registered("equals")
        assert registry.is_registered("contains")
        assert registry.is_registered("exists")

        # Test getting each function
        equals_func = registry.get_function("equals")
        contains_func = registry.get_function("contains")
        exists_func = registry.get_function("exists")

        assert isinstance(equals_func, EqualsFunction)
        assert isinstance(contains_func, ContainsFunction)
        assert isinstance(exists_func, ExistsFunction)


class TestDefaultRegistry:
    """Test cases for the default registry instance."""

    def test_default_registry_has_core_functions(self):
        """Test that default registry has all three core functions."""
        expected_functions = ["equals", "contains", "exists"]
        registered_names = default_registry.get_registered_names()

        for func_name in expected_functions:
            assert func_name in registered_names
            assert default_registry.is_registered(func_name)

    def test_default_registry_equals_function(self):
        """Test that default registry equals function works."""
        func = default_registry.get_function("equals")
        assert isinstance(func, EqualsFunction)

    def test_default_registry_contains_function(self):
        """Test that default registry contains function works."""
        func = default_registry.get_function("contains")
        assert isinstance(func, ContainsFunction)

    def test_default_registry_exists_function(self):
        """Test that default registry exists function works."""
        func = default_registry.get_function("exists")
        assert isinstance(func, ExistsFunction)

    def test_default_registry_function_evaluation(self):
        """Test that functions from default registry can evaluate."""
        # Create a simple DICOM dataset for testing
        dataset = pydicom.Dataset()
        dataset.PatientName = "John Doe"
        dataset.StudyDescription = "MRI Brain"

        # Test equals function
        equals_func = default_registry.get_function("equals")
        assert equals_func.evaluate(dataset, "PatientName", "John Doe")
        assert not equals_func.evaluate(dataset, "PatientName", "Jane Doe")

        # Test contains function
        contains_func = default_registry.get_function("contains")
        assert contains_func.evaluate(dataset, "StudyDescription", "MRI")
        assert not contains_func.evaluate(dataset, "StudyDescription", "CT")

        # Test exists function
        exists_func = default_registry.get_function("exists")
        assert exists_func.evaluate(dataset, "PatientName")
        assert not exists_func.evaluate(dataset, "NonExistentAttribute")

    def test_default_registry_is_separate_instance(self):
        """Test that default registry is separate from new instances."""
        new_registry = FunctionRegistry()

        # Default registry should have functions, new one should be empty
        assert len(default_registry.get_registered_names()) == 3
        assert len(new_registry.get_registered_names()) == 0

        # Modifying new registry shouldn't affect default
        new_registry.register("test", MockFunction)
        assert new_registry.is_registered("test")
        assert not default_registry.is_registered("test")


class TestFunctionRegistryIntegration:
    """Integration tests for function registry with actual DICOM data."""

    def test_registry_with_real_dicom_dataset(self):
        """Test registry functions with a realistic DICOM dataset."""
        # Create a more realistic DICOM dataset
        dataset = pydicom.Dataset()
        dataset.PatientName = "Smith^John^A"
        dataset.PatientID = "12345"
        dataset.StudyDescription = "MRI Brain with Contrast"
        dataset.Modality = "MR"
        dataset.StudyDate = "20240101"

        registry = FunctionRegistry()
        registry.register("equals", EqualsFunction)
        registry.register("contains", ContainsFunction)
        registry.register("exists", ExistsFunction)

        # Test various scenarios
        equals_func = registry.get_function("equals")
        contains_func = registry.get_function("contains")
        exists_func = registry.get_function("exists")

        # Equals tests
        assert equals_func.evaluate(dataset, "PatientID", "12345")
        assert equals_func.evaluate(dataset, "Modality", "MR")
        assert not equals_func.evaluate(dataset, "Modality", "CT")

        # Contains tests
        assert contains_func.evaluate(dataset, "StudyDescription", "Brain")
        assert contains_func.evaluate(dataset, "StudyDescription", "Contrast")
        assert contains_func.evaluate(dataset, "PatientName", "John")
        assert not contains_func.evaluate(dataset, "StudyDescription", "Chest")

        # Exists tests
        assert exists_func.evaluate(dataset, "PatientName")
        assert exists_func.evaluate(dataset, "StudyDate")
        assert not exists_func.evaluate(dataset, "SeriesDescription")

    def test_registry_error_handling(self):
        """Test that registry properly handles function evaluation errors."""
        registry = FunctionRegistry()
        registry.register("equals", EqualsFunction)

        dataset = pydicom.Dataset()
        dataset.PatientName = "Test Patient"

        equals_func = registry.get_function("equals")

        # Test that missing argument raises appropriate error
        with pytest.raises((EvaluationError, TypeError)):
            equals_func.evaluate(dataset, "PatientName", None)
