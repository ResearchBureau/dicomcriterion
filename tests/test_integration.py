"""Comprehensive integration tests for the DICOM Criterion class.

This module contains integration tests that verify the complete functionality
of the Criterion class with complex boolean expressions, multiple operators,
nested expressions, and comprehensive error handling.
"""

import pytest
from pydicom import Dataset

from dicomcriterion import (
    Criterion,
    ExpressionParseError,
    SymbolParseError,
    EvaluationError,
)


class TestComplexBooleanExpressions:
    """Test complex boolean expressions with multiple operators."""

    def test_complex_and_or_combination(self):
        """Test complex expression with both AND and OR operators.

        Requirements: 4.1, 4.2
        """
        expression = (
            "PatientName.equals('John') and "
            "(StudyDescription.contains('MRI') or "
            "StudyDescription.contains('CT'))"
        )
        criterion = Criterion(expression)

        # Test case 1: Matches PatientName and has MRI in StudyDescription
        dataset1 = Dataset()
        dataset1.PatientName = "John"
        dataset1.StudyDescription = "Brain MRI with contrast"

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Matches PatientName and has CT in StudyDescription
        dataset2 = Dataset()
        dataset2.PatientName = "John"
        dataset2.StudyDescription = "Chest CT scan"

        assert criterion.evaluate(dataset2) is True

        # Test case 3: Matches PatientName but has neither MRI nor CT
        dataset3 = Dataset()
        dataset3.PatientName = "John"
        dataset3.StudyDescription = "X-ray examination"

        assert criterion.evaluate(dataset3) is False

        # Test case 4: Doesn't match PatientName but has MRI
        dataset4 = Dataset()
        dataset4.PatientName = "Jane"
        dataset4.StudyDescription = "Brain MRI with contrast"

        assert criterion.evaluate(dataset4) is False

    def test_multiple_and_operators(self):
        """Test expression with multiple AND operators.

        Requirements: 4.1
        """
        expression = (
            "PatientName.equals('John') and PatientID.exists() "
            "and StudyDate.exists() and StudyDescription.contains('MRI')"
        )
        criterion = Criterion(expression)

        # Test case 1: All conditions satisfied
        dataset1 = Dataset()
        dataset1.PatientName = "John"
        dataset1.PatientID = "12345"
        dataset1.StudyDate = "20240101"
        dataset1.StudyDescription = "Brain MRI scan"

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Missing one condition (StudyDate)
        dataset2 = Dataset()
        dataset2.PatientName = "John"
        dataset2.PatientID = "12345"
        dataset2.StudyDescription = "Brain MRI scan"
        # StudyDate is missing

        assert criterion.evaluate(dataset2) is False

        # Test case 3: Missing multiple conditions
        dataset3 = Dataset()
        dataset3.PatientName = "John"
        # PatientID, StudyDate, and StudyDescription are missing

        assert criterion.evaluate(dataset3) is False

    def test_multiple_or_operators(self):
        """Test expression with multiple OR operators.

        Requirements: 4.2
        """
        expression = (
            "PatientName.equals('John') or PatientName.equals('Jane') "
            "or PatientName.equals('Bob') or PatientID.equals('EMERGENCY')"
        )
        criterion = Criterion(expression)

        # Test case 1: Matches first condition
        dataset1 = Dataset()
        dataset1.PatientName = "John"
        dataset1.PatientID = "12345"

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Matches middle condition
        dataset2 = Dataset()
        dataset2.PatientName = "Bob"
        dataset2.PatientID = "67890"

        assert criterion.evaluate(dataset2) is True

        # Test case 3: Matches last condition only
        dataset3 = Dataset()
        dataset3.PatientName = "Unknown"
        dataset3.PatientID = "EMERGENCY"

        assert criterion.evaluate(dataset3) is True

        # Test case 4: Matches none of the conditions
        dataset4 = Dataset()
        dataset4.PatientName = "Alice"
        dataset4.PatientID = "99999"

        assert criterion.evaluate(dataset4) is False

    def test_mixed_and_or_operators(self):
        """Test expression with mixed AND and OR operators.

        Requirements: 4.1, 4.2
        """
        expression = (
            "PatientName.equals('John') or "
            "PatientName.equals('Jane') and StudyDescription.contains('MRI')"
        )
        criterion = Criterion(expression)

        # Test case 1: Matches first OR condition (should be True regardless of AND)
        dataset1 = Dataset()
        dataset1.PatientName = "John"
        dataset1.StudyDescription = "CT scan"  # Doesn't contain MRI

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Matches second part of AND condition
        dataset2 = Dataset()
        dataset2.PatientName = "Jane"
        dataset2.StudyDescription = "Brain MRI scan"

        assert criterion.evaluate(dataset2) is True

        # Test case 3: Matches Jane but not MRI condition
        dataset3 = Dataset()
        dataset3.PatientName = "Jane"
        dataset3.StudyDescription = "CT scan"

        assert criterion.evaluate(dataset3) is False

        # Test case 4: Matches neither condition
        dataset4 = Dataset()
        dataset4.PatientName = "Bob"
        dataset4.StudyDescription = "X-ray"

        assert criterion.evaluate(dataset4) is False


