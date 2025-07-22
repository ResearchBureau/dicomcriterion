"""DICOM validation functions for boolean expression evaluation."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

import pydicom

from .exceptions import EvaluationError, FunctionNotFoundError


class DicomFunction(ABC):
    """Abstract base class for DICOM validation functions.

    This class defines the interface that all DICOM validation functions
    must implement. Functions are used within boolean expressions to
    validate DICOM attribute values.
    """

    @abstractmethod
    def evaluate(
        self, dataset: pydicom.Dataset, attribute: str, argument: Optional[str] = None
    ) -> bool:
        """Evaluate the function against a DICOM dataset attribute.

        Parameters
        ----------
        dataset : pydicom.Dataset
            The DICOM dataset to evaluate against
        attribute : str
            The DICOM attribute name or tag to check
        argument : str, optional
            Function argument (e.g., value to compare against)

        Returns
        -------
        bool
            Result of the function evaluation

        Raises
        ------
        EvaluationError
            If evaluation fails due to invalid data or other errors
        """
        pass


class FunctionRegistry:
    """Registry for managing available DICOM validation functions.

    This class maintains a registry of available DICOM functions that
    can be used in boolean expressions. It provides methods to register
    new functions and retrieve them by name.
    """

    def __init__(self) -> None:
        """Initialize an empty function registry."""
        self._functions: Dict[str, Type[DicomFunction]] = {}

    def register(self, name: str, func_class: Type[DicomFunction]) -> None:
        """Register a DICOM function class.

        Parameters
        ----------
        name : str
            The name to register the function under
        func_class : Type[DicomFunction]
            The function class to register

        Raises
        ------
        TypeError
            If func_class is not a subclass of DicomFunction
        """
        if not issubclass(func_class, DicomFunction):
            raise TypeError(
                f"Function class must be a subclass of DicomFunction, "
                f"got {func_class.__name__}"
            )

        self._functions[name] = func_class

    def get_function(self, name: str) -> DicomFunction:
        """Get a function instance by name.

        Parameters
        ----------
        name : str
            The name of the function to retrieve

        Returns
        -------
        DicomFunction
            An instance of the requested function

        Raises
        ------
        FunctionNotFoundError
            If the function name is not registered
        """
        if name not in self._functions:
            available = list(self._functions.keys())
            raise FunctionNotFoundError(name, available)

        return self._functions[name]()

    def is_registered(self, name: str) -> bool:
        """Check if a function name is registered.

        Parameters
        ----------
        name : str
            The function name to check

        Returns
        -------
        bool
            True if the function is registered, False otherwise
        """
        return name in self._functions

    def get_registered_names(self) -> list[str]:
        """Get a list of all registered function names.

        Returns
        -------
        list[str]
            List of registered function names
        """
        return list(self._functions.keys())


class EqualsFunction(DicomFunction):
    """DICOM function that checks if an attribute equals a specific value.

    This function compares DICOM attribute values with a provided argument,
    handling type conversion and comparison logic appropriately.
    """

    def evaluate(
        self, dataset: pydicom.Dataset, attribute: str, argument: Optional[str] = None
    ) -> bool:
        """Check if DICOM attribute equals the specified value.

        Parameters
        ----------
        dataset : pydicom.Dataset
            The DICOM dataset to evaluate against
        attribute : str
            The DICOM attribute name or tag to check
        argument : str, optional
            The value to compare against (required for equals function)

        Returns
        -------
        bool
            True if the attribute equals the argument, False otherwise

        Raises
        ------
        EvaluationError
            If argument is None or evaluation fails
        """
        if argument is None:
            raise EvaluationError(
                attribute=attribute, details="equals() function requires an argument"
            )

        try:
            # Try to get the attribute value from the dataset
            if isinstance(attribute, str) and hasattr(dataset, attribute):
                # Access by attribute name (e.g., PatientName)
                dicom_value = getattr(dataset, attribute)
            elif attribute in dataset:
                # Access by tag or keyword
                dicom_value = dataset[attribute].value
            else:
                # Attribute doesn't exist, equals comparison is False
                return False

            # Handle different DICOM value types
            if dicom_value is None:
                return argument.lower() in ("none", "null", "")

            # Convert DICOM value to string for comparison
            if hasattr(dicom_value, "value"):
                # Handle DataElement objects
                compare_value = str(dicom_value.value)
            else:
                # Handle direct values
                compare_value = str(dicom_value)

            # Perform case-insensitive comparison
            return compare_value.strip().lower() == argument.strip().lower()

        except Exception as e:
            raise EvaluationError(
                attribute=attribute,
                details=f"Failed to evaluate equals function: {str(e)}",
            ) from e


class ContainsFunction(DicomFunction):
    """DICOM function that checks if an attribute contains a substring.

    This function performs substring matching in DICOM attribute values,
    handling string conversion and case sensitivity appropriately.
    """

    def evaluate(
        self, dataset: pydicom.Dataset, attribute: str, argument: Optional[str] = None
    ) -> bool:
        """Check if DICOM attribute contains the specified substring.

        Parameters
        ----------
        dataset : pydicom.Dataset
            The DICOM dataset to evaluate against
        attribute : str
            The DICOM attribute name or tag to check
        argument : str, optional
            The substring to search for (required for contains function)

        Returns
        -------
        bool
            True if the attribute contains the substring, False otherwise

        Raises
        ------
        EvaluationError
            If argument is None or evaluation fails
        """
        if argument is None:
            raise EvaluationError(
                attribute=attribute,
                details="contains() function requires an argument",
            )

        try:
            # Try to get the attribute value from the dataset
            if isinstance(attribute, str) and hasattr(dataset, attribute):
                # Access by attribute name (e.g., PatientName)
                dicom_value = getattr(dataset, attribute)
            elif attribute in dataset:
                # Access by tag or keyword
                dicom_value = dataset[attribute].value
            else:
                # Attribute doesn't exist, contains comparison is False
                return False

            # Handle different DICOM value types
            if dicom_value is None:
                # None values can't contain anything
                return False

            # Convert DICOM value to string for substring search
            if hasattr(dicom_value, "value"):
                # Handle DataElement objects
                search_text = str(dicom_value.value)
            else:
                # Handle direct values
                search_text = str(dicom_value)

            # Perform case-insensitive substring search
            return argument.lower() in search_text.lower()

        except Exception as e:
            raise EvaluationError(
                attribute=attribute,
                details=f"Failed to evaluate contains function: {str(e)}",
            ) from e


class ExistsFunction(DicomFunction):
    """DICOM function that checks if an attribute exists in the dataset.

    This function checks for the presence of DICOM attributes in a dataset,
    handling missing attributes gracefully.
    """

    def evaluate(
        self, dataset: pydicom.Dataset, attribute: str, argument: Optional[str] = None
    ) -> bool:
        """Check if DICOM attribute exists in the dataset.

        Parameters
        ----------
        dataset : pydicom.Dataset
            The DICOM dataset to evaluate against
        attribute : str
            The DICOM attribute name or tag to check for existence
        argument : str, optional
            Not used for exists function (should be None)

        Returns
        -------
        bool
            True if the attribute exists, False otherwise

        Raises
        ------
        EvaluationError
            If evaluation fails due to dataset access errors
        """
        try:
            # Check if attribute exists in the dataset
            if isinstance(attribute, str) and hasattr(dataset, attribute):
                # Check by attribute name (e.g., PatientName)
                # hasattr returns True even if the value is None
                return True
            elif attribute in dataset:
                # Check by tag or keyword
                return True
            else:
                # Attribute doesn't exist
                return False

        except Exception as e:
            raise EvaluationError(
                attribute=attribute,
                details=f"Failed to evaluate exists function: {str(e)}",
            ) from e


# Default registry instance with core functions registered
default_registry = FunctionRegistry()
default_registry.register("equals", EqualsFunction)
default_registry.register("contains", ContainsFunction)
default_registry.register("exists", ExistsFunction)
