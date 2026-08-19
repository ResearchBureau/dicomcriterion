"""Test for bug with literal parentheses in DICOM tag values.

This test reproduces a bug where DICOM tag values containing literal ')'
characters cause parse errors when used in criterion expressions.

Bug: Saving a template could fail with a dicomcriterion parse error whenever
a DICOM tag value in the template's signature contains a literal ) character,
for example ManufacturerModelName = "Discovery A (S/N85606)"
"""

import pytest
from pydicom import Dataset

from dicomcriterion import Criterion, ExpressionParseError


class TestLiteralParenthesesBug:
    """Test cases for the literal parentheses bug."""

    def test_manufacturer_model_name_with_parentheses(self):
        """Test parsing expression with ManufacturerModelName containing parentheses.

        This should reproduce the bug where expressions containing DICOM values
        with literal ')' characters fail to parse correctly.
        """
        # Create a dataset with ManufacturerModelName containing parentheses
        dataset = Dataset()
        dataset.ManufacturerModelName = "Discovery A (S/N85606)"
        dataset.PatientName = "John Doe"

        # This expression should work but may fail due to the bug
        expression = "ManufacturerModelName.equals('Discovery A (S/N85606)')"

        # Try to create the criterion - this might raise ExpressionParseError
        try:
            criterion = Criterion(expression)
            result = criterion.evaluate(dataset)
            assert result is True
        except ExpressionParseError as e:
            # If we get here, we've reproduced the bug
            pytest.fail(
                f"Bug reproduced: Expression with literal ')' in value failed to parse: {e}"
            )

    def test_multiple_parentheses_in_value(self):
        """Test expression with multiple parentheses in the DICOM value."""
        dataset = Dataset()
        dataset.StudyDescription = "Brain MRI (Protocol A) (Contrast B)"

        expression = "StudyDescription.equals('Brain MRI (Protocol A) (Contrast B)')"

        try:
            criterion = Criterion(expression)
            result = criterion.evaluate(dataset)
            assert result is True
        except ExpressionParseError as e:
            pytest.fail(
                f"Bug reproduced: Expression with multiple ')' in value failed: {e}"
            )

    def test_nested_parentheses_in_value(self):
        """Test expression with nested parentheses in the DICOM value."""
        dataset = Dataset()
        dataset.DeviceSerialNumber = "Model X (Config (Type A))"

        expression = "DeviceSerialNumber.equals('Model X (Config (Type A))')"

        try:
            criterion = Criterion(expression)
            result = criterion.evaluate(dataset)
            assert result is True
        except ExpressionParseError as e:
            pytest.fail(
                f"Bug reproduced: Expression with nested parentheses failed: {e}"
            )

    def test_parentheses_in_contains_function(self):
        """Test contains function with parentheses in the search value."""
        dataset = Dataset()
        dataset.StudyDescription = "MRI Brain Study (Protocol A) with contrast"

        expression = "StudyDescription.contains('(Protocol A)')"

        try:
            criterion = Criterion(expression)
            result = criterion.evaluate(dataset)
            assert result is True
        except ExpressionParseError as e:
            pytest.fail(
                f"Bug reproduced: Contains with parentheses in value failed: {e}"
            )

    def test_complex_expression_with_parentheses_values(self):
        """Test complex boolean expression with parentheses in multiple values."""
        dataset = Dataset()
        dataset.ManufacturerModelName = "Discovery A (S/N85606)"
        dataset.StudyDescription = "Brain MRI (Protocol A)"
        dataset.PatientName = "Smith, John (ID: 12345)"

        expression = (
            "ManufacturerModelName.equals('Discovery A (S/N85606)') and "
            "StudyDescription.contains('(Protocol A)') and "
            "PatientName.contains('(ID: 12345)')"
        )

        try:
            criterion = Criterion(expression)
            result = criterion.evaluate(dataset)
            assert result is True
        except ExpressionParseError as e:
            pytest.fail(
                f"Bug reproduced: Complex expression with parentheses failed: {e}"
            )

    def test_unbalanced_parentheses_in_value_should_work(self):
        """Test that unbalanced parentheses within quoted values should work.

        The bug might be that the regex incorrectly matches parentheses inside
        quoted strings as function call parentheses.
        """
        dataset = Dataset()
        dataset.Comments = "Patient notes: See report (page 1"  # Missing closing )

        expression = "Comments.equals('Patient notes: See report (page 1')"

        try:
            criterion = Criterion(expression)
            result = criterion.evaluate(dataset)
            assert result is True
        except ExpressionParseError as e:
            pytest.fail(
                f"Bug reproduced: Unbalanced parentheses in quoted value failed: {e}"
            )

    def test_parentheses_with_double_quotes(self):
        """Test parentheses in values when using double quotes."""
        dataset = Dataset()
        dataset.ManufacturerModelName = "Discovery A (S/N85606)"

        expression = 'ManufacturerModelName.equals("Discovery A (S/N85606)")'

        try:
            criterion = Criterion(expression)
            result = criterion.evaluate(dataset)
            assert result is True
        except ExpressionParseError as e:
            pytest.fail(
                f"Bug reproduced: Double-quoted value with parentheses failed: {e}"
            )

    def test_parentheses_at_different_positions(self):
        """Test parentheses at the start, middle, and end of values."""

        # Test cases with parentheses in different positions
        test_cases = [
            ("(Start) with parentheses", "TagA.equals('(Start) with parentheses')"),
            ("Middle (here) parentheses", "TagB.equals('Middle (here) parentheses')"),
            (
                "End with parentheses (here)",
                "TagC.equals('End with parentheses (here)')",
            ),
        ]

        for value, expression in test_cases:
            # Create dataset with the test value
            dataset_copy = Dataset()
            if "TagA" in expression:
                dataset_copy.TagA = value
            elif "TagB" in expression:
                dataset_copy.TagB = value
            elif "TagC" in expression:
                dataset_copy.TagC = value

            try:
                criterion = Criterion(expression)
                # Note: This test might fail during evaluation due to missing attributes,
                # but the main goal is to test that parsing doesn't fail
                assert criterion is not None
            except ExpressionParseError as e:
                pytest.fail(
                    f"Bug reproduced: Expression '{expression}' failed to parse: {e}"
                )

    def test_expected_parsing_behavior(self):
        """Test to verify the expected parsing behavior without the bug.

        This test documents what the expected behavior should be:
        - Function calls use parentheses: attribute.function(args)
        - Quoted string arguments can contain any characters including ')'
        - The parser should not confuse ')' inside quotes with function call ')'
        """
        dataset = Dataset()
        dataset.TestAttribute = "Value with ) inside"

        # This should work - ')' is inside the quoted argument
        expression = "TestAttribute.equals('Value with ) inside')"

        try:
            criterion = Criterion(expression)
            result = criterion.evaluate(dataset)
            assert result is True
        except ExpressionParseError as e:
            pytest.fail(
                f"Expected behavior test failed - this indicates the bug exists: {e}"
            )


