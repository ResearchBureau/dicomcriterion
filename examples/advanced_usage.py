#!/usr/bin/env python3
"""Advanced usage examples for the DICOM Criterion library.

This script demonstrates advanced features including complex expressions,
real-world validation scenarios, custom function registries, and
comprehensive error handling patterns.
"""

from pydicom import Dataset
from dicomcriterion import (
    Criterion,
    FunctionRegistry,
    DicomFunction,
    ExpressionParseError,
    EvaluationError,
)
from typing import Optional
import pydicom


class CustomValidationFunction(DicomFunction):
    """Custom validation function for demonstration purposes.

    This function checks if a numeric DICOM attribute is within a specified range.
    """

    def evaluate(
        self, dataset: pydicom.Dataset, attribute: str, argument: Optional[str] = None
    ) -> bool:
        """Check if numeric attribute is within range 'min-max'."""
        if argument is None:
            raise ValueError("Range function requires argument in format 'min-max'")

        try:
            min_val, max_val = map(float, argument.split("-"))
        except ValueError as err:
            raise ValueError(
                "Range argument must be in format 'min-max' (e.g., '18-65')"
            ) from err

        try:
            if hasattr(dataset, attribute):
                value = float(getattr(dataset, attribute))
                return min_val <= value <= max_val
            elif attribute in dataset:
                value = float(dataset[attribute].value)
                return min_val <= value <= max_val
            else:
                return False
        except (ValueError, TypeError):
            return False


def create_comprehensive_dataset():
    """Create a comprehensive DICOM dataset for advanced examples.

    Returns
    -------
    pydicom.Dataset
        Comprehensive dataset with various DICOM attributes
    """
    dataset = Dataset()

    # Patient information
    dataset.PatientName = "John Doe"
    dataset.PatientID = "HOSP12345"
    dataset.PatientBirthDate = "19800101"
    dataset.PatientAge = "044Y"
    dataset.PatientSex = "M"
    dataset.PatientWeight = "75.5"

    # Study information
    dataset.StudyDescription = "Brain MRI with contrast - STAT"
    dataset.StudyDate = "20240101"
    dataset.StudyTime = "143000"
    dataset.StudyInstanceUID = "1.2.3.4.5.6.7.8.9"
    dataset.AccessionNumber = "ACC2024001"

    # Series information
    dataset.SeriesDescription = "T1 MPRAGE post contrast"
    dataset.Modality = "MR"
    dataset.SeriesNumber = "3"

    # Institution information
    dataset.InstitutionName = "General Hospital"
    dataset.InstitutionalDepartmentName = "Radiology"

    return dataset


def create_emergency_dataset():
    """Create an emergency case dataset."""
    dataset = Dataset()
    dataset.PatientName = "EMERGENCY Patient"
    dataset.PatientID = "EMRG999"
    dataset.StudyDescription = "STAT Head CT - Trauma"
    dataset.StudyDate = "20240101"
    dataset.Modality = "CT"
    dataset.InstitutionName = "Emergency Hospital"

    return dataset


def create_test_dataset():
    """Create a test/QA dataset."""
    dataset = Dataset()
    dataset.PatientName = "PHANTOM Test"
    dataset.PatientID = "QA001"
    dataset.StudyDescription = "Daily QA TEST - Phantom"
    dataset.StudyDate = "20240101"
    dataset.Modality = "MR"
    dataset.InstitutionName = "General Hospital"

    return dataset


def example_complex_validation_rules():
    """Demonstrate complex validation rules for real-world scenarios."""
    print("=== Complex Validation Rules ===")

    dataset = create_comprehensive_dataset()

    # Patient privacy validation
    privacy_rule = """
    not (PatientName.equals('Anonymous') or
         PatientName.equals('') or
         PatientName.contains('UNKNOWN')) and
    PatientID.exists() and
    PatientBirthDate.exists()
    """

    criterion = Criterion(privacy_rule)
    result = criterion.evaluate(dataset)
    print(f"Patient privacy validation: {result}")  # True

    # Study quality validation
    quality_rule = """
    StudyDescription.exists() and
    not (StudyDescription.contains('TEST') or
         StudyDescription.contains('PHANTOM') or
         StudyDescription.contains('QA')) and
    (StudyDescription.contains('MRI') or
     StudyDescription.contains('CT') or
     StudyDescription.contains('X-RAY'))
    """

    criterion = Criterion(quality_rule)
    result = criterion.evaluate(dataset)
    print(
        f"Study quality validation: {result}"
    )  # False (contains 'MRI' but also 'STAT')

    # Emergency study identification
    emergency_rule = """
    (StudyDescription.contains('STAT') or
     StudyDescription.contains('EMERGENCY') or
     PatientName.contains('EMERGENCY')) and
    not StudyDescription.contains('TEST')
    """

    criterion = Criterion(emergency_rule)
    result = criterion.evaluate(dataset)
    print(f"Emergency study identification: {result}")  # True

    print()