class TestNestedExpressionsAndPrecedence:
    """Test nested expressions with parentheses and operator precedence."""

    def test_simple_parentheses_grouping(self):
        """Test simple parentheses for grouping operations.

        Requirements: 4.4
        """
        expression = (
            "(PatientName.equals('John') or "
            "PatientName.equals('Jane')) and StudyDescription.contains('MRI')"
        )
        criterion = Criterion(expression)

        # Test case 1: First name matches and has MRI
        dataset1 = Dataset()
        dataset1.PatientName = "John"
        dataset1.StudyDescription = "Brain MRI scan"

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Second name matches and has MRI
        dataset2 = Dataset()
        dataset2.PatientName = "Jane"
        dataset2.StudyDescription = "Spine MRI with contrast"

        assert criterion.evaluate(dataset2) is True

        # Test case 3: Name matches but no MRI
        dataset3 = Dataset()
        dataset3.PatientName = "John"
        dataset3.StudyDescription = "CT scan"

        assert criterion.evaluate(dataset3) is False

        # Test case 4: Has MRI but name doesn't match
        dataset4 = Dataset()
        dataset4.PatientName = "Bob"
        dataset4.StudyDescription = "Brain MRI scan"

        assert criterion.evaluate(dataset4) is False

    def test_nested_parentheses(self):
        """Test deeply nested parentheses expressions.

        Requirements: 4.4
        """
        expression = (
            "((PatientName.equals('John') or "
            "PatientName.equals('Jane')) and "
            "StudyDescription.contains('MRI')) or "
            "(PatientID.exists() and StudyDate.equals('20240101'))"
        )
        criterion = Criterion(expression)

        # Test case 1: Satisfies first complex condition
        dataset1 = Dataset()
        dataset1.PatientName = "John"
        dataset1.StudyDescription = "Brain MRI scan"
        dataset1.PatientID = "12345"
        dataset1.StudyDate = "20240102"  # Different date

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Satisfies second complex condition
        dataset2 = Dataset()
        dataset2.PatientName = "Bob"  # Doesn't match first condition
        dataset2.StudyDescription = "CT scan"  # Doesn't match first condition
        dataset2.PatientID = "67890"
        dataset2.StudyDate = "20240101"  # Matches second condition

        assert criterion.evaluate(dataset2) is True

        # Test case 3: Satisfies both complex conditions
        dataset3 = Dataset()
        dataset3.PatientName = "Jane"
        dataset3.StudyDescription = "Spine MRI"
        dataset3.PatientID = "99999"
        dataset3.StudyDate = "20240101"

        assert criterion.evaluate(dataset3) is True

        # Test case 4: Satisfies neither complex condition
        dataset4 = Dataset()
        dataset4.PatientName = "Bob"
        dataset4.StudyDescription = "CT scan"
        dataset4.StudyDate = "20240102"
        # PatientID is missing

        assert criterion.evaluate(dataset4) is False

    def test_operator_precedence_without_parentheses(self):
        """Test that operator precedence works correctly without explicit parentheses.

        Requirements: 4.4
        """
        # AND has higher precedence than OR
        expression = (
            "PatientName.equals('John') or "
            "PatientName.equals('Jane') and "
            "StudyDescription.contains('MRI')"
        )
        criterion = Criterion(expression)

        # This should be evaluated as: PatientName.equals('John') or
        # (PatientName.equals('Jane') and StudyDescription.contains('MRI'))

        # Test case 1: First condition is true (should be True
        # regardless of second part)
        dataset1 = Dataset()
        dataset1.PatientName = "John"
        dataset1.StudyDescription = "CT scan"  # No MRI

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Second part of AND is satisfied
        dataset2 = Dataset()
        dataset2.PatientName = "Jane"
        dataset2.StudyDescription = "Brain MRI"

        assert criterion.evaluate(dataset2) is True

        # Test case 3: Jane but no MRI (second part of AND fails)
        dataset3 = Dataset()
        dataset3.PatientName = "Jane"
        dataset3.StudyDescription = "CT scan"

        assert criterion.evaluate(dataset3) is False

    def test_complex_nested_with_not_operator(self):
        """Test complex nested expressions with NOT operator.

        Requirements: 4.3, 4.4
        """
        expression = (
            "not (PatientName.equals('Anonymous') "
            "or PatientName.equals('Unknown')) "
            "and (StudyDescription.contains('MRI')"
            " or StudyDescription.contains('CT'))"
        )
        criterion = Criterion(expression)

        # Test case 1: Valid patient name and has MRI
        dataset1 = Dataset()
        dataset1.PatientName = "John Doe"
        dataset1.StudyDescription = "Brain MRI scan"

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Valid patient name and has CT
        dataset2 = Dataset()
        dataset2.PatientName = "Jane Smith"
        dataset2.StudyDescription = "Chest CT with contrast"

        assert criterion.evaluate(dataset2) is True

        # Test case 3: Anonymous patient (should fail NOT condition)
        dataset3 = Dataset()
        dataset3.PatientName = "Anonymous"
        dataset3.StudyDescription = "Brain MRI scan"

        assert criterion.evaluate(dataset3) is False

        # Test case 4: Valid name but no MRI/CT
        dataset4 = Dataset()
        dataset4.PatientName = "John Doe"
        dataset4.StudyDescription = "X-ray examination"

        assert criterion.evaluate(dataset4) is False