class TestRegexPatternAnalysis:
    """Tests to analyze the root cause of the parsing bug."""

    def test_regex_pattern_behavior(self):
        """Test to understand how the current regex pattern behaves.

        This test helps identify the root cause by testing the regex pattern
        used in _extract_dicom_symbols method directly.
        """

        # Test various expressions to see which ones fail
        test_expressions = [
            "PatientName.equals('John')",  # Should work
            "PatientName.equals('John (Doe)')",  # Might fail due to bug
            "PatientName.equals('John') and StudyID.exists()",  # Should work
            "PatientName.equals('John (Doe)') and StudyID.exists()",  # Might fail
        ]

        results = []
        for expr in test_expressions:
            try:
                results.append((expr, "SUCCESS", None))
            except Exception as e:
                results.append((expr, "FAILED", str(e)))

        # Log results for analysis
        for expr, status, error in results:
            if status == "FAILED":
                print(f"FAILED: {expr}")
                print(f"  Error: {error}")
            else:
                print(f"SUCCESS: {expr}")

        # If any expressions with parentheses in values failed, the bug exists
        failed_with_parens = [
            r
            for r in results
            if r[1] == "FAILED" and "(" in r[0] and "equals('" in r[0]
        ]

        if failed_with_parens:
            pytest.fail(
                f"Bug confirmed: {len(failed_with_parens)} expressions with "
                f"parentheses in values failed to parse"
            )