def example_multiple_datasets():
    """Demonstrate validation across multiple different datasets."""
    print("=== Multiple Dataset Validation ===")

    datasets = {
        "Regular Patient": create_comprehensive_dataset(),
        "Emergency Case": create_emergency_dataset(),
        "Test/QA Study": create_test_dataset(),
    }

    # Define validation rules
    rules = {
        "Has Patient Info": "PatientName.exists() and PatientID.exists()",
        "Is Emergency": (
            "StudyDescription.contains('STAT') or "
            "StudyDescription.contains('EMERGENCY') or "
            "PatientName.contains('EMERGENCY')"
        ),
        "Is Test Study": (
            "StudyDescription.contains('TEST') or "
            "StudyDescription.contains('PHANTOM') or "
            "StudyDescription.contains('QA')"
        ),
        "Is Clinical Study": (
            "not (StudyDescription.contains('TEST') or "
            "StudyDescription.contains('PHANTOM') or "
            "StudyDescription.contains('QA'))"
        ),
        "Has MRI": "StudyDescription.contains('MRI') or Modality.equals('MR')",
        "Has CT": "StudyDescription.contains('CT') or Modality.equals('CT')",
    }

    # Evaluate each rule against each dataset
    print(f"{'Dataset':<15} {'Rule':<20} {'Result'}")
    print("-" * 50)

    for dataset_name, dataset in datasets.items():
        for rule_name, rule_expression in rules.items():
            try:
                criterion = Criterion(rule_expression)
                result = criterion.evaluate(dataset)
                print(f"{dataset_name:<15} {rule_name:<20} {result}")
            except Exception as e:
                print(f"{dataset_name:<15} {rule_name:<20} ERROR: {e}")

    print()


def example_custom_function_registry():
    """Demonstrate custom function registry with additional functions."""
    print("=== Custom Function Registry ===")

    # Import the function classes
    from dicomcriterion.functions import (
        EqualsFunction,
        ContainsFunction,
        ExistsFunction,
    )

    # Create custom registry with additional function
    custom_registry = FunctionRegistry()
    custom_registry.register("equals", EqualsFunction)
    custom_registry.register("contains", ContainsFunction)
    custom_registry.register("exists", ExistsFunction)
    custom_registry.register("in_range", CustomValidationFunction)

    # Create dataset with numeric values
    dataset = create_comprehensive_dataset()

    # Use custom function in expression
    try:
        criterion = Criterion(
            "PatientWeight.in_range('60-90')", registry=custom_registry
        )
        result = criterion.evaluate(dataset)
        print(
            f"Patient weight in range " f"60-90 kg: {result}"
        )  # True (75.5 is in range)

        criterion = Criterion(
            "PatientWeight.in_range('80-100')", registry=custom_registry
        )
        result = criterion.evaluate(dataset)
        print(
            f"Patient weight in range 80-100 kg: {result}"
        )  # False (75.5 is not in range)

    except Exception as e:
        print(f"Custom function error: {e}")

    print()


def example_comprehensive_error_handling():
    """Demonstrate comprehensive error handling patterns."""
    print("=== Comprehensive Error Handling ===")

    dataset = create_comprehensive_dataset()

    # Collection of invalid expressions for testing
    invalid_expressions = [
        ("", "Empty expression"),
        (
            "PatientName.equals('John') and and StudyID.exists()",
            "Invalid boolean syntax",
        ),
        (
            "(PatientName.equals('John') and StudyID.exists()",
            "Mismatched parentheses",
        ),
        ("PatientName.unknown_function('test')", "Unknown function"),
        ("invalid_format_without_dot", "Invalid symbol format"),
        ("PatientName.equals()", "Missing required argument"),
    ]

    for expression, description in invalid_expressions:
        try:
            criterion = Criterion(expression)
            result = criterion.evaluate(dataset)
            print(f"Unexpected success for {description}: {result}")
        except ExpressionParseError as e:
            print(f"Expression Parse Error ({description}): {e}")
        except Exception as e:
            print(f"Other Error ({description}): {type(e).__name__}: {e}")

    # Test evaluation errors
    print("\nEvaluation Error Examples:")

    try:
        criterion = Criterion("PatientName.equals('John')")
        result = criterion.evaluate(None)  # Invalid dataset
    except EvaluationError as e:
        print(f"Evaluation Error (None dataset): {e}")
    except Exception as e:
        print(f"Other Error (None dataset): {type(e).__name__}: {e}")

    print()