class TestAllDicomFunctionCombinations:
    """Test combinations of all three DICOM functions (equals, contains, exists)."""

    def test_all_three_functions_with_and(self):
        """Test expression using all three functions with AND operator.

        Requirements: 4.1
        """
        expression = (
            "PatientName.equals('John Doe') and "
            "StudyDescription.contains('MRI') and PatientID.exists()"
        )
        criterion = Criterion(expression)

        # Test case 1: All conditions satisfied
        dataset1 = Dataset()
        dataset1.PatientName = "John Doe"
        dataset1.StudyDescription = "Brain MRI with contrast"
        dataset1.PatientID = "12345"

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Missing PatientID (exists fails)
        dataset2 = Dataset()
        dataset2.PatientName = "John Doe"
        dataset2.StudyDescription = "Brain MRI with contrast"
        # PatientID is missing

        assert criterion.evaluate(dataset2) is False

        # Test case 3: Wrong patient name (equals fails)
        dataset3 = Dataset()
        dataset3.PatientName = "Jane Smith"
        dataset3.StudyDescription = "Brain MRI with contrast"
        dataset3.PatientID = "12345"

        assert criterion.evaluate(dataset3) is False

        # Test case 4: No MRI in description (contains fails)
        dataset4 = Dataset()
        dataset4.PatientName = "John Doe"
        dataset4.StudyDescription = "CT scan of chest"
        dataset4.PatientID = "12345"

        assert criterion.evaluate(dataset4) is False

    def test_all_three_functions_with_or(self):
        """Test expression using all three functions with OR operator.

        Requirements: 4.2
        """
        expression = (
            "PatientName.equals('Emergency') or "
            "StudyDescription.contains('STAT') or PatientID.exists()"
        )
        criterion = Criterion(expression)

        # Test case 1: Only first condition satisfied
        dataset1 = Dataset()
        dataset1.PatientName = "Emergency"
        dataset1.StudyDescription = "Regular scan"
        # PatientID is missing

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Only second condition satisfied
        dataset2 = Dataset()
        dataset2.PatientName = "John Doe"
        dataset2.StudyDescription = "STAT Brain MRI"
        # PatientID is missing

        assert criterion.evaluate(dataset2) is True

        # Test case 3: Only third condition satisfied
        dataset3 = Dataset()
        dataset3.PatientName = "John Doe"
        dataset3.StudyDescription = "Regular scan"
        dataset3.PatientID = "12345"

        assert criterion.evaluate(dataset3) is True

        # Test case 4: All conditions satisfied
        dataset4 = Dataset()
        dataset4.PatientName = "Emergency"
        dataset4.StudyDescription = "STAT Brain MRI"
        dataset4.PatientID = "12345"

        assert criterion.evaluate(dataset4) is True

        # Test case 5: No conditions satisfied
        dataset5 = Dataset()
        dataset5.PatientName = "John Doe"
        dataset5.StudyDescription = "Regular scan"
        # PatientID is missing

        assert criterion.evaluate(dataset5) is False

    def test_mixed_functions_with_complex_logic(self):
        """Test complex expression mixing all three functions with various operators.

        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        expression = (
            "(PatientName.equals('John') and "
            "StudyDescription.contains('MRI')) or "
            "(not PatientID.exists() and StudyDate.equals('20240101'))"
        )
        criterion = Criterion(expression)

        # Test case 1: First complex condition satisfied
        dataset1 = Dataset()
        dataset1.PatientName = "John"
        dataset1.StudyDescription = "Brain MRI scan"
        dataset1.PatientID = "12345"
        dataset1.StudyDate = "20240102"

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Second complex condition satisfied (no
        # PatientID and correct date)
        dataset2 = Dataset()
        dataset2.PatientName = "Jane"
        dataset2.StudyDescription = "CT scan"
        # PatientID is missing (not exists() = True)
        dataset2.StudyDate = "20240101"

        assert criterion.evaluate(dataset2) is True

        # Test case 3: Both conditions satisfied
        dataset3 = Dataset()
        dataset3.PatientName = "John"
        dataset3.StudyDescription = "Spine MRI"
        # PatientID is missing
        dataset3.StudyDate = "20240101"

        assert criterion.evaluate(dataset3) is True

        # Test case 4: Neither condition satisfied
        dataset4 = Dataset()
        dataset4.PatientName = "Jane"  # Not John
        dataset4.StudyDescription = "CT scan"  # No MRI
        dataset4.PatientID = "12345"  # Exists (so not exists() = False)
        dataset4.StudyDate = "20240102"  # Wrong date

        assert criterion.evaluate(dataset4) is False

    def test_function_combinations_with_same_attribute(self):
        """Test multiple functions applied to the same DICOM attribute.

        Requirements: 4.1, 4.2
        """
        expression = (
            "PatientName.exists() and (PatientName.equals('John')"
            " or PatientName.contains('Doe'))"
        )
        criterion = Criterion(expression)

        # Test case 1: PatientName exists and equals 'John'
        dataset1 = Dataset()
        dataset1.PatientName = "John"

        assert criterion.evaluate(dataset1) is True

        # Test case 2: PatientName exists and contains 'Doe'
        dataset2 = Dataset()
        dataset2.PatientName = "Jane Doe"

        assert criterion.evaluate(dataset2) is True

        # Test case 3: PatientName exists but matches neither condition
        dataset3 = Dataset()
        dataset3.PatientName = "Bob Smith"

        assert criterion.evaluate(dataset3) is False

        # Test case 4: PatientName doesn't exist
        dataset4 = Dataset()
        dataset4.StudyDescription = "Some study"
        # PatientName is missing

        assert criterion.evaluate(dataset4) is False


class TestComprehensiveErrorHandling:
    """Test error handling across the entire evaluation chain."""

    def test_expression_parse_errors(self):
        """Test various expression parsing errors.

        Requirements: 3.4
        """
        # Test invalid boolean syntax
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("PatientName.equals('John') and and StudyID.exists()")
        assert "Failed to parse boolean expression" in str(exc_info.value)

        # Test mismatched parentheses
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("(PatientName.equals('John') and StudyID.exists()")
        assert "Failed to parse boolean expression" in str(exc_info.value)

        # Test empty expression
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("")
        assert "No valid DICOM symbols found" in str(exc_info.value)

        # Test expression with no valid DICOM symbols
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("true and false")
        assert "No valid DICOM symbols found" in str(exc_info.value)

    def test_symbol_parse_errors(self):
        """Test DICOM symbol parsing errors.

        Requirements: 3.4
        """
        # Test unregistered function
        with pytest.raises(SymbolParseError) as exc_info:
            Criterion("PatientName.unknown_function('test')")
        assert "Function 'unknown_function' is not registered" in str(exc_info.value)

        # Test invalid symbol format (missing parentheses)
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("PatientName.equals")
        assert "No valid DICOM symbols found" in str(exc_info.value)

        # Test invalid attribute name - this actually gets parsed as a valid symbol
        # but would fail during evaluation, so let's test a truly invalid format
        with pytest.raises(ExpressionParseError) as exc_info:
            Criterion("invalid_format_without_dot")
        assert "No valid DICOM symbols found" in str(exc_info.value)

    def test_evaluation_errors_with_invalid_datasets(self):
        """Test evaluation errors with invalid or problematic datasets.

        Requirements: 3.4
        """
        criterion = Criterion("PatientName.equals('John')")

        # Test with None dataset
        with pytest.raises(EvaluationError):
            criterion.evaluate(None)

        # Test with dataset that raises errors on attribute access
        class ProblematicDataset:
            def __getattr__(self, name):
                raise ValueError(f"Cannot access attribute {name}")

        with pytest.raises(EvaluationError):
            criterion.evaluate(ProblematicDataset())

    def test_error_propagation_in_complex_expressions(self):
        """Test that errors propagate correctly in complex expressions.

        Requirements: 3.4
        """
        # Create a complex expression
        expression = (
            "(PatientName.equals('John') and "
            "StudyDescription.contains('MRI')) or PatientID.exists()"
        )
        criterion = Criterion(expression)

        # Test error propagation with invalid dataset
        with pytest.raises(EvaluationError) as exc_info:
            criterion.evaluate(None)

        # Verify error message contains context about the expression
        assert "Failed to evaluate expression against dataset" in str(exc_info.value)

    def test_meaningful_error_messages(self):
        """Test that error messages are meaningful and helpful.

        Requirements: 3.4
        """
        # Test expression parse error message
        try:
            Criterion("PatientName.equals('John') and and StudyID.exists()")
        except ExpressionParseError as e:
            assert "Failed to parse boolean expression" in str(e)
            assert "PatientName.equals('John') and and StudyID.exists()" in str(e)

        # Test symbol parse error message
        try:
            Criterion("PatientName.unknown_function('test')")
        except SymbolParseError as e:
            assert "Function 'unknown_function' is not registered" in str(e)
            assert "PatientName.unknown_function" in str(e)

        # Test evaluation error message
        criterion = Criterion("PatientName.equals('John')")
        try:
            criterion.evaluate(None)
        except EvaluationError as e:
            assert "Failed to evaluate expression against dataset" in str(e)
            assert "PatientName.equals('John')" in str(e)


class TestRealWorldScenarios:
    """Test realistic DICOM validation scenarios."""

    def test_patient_privacy_validation(self):
        """Test validation for patient privacy requirements.

        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        # Ensure patient is not anonymous and has required identifiers
        expression = (
            "not (PatientName.equals('Anonymous') or "
            "PatientName.equals('') or PatientName.contains('UNKNOWN')) "
            "and PatientID.exists() and PatientBirthDate.exists()"
        )
        criterion = Criterion(expression)

        # Test case 1: Valid patient with all required info
        dataset1 = Dataset()
        dataset1.PatientName = "John Doe"
        dataset1.PatientID = "12345"
        dataset1.PatientBirthDate = "19800101"

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Anonymous patient (should fail)
        dataset2 = Dataset()
        dataset2.PatientName = "Anonymous"
        dataset2.PatientID = "12345"
        dataset2.PatientBirthDate = "19800101"

        assert criterion.evaluate(dataset2) is False

        # Test case 3: Missing PatientID (should fail)
        dataset3 = Dataset()
        dataset3.PatientName = "John Doe"
        dataset3.PatientBirthDate = "19800101"
        # PatientID is missing

        assert criterion.evaluate(dataset3) is False

    def test_study_quality_validation(self):
        """Test validation for study quality requirements.

        Requirements: 4.1, 4.2, 4.4
        """
        # Ensure study has proper description and is not a test/phantom study
        expression = (
            "StudyDescription.exists() and "
            "not (StudyDescription.contains('TEST') or "
            "StudyDescription.contains('PHANTOM') or "
            "StudyDescription.contains('QA')) and "
            "(StudyDescription.contains('MRI') or "
            "StudyDescription.contains('CT') or "
            "StudyDescription.contains('X-RAY'))"
        )
        criterion = Criterion(expression)

        # Test case 1: Valid MRI study
        dataset1 = Dataset()
        dataset1.StudyDescription = "Brain MRI with contrast"

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Valid CT study
        dataset2 = Dataset()
        dataset2.StudyDescription = "Chest CT without contrast"

        assert criterion.evaluate(dataset2) is True

        # Test case 3: Test study (should fail)
        dataset3 = Dataset()
        dataset3.StudyDescription = "TEST Brain MRI"

        assert criterion.evaluate(dataset3) is False

        # Test case 4: Phantom study (should fail)
        dataset4 = Dataset()
        dataset4.StudyDescription = "PHANTOM QA study"

        assert criterion.evaluate(dataset4) is False

        # Test case 5: Unsupported modality (should fail)
        dataset5 = Dataset()
        dataset5.StudyDescription = "Ultrasound examination"

        assert criterion.evaluate(dataset5) is False

    def test_emergency_study_validation(self):
        """Test validation for emergency study processing.

        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        # Emergency studies: either marked as STAT/EMERGENCY or patient
        # name indicates emergency
        expression = (
            "(StudyDescription.contains('STAT') or "
            "StudyDescription.contains('EMERGENCY') or "
            "PatientName.contains('EMERGENCY')) and not "
            "StudyDescription.contains('TEST')"
        )
        criterion = Criterion(expression)

        # Test case 1: STAT study
        dataset1 = Dataset()
        dataset1.StudyDescription = "STAT Brain CT"
        dataset1.PatientName = "John Doe"

        assert criterion.evaluate(dataset1) is True

        # Test case 2: Emergency patient
        dataset2 = Dataset()
        dataset2.StudyDescription = "Brain MRI"
        dataset2.PatientName = "EMERGENCY Patient"

        assert criterion.evaluate(dataset2) is True

        # Test case 3: Emergency study description
        dataset3 = Dataset()
        dataset3.StudyDescription = "EMERGENCY Chest X-ray"
        dataset3.PatientName = "Jane Smith"

        assert criterion.evaluate(dataset3) is True

        # Test case 4: Test emergency study (should fail due to TEST exclusion)
        dataset4 = Dataset()
        dataset4.StudyDescription = "STAT TEST Brain CT"
        dataset4.PatientName = "John Doe"

        assert criterion.evaluate(dataset4) is False

        # Test case 5: Regular study (should fail)
        dataset5 = Dataset()
        dataset5.StudyDescription = "Routine Brain MRI"
        dataset5.PatientName = "John Doe"

        assert criterion.evaluate(dataset5) is False


class TestUsageExamples:
    """Integration tests that serve as comprehensive usage examples.

    These tests demonstrate practical usage patterns and serve as
    executable documentation for the library's capabilities.
    """

    def test_basic_usage_examples(self):
        """Test basic usage patterns as executable examples.

        Requirements: 1.1, 2.1, 2.2, 2.3, 3.1, 3.2
        """
        # Create a sample dataset
        dataset = Dataset()
        dataset.PatientName = "John Doe"
        dataset.PatientID = "12345"
        dataset.StudyDescription = "Brain MRI with contrast"
        dataset.StudyDate = "20240101"

        # Example 1: Simple equality check
        criterion = Criterion("PatientName.equals('John Doe')")
        assert criterion.evaluate(dataset) is True

        # Example 2: Case-insensitive equality
        criterion = Criterion("PatientName.equals('john doe')")
        assert criterion.evaluate(dataset) is True

        # Example 3: Substring matching
        criterion = Criterion("StudyDescription.contains('MRI')")
        assert criterion.evaluate(dataset) is True

        # Example 4: Attribute existence check
        criterion = Criterion("PatientID.exists()")
        assert criterion.evaluate(dataset) is True

        # Example 5: Non-existing attribute
        criterion = Criterion("SeriesDescription.exists()")
        assert criterion.evaluate(dataset) is False

        # Example 6: Boolean combination with AND
        criterion = Criterion(
            "PatientName.equals('John Doe') and StudyDescription.contains('MRI')"
        )
        assert criterion.evaluate(dataset) is True

        # Example 7: Boolean combination with OR
        criterion = Criterion(
            "StudyDescription.contains('CT') or StudyDescription.contains('MRI')"
        )
        assert criterion.evaluate(dataset) is True

        # Example 8: NOT operator
        criterion = Criterion("not PatientName.equals('Anonymous')")
        assert criterion.evaluate(dataset) is True

    def test_medical_imaging_workflow_examples(self):
        """Test real-world medical imaging workflow scenarios.

        Requirements: 1.1, 2.1, 2.2, 2.3, 3.1, 3.2
        """
        # Create different types of medical datasets

        # Regular clinical study
        clinical_dataset = Dataset()
        clinical_dataset.PatientName = "John Smith"
        clinical_dataset.PatientID = "HOSP12345"
        clinical_dataset.PatientBirthDate = "19800101"
        clinical_dataset.StudyDescription = "Brain MRI without contrast"
        clinical_dataset.Modality = "MR"
        clinical_dataset.InstitutionName = "General Hospital"

        # Emergency study
        emergency_dataset = Dataset()
        emergency_dataset.PatientName = "EMERGENCY Patient"
        emergency_dataset.PatientID = "EMRG999"
        emergency_dataset.StudyDescription = "STAT Head CT - Trauma"
        emergency_dataset.Modality = "CT"

        # Test/QA study
        qa_dataset = Dataset()
        qa_dataset.PatientName = "PHANTOM Test"
        qa_dataset.PatientID = "QA001"
        qa_dataset.StudyDescription = "Daily QA TEST - Phantom"
        qa_dataset.Modality = "MR"

        # Example 1: Patient privacy validation
        privacy_rule = """
        not (PatientName.equals('Anonymous') or
             PatientName.equals('') or
             PatientName.contains('UNKNOWN')) and
        PatientID.exists() and
        PatientBirthDate.exists()
        """
        criterion = Criterion(privacy_rule)
        assert criterion.evaluate(clinical_dataset) is True  # Has all required info
        assert criterion.evaluate(emergency_dataset) is False  # Missing birth date

        # Example 2: Emergency study identification
        emergency_rule = """
        (StudyDescription.contains('STAT') or
         StudyDescription.contains('EMERGENCY') or
         PatientName.contains('EMERGENCY')) and
        not StudyDescription.contains('TEST')
        """
        criterion = Criterion(emergency_rule)
        assert criterion.evaluate(clinical_dataset) is False  # Not emergency
        assert criterion.evaluate(emergency_dataset) is True  # Is emergency
        assert criterion.evaluate(qa_dataset) is False  # Is test study

        # Example 3: Clinical study validation
        clinical_rule = """
        not (StudyDescription.contains('TEST') or
             StudyDescription.contains('PHANTOM') or
             StudyDescription.contains('QA')) and
        PatientName.exists() and
        PatientID.exists()
        """
        criterion = Criterion(clinical_rule)
        assert criterion.evaluate(clinical_dataset) is True  # Valid clinical study
        assert criterion.evaluate(emergency_dataset) is True  # Valid emergency study
        assert criterion.evaluate(qa_dataset) is False  # Is QA study

        # Example 4: Modality-specific validation
        mri_rule = "StudyDescription.contains('MRI') or Modality.equals('MR')"
        ct_rule = "StudyDescription.contains('CT') or Modality.equals('CT')"

        mri_criterion = Criterion(mri_rule)
        ct_criterion = Criterion(ct_rule)

        assert mri_criterion.evaluate(clinical_dataset) is True  # MRI study
        assert ct_criterion.evaluate(clinical_dataset) is False  # Not CT
        assert mri_criterion.evaluate(emergency_dataset) is False  # Not MRI
        assert ct_criterion.evaluate(emergency_dataset) is True  # CT study

    def test_data_quality_validation_examples(self):
        """Test data quality validation scenarios.

        Requirements: 1.1, 2.1, 2.2, 2.3, 3.1, 3.2
        """
        # Complete dataset with all required fields
        complete_dataset = Dataset()
        complete_dataset.PatientName = "Jane Doe"
        complete_dataset.PatientID = "HOSP67890"
        complete_dataset.PatientBirthDate = "19750615"
        complete_dataset.StudyDescription = "Chest CT with contrast"
        complete_dataset.StudyDate = "20240101"
        complete_dataset.StudyTime = "143000"
        complete_dataset.Modality = "CT"
        complete_dataset.InstitutionName = "Medical Center"

        # Incomplete dataset missing critical fields
        incomplete_dataset = Dataset()
        incomplete_dataset.StudyDescription = "Some study"
        incomplete_dataset.Modality = "MR"
        # Missing PatientName, PatientID, etc.

        # Anonymous dataset
        anonymous_dataset = Dataset()
        anonymous_dataset.PatientName = "Anonymous"
        anonymous_dataset.StudyDescription = "Research study"
        anonymous_dataset.Modality = "MR"

        # Example 1: Minimum required fields validation
        minimum_fields_rule = """
        PatientName.exists() and
        PatientID.exists() and
        StudyDescription.exists() and
        Modality.exists()
        """
        criterion = Criterion(minimum_fields_rule)
        assert criterion.evaluate(complete_dataset) is True
        assert criterion.evaluate(incomplete_dataset) is False
        assert criterion.evaluate(anonymous_dataset) is False

        # Example 2: Patient identification validation
        patient_id_rule = """
        PatientName.exists() and
        not PatientName.equals('Anonymous') and
        not PatientName.equals('') and
        PatientID.exists()
        """
        criterion = Criterion(patient_id_rule)
        assert criterion.evaluate(complete_dataset) is True
        assert criterion.evaluate(incomplete_dataset) is False
        assert criterion.evaluate(anonymous_dataset) is False

        # Example 3: Study completeness validation
        study_complete_rule = """
        StudyDescription.exists() and
        StudyDate.exists() and
        Modality.exists() and
        not StudyDescription.equals('')
        """
        criterion = Criterion(study_complete_rule)
        assert criterion.evaluate(complete_dataset) is True
        assert criterion.evaluate(incomplete_dataset) is False  # Missing StudyDate

        # Example 4: Institution validation
        institution_rule = (
            "InstitutionName.exists() and not " "InstitutionName.equals('')"
        )
        criterion = Criterion(institution_rule)
        assert criterion.evaluate(complete_dataset) is True
        assert criterion.evaluate(incomplete_dataset) is False

    def test_complex_filtering_examples(self):
        """Test complex filtering scenarios for DICOM datasets.

        Requirements: 1.1, 2.1, 2.2, 2.3, 3.1, 3.2, 4.1, 4.2, 4.3, 4.4
        """
        # Create various datasets for filtering examples
        datasets = []

        # Adult MRI study
        adult_mri = Dataset()
        adult_mri.PatientName = "Adult Patient"
        adult_mri.PatientAge = "045Y"
        adult_mri.StudyDescription = "Brain MRI without contrast"
        adult_mri.Modality = "MR"
        adult_mri.BodyPartExamined = "BRAIN"
        datasets.append(("Adult MRI", adult_mri))

        # Pediatric CT study
        pediatric_ct = Dataset()
        pediatric_ct.PatientName = "Child Patient"
        pediatric_ct.PatientAge = "012Y"
        pediatric_ct.StudyDescription = "Chest CT with contrast"
        pediatric_ct.Modality = "CT"
        pediatric_ct.BodyPartExamined = "CHEST"
        datasets.append(("Pediatric CT", pediatric_ct))

        # Cardiac MRI study
        cardiac_mri = Dataset()
        cardiac_mri.PatientName = "Cardiac Patient"
        cardiac_mri.PatientAge = "055Y"
        cardiac_mri.StudyDescription = "Cardiac MRI with gadolinium"
        cardiac_mri.Modality = "MR"
        cardiac_mri.BodyPartExamined = "HEART"
        datasets.append(("Cardiac MRI", cardiac_mri))

        # Example 1: Filter for MRI studies only
        mri_filter = "Modality.equals('MR')"
        criterion = Criterion(mri_filter)

        mri_results = [
            (name, criterion.evaluate(dataset)) for name, dataset in datasets
        ]
        expected_mri = [
            ("Adult MRI", True),
            ("Pediatric CT", False),
            ("Cardiac MRI", True),
        ]
        assert mri_results == expected_mri

        # Example 2: Filter for brain studies
        brain_filter = """
        StudyDescription.contains('Brain') or
        BodyPartExamined.equals('BRAIN')
        """
        criterion = Criterion(brain_filter)

        brain_results = [
            (name, criterion.evaluate(dataset)) for name, dataset in datasets
        ]
        expected_brain = [
            ("Adult MRI", True),
            ("Pediatric CT", False),
            ("Cardiac MRI", False),
        ]
        assert brain_results == expected_brain

        # Example 3: Filter for contrast studies
        contrast_filter = """
        StudyDescription.contains('with contrast') or
        StudyDescription.contains('gadolinium')
        """
        criterion = Criterion(contrast_filter)

        contrast_results = [
            (name, criterion.evaluate(dataset)) for name, dataset in datasets
        ]
        expected_contrast = [
            ("Adult MRI", False),
            ("Pediatric CT", True),
            ("Cardiac MRI", True),
        ]
        assert contrast_results == expected_contrast

        # Example 4: Complex multi-criteria filter
        complex_filter = """
        (Modality.equals('MR') and
         (StudyDescription.contains('Brain') or
          StudyDescription.contains('Cardiac'))) or
        (Modality.equals('CT') and PatientAge.contains('Y'))
        """
        criterion = Criterion(complex_filter)

        complex_results = [
            (name, criterion.evaluate(dataset)) for name, dataset in datasets
        ]
        expected_complex = [
            ("Adult MRI", True),
            ("Pediatric CT", True),
            ("Cardiac MRI", True),
        ]
        assert complex_results == expected_complex

    def test_error_handling_usage_examples(self):
        """Test error handling patterns as usage examples.

        Requirements: 3.4
        """
        dataset = Dataset()
        dataset.PatientName = "Test Patient"
        dataset.StudyDescription = "Test Study"

        # Example 1: Handling expression parse errors
        invalid_expressions = [
            "",  # Empty expression
            "PatientName.equals('John') and and StudyID.exists()",  # Invalid syntax
            "(PatientName.equals('John') and "
            "StudyID.exists()",  # Mismatched parentheses
        ]

        for expression in invalid_expressions:
            with pytest.raises(ExpressionParseError):
                Criterion(expression)

        # Example 2: Handling symbol parse errors
        invalid_symbols = [
            "PatientName.unknown_function('test')",  # Unknown function
            "invalid_format_without_dot",  # Invalid format
        ]

        for expression in invalid_symbols:
            with pytest.raises((SymbolParseError, ExpressionParseError)):
                Criterion(expression)

        # Example 3: Handling evaluation errors
        criterion = Criterion("PatientName.equals('Test')")

        # Test with None dataset
        with pytest.raises(EvaluationError):
            criterion.evaluate(None)

        # Example 4: Graceful handling of missing attributes
        criterion = Criterion("NonExistentAttribute.exists()")
        result = criterion.evaluate(dataset)
        assert result is False  # Should return False, not raise error

        # Example 5: Handling missing arguments
        with pytest.raises(EvaluationError):
            criterion = Criterion("PatientName.equals()")
            criterion.evaluate(dataset)

    def test_performance_usage_examples(self):
        """Test performance-oriented usage patterns.

        Requirements: 1.1, 3.1, 3.2
        """
        # Create multiple datasets for performance testing
        datasets = []
        for i in range(10):
            dataset = Dataset()
            dataset.PatientName = f"Patient {i}"
            dataset.PatientID = f"ID{i:03d}"
            dataset.StudyDescription = f"Study {i} - {'MRI' if i % 2 == 0 else 'CT'}"
            dataset.Modality = "MR" if i % 2 == 0 else "CT"
            datasets.append(dataset)

        # Example 1: Reusing compiled criterion for multiple evaluations
        criterion = Criterion(
            "PatientName.exists() and StudyDescription.contains('MRI')"
        )

        results = []
        for dataset in datasets:
            result = criterion.evaluate(dataset)
            results.append(result)

        # Should have True for even indices (MRI studies), False for odd (CT studies)
        expected = [True if i % 2 == 0 else False for i in range(10)]
        assert results == expected

        # Example 2: Complex expression reuse
        complex_criterion = Criterion(
            """
        (PatientName.exists() and PatientID.exists()) and
        (StudyDescription.exists() and Modality.exists()) and
        (StudyDescription.contains('MRI') or StudyDescription.contains('CT'))
        """
        )

        complex_results = [complex_criterion.evaluate(x) for x in datasets]
        # All should be True since all datasets have the required fields
        # and contain MRI or CT
        assert all(complex_results)

        # Example 3: Batch validation pattern
        validation_rules = {
            "has_patient_info": "PatientName.exists() and PatientID.exists()",
            "has_study_info": "StudyDescription.exists() and Modality.exists()",
            "is_mri": "StudyDescription.contains('MRI') or Modality.equals('MR')",
            "is_ct": "StudyDescription.contains('CT') or Modality.equals('CT')",
        }

        # Pre-compile all criteria
        compiled_criteria = {
            name: Criterion(rule) for name, rule in validation_rules.items()
        }

        # Batch evaluate
        batch_results = []
        for _i, dataset in enumerate(datasets):
            dataset_results = {}
            for rule_name, criterion in compiled_criteria.items():
                dataset_results[rule_name] = criterion.evaluate(dataset)
            batch_results.append(dataset_results)

        # Verify results
        for i, results in enumerate(batch_results):
            assert results["has_patient_info"] is True
            assert results["has_study_info"] is True
            assert results["is_mri"] == (i % 2 == 0)  # Even indices are MRI
            assert results["is_ct"] == (i % 2 == 1)  # Odd indices are CT
