#!/usr/bin/env python3
"""Basic usage examples for the DICOM Criterion library.

This script demonstrates the fundamental features of the DICOM Criterion
library, including simple expressions, basic functions, and dataset evaluation.
"""

from pydicom import Dataset
from dicomcriterion import Criterion


def create_sample_dataset():
    """Create a sample DICOM dataset for demonstration purposes.

    Returns
    -------
    pydicom.Dataset
        Sample dataset with common DICOM attributes
    """
    dataset = Dataset()
    dataset.PatientName = "John Doe"
    dataset.PatientID = "12345"
    dataset.PatientBirthDate = "19800101"
    dataset.StudyDescription = "Brain MRI with contrast"
    dataset.StudyDate = "20240101"
    dataset.Modality = "MR"
    dataset.InstitutionName = "General Hospital"

    return dataset


def example_equals_function():
    """Demonstrate the equals() function for exact value matching."""
    print("=== Equals Function Examples ===")

    dataset = create_sample_dataset()

    # Simple equality check
    criterion = Criterion("PatientName.equals('John Doe')")
    result = criterion.evaluate(dataset)
    print(f"PatientName equals 'John Doe': {result}")  # True

    # Case-insensitive comparison
    criterion = Criterion("PatientName.equals('john doe')")
    result = criterion.evaluate(dataset)
    print(f"PatientName equals 'john doe' (case-insensitive): {result}")  # True

    # Non-matching value
    criterion = Criterion("PatientName.equals('Jane Smith')")
    result = criterion.evaluate(dataset)
    print(f"PatientName equals 'Jane Smith': {result}")  # False

    # Numeric comparison
    criterion = Criterion("PatientID.equals('12345')")
    result = criterion.evaluate(dataset)
    print(f"PatientID equals '12345': {result}")  # True

    print()


def example_contains_function():
    """Demonstrate the contains() function for substring matching."""
    print("=== Contains Function Examples ===")

    dataset = create_sample_dataset()

    # Substring search in study description
    criterion = Criterion("StudyDescription.contains('MRI')")
    result = criterion.evaluate(dataset)
    print(f"StudyDescription contains 'MRI': {result}")  # True

    # Case-insensitive substring search
    criterion = Criterion("StudyDescription.contains('brain')")
    result = criterion.evaluate(dataset)
    print(f"StudyDescription contains 'brain' (case-insensitive): {result}")  # True

    # Non-matching substring
    criterion = Criterion("StudyDescription.contains('CT')")
    result = criterion.evaluate(dataset)
    print(f"StudyDescription contains 'CT': {result}")  # False

    # Partial name matching
    criterion = Criterion("PatientName.contains('John')")
    result = criterion.evaluate(dataset)
    print(f"PatientName contains 'John': {result}")  # True

    print()


def example_exists_function():
    """Demonstrate the exists() function for attribute presence checking."""
    print("=== Exists Function Examples ===")

    dataset = create_sample_dataset()

    # Check for existing attributes
    criterion = Criterion("PatientName.exists()")
    result = criterion.evaluate(dataset)
    print(f"PatientName exists: {result}")  # True

    criterion = Criterion("StudyDescription.exists()")
    result = criterion.evaluate(dataset)
    print(f"StudyDescription exists: {result}")  # True

    # Check for non-existing attribute
    criterion = Criterion("SeriesDescription.exists()")
    result = criterion.evaluate(dataset)
    print(f"SeriesDescription exists: {result}")  # False

    # Multiple existence checks
    criterion = Criterion("PatientID.exists()")
    result = criterion.evaluate(dataset)
    print(f"PatientID exists: {result}")  # True

    print()


def example_boolean_operators():
    """Demonstrate boolean operators (and, or, not) in expressions."""
    print("=== Boolean Operators Examples ===")

    dataset = create_sample_dataset()

    # AND operator - both conditions must be true
    criterion = Criterion(
        "PatientName.equals('John Doe') and " "StudyDescription.contains('MRI')"
    )
    result = criterion.evaluate(dataset)
    print(
        f"PatientName is 'John Doe' AND StudyDescription contains 'MRI': {result}"
    )  # True

    # OR operator - at least one condition must be true
    criterion = Criterion(
        "StudyDescription.contains('CT') or " "StudyDescription.contains('MRI')"
    )
    result = criterion.evaluate(dataset)
    print(f"StudyDescription contains 'CT' OR 'MRI': {result}")  # True

    # NOT operator - inverts the result
    criterion = Criterion("not PatientName.equals('Anonymous')")
    result = criterion.evaluate(dataset)
    print(f"PatientName is NOT 'Anonymous': {result}")  # True

    # Complex combination
    criterion = Criterion(
        "PatientID.exists() and not " "PatientName.equals('Anonymous')"
    )
    result = criterion.evaluate(dataset)
    print(f"PatientID exists AND PatientName is NOT 'Anonymous': {result}")  # True

    print()


def example_parentheses_grouping():
    """Demonstrate parentheses for grouping and precedence control."""
    print("=== Parentheses Grouping Examples ===")

    dataset = create_sample_dataset()

    # Without parentheses - AND has higher precedence than OR
    criterion = Criterion(
        "PatientName.equals('John Doe') or "
        "PatientName.equals('Jane Smith') and "
        "StudyDescription.contains('CT')"
    )
    result = criterion.evaluate(dataset)
    print(
        f"Without parentheses: {result}"
    )  # True (because PatientName equals 'John Doe')

    # With parentheses - explicit grouping
    criterion = Criterion(
        "(PatientName.equals('John Doe') or "
        "PatientName.equals('Jane Smith')) and "
        "StudyDescription.contains('MRI')"
    )
    result = criterion.evaluate(dataset)
    print(f"With parentheses - both name matches and MRI: {result}")  # True

    # Complex nested grouping
    criterion = Criterion(
        "(PatientName.exists() and PatientID.exists()) and "
        "(StudyDescription.contains('MRI') or "
        "StudyDescription.contains('CT'))"
    )
    result = criterion.evaluate(dataset)
    print(f"Complex nested grouping: {result}")  # True

    print()


def example_error_handling():
    """Demonstrate error handling for invalid expressions and datasets."""
    print("=== Error Handling Examples ===")

    dataset = create_sample_dataset()

    # Invalid expression syntax
    try:
        criterion = Criterion("PatientName.equals('John') and and StudyID.exists()")
    except Exception as e:
        print(f"Invalid syntax error: {type(e).__name__}: {e}")

    # Invalid function name
    try:
        criterion = Criterion("PatientName.unknown_function('test')")
    except Exception as e:
        print(f"Unknown function error: {type(e).__name__}: {e}")

    # Missing required argument
    try:
        criterion = Criterion("PatientName.equals()")
        criterion.evaluate(dataset)
    except Exception as e:
        print(f"Missing argument error: {type(e).__name__}: {e}")

    print()


def main():
    """Run all example demonstrations."""
    print("DICOM Criterion Library - Basic Usage Examples")
    print("=" * 50)
    print()

    example_equals_function()
    example_contains_function()
    example_exists_function()
    example_boolean_operators()
    example_parentheses_grouping()
    example_error_handling()

    print("All examples completed successfully!")


if __name__ == "__main__":
    main()