def example_performance_patterns():
    """Demonstrate performance considerations and best practices."""
    print("=== Performance Patterns ===")

    # Create multiple datasets
    datasets = [create_comprehensive_dataset() for _ in range(5)]

    # Pre-compile criterion for reuse
    criterion = Criterion("PatientName.exists() and StudyDescription.contains('MRI')")

    print("Evaluating same criterion against multiple datasets:")
    for i, dataset in enumerate(datasets, 1):
        result = criterion.evaluate(dataset)
        print(f"Dataset {i}: {result}")

    # Complex expression that should be optimized
    complex_expression = """
    (PatientName.exists() and PatientID.exists() and
     PatientBirthDate.exists()) and
    (StudyDescription.exists() and StudyDate.exists()) and
    (not (StudyDescription.contains('TEST') or
          StudyDescription.contains('PHANTOM'))) and
    (StudyDescription.contains('MRI') or
     StudyDescription.contains('CT') or
     StudyDescription.contains('X-RAY'))
    """

    criterion = Criterion(complex_expression)
    result = criterion.evaluate(datasets[0])
    print(f"\nComplex expression result: {result}")

    print()


def example_real_world_workflows():
    """Demonstrate real-world DICOM validation workflows."""
    print("=== Real-World Workflows ===")

    # Simulate a batch of DICOM studies
    studies = {
        "Study 1": create_comprehensive_dataset(),
        "Study 2": create_emergency_dataset(),
        "Study 3": create_test_dataset(),
    }

    # Define workflow validation rules
    workflows = {
        "Clinical Workflow": {
            "rule": (
                "not (StudyDescription.contains('TEST') or "
                "StudyDescription.contains('PHANTOM')) and "
                "PatientName.exists() and PatientID.exists()"
            ),
            "description": "Studies suitable for clinical workflow",
        },
        "Emergency Workflow": {
            "rule": (
                "(StudyDescription.contains('STAT') or "
                "StudyDescription.contains('EMERGENCY') or "
                "PatientName.contains('EMERGENCY')) and "
                "not StudyDescription.contains('TEST')"
            ),
            "description": "Studies requiring emergency processing",
        },
        "QA Workflow": {
            "rule": (
                "StudyDescription.contains('TEST') or "
                "StudyDescription.contains('PHANTOM') or "
                "StudyDescription.contains('QA')"
            ),
            "description": "Studies for quality assurance workflow",
        },
        "Research Workflow": {
            "rule": (
                "PatientName.exists() and PatientID.exists() and "
                "not (StudyDescription.contains('TEST') or "
                "StudyDescription.contains('EMERGENCY'))"
            ),
            "description": "Studies suitable for research",
        },
    }

    print("Workflow Assignment Results:")
    print("=" * 60)

    for study_name, dataset in studies.items():
        print(f"\n{study_name}:")
        print(f"  Patient: {getattr(dataset, 'PatientName', 'N/A')}")
        print(f"  Study: {getattr(dataset, 'StudyDescription', 'N/A')}")
        print("  Workflow Assignments:")

        for workflow_name, workflow_info in workflows.items():
            try:
                criterion = Criterion(workflow_info["rule"])
                result = criterion.evaluate(dataset)
                status = "✓ ASSIGNED" if result else "✗ Not suitable"
                print(f"    {workflow_name}: {status}")
            except Exception as e:
                print(f"    {workflow_name}: ERROR - {e}")

    print()


def main():
    """Run all advanced example demonstrations."""
    print("DICOM Criterion Library - Advanced Usage Examples")
    print("=" * 55)
    print()

    example_complex_validation_rules()
    example_multiple_datasets()
    example_custom_function_registry()
    example_comprehensive_error_handling()
    example_performance_patterns()
    example_real_world_workflows()

    print("All advanced examples completed successfully!")


if __name__ == "__main__":
    main()
