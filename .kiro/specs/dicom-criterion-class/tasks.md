# Implementation Plan

- [x] 1. Set up project dependencies and core structure
  - Add boolean.py and pydicom dependencies to pyproject.toml
  - Create main package __init__.py file
  - Set up basic project structure for the Criterion class
  - _Requirements: 1.1, 1.4_

- [x] 2. Implement exception hierarchy and error handling
  - Create custom exception classes for different error types
  - Implement clear error messages for parse and evaluation failures
  - Write unit tests for exception handling
  - _Requirements: 1.4, 3.4_

- [x] 3. Create DICOM function interface and concrete implementations
- [x] 3.1 Implement abstract DicomFunction base class
  - Define the interface for DICOM validation functions
  - Create abstract evaluate method signature
  - Write unit tests for the interface
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 3.2 Implement EqualsFunction class
  - Create equals function that compares DICOM attribute values
  - Handle type conversion and comparison logic
  - Write comprehensive unit tests with various data types
  - _Requirements: 2.1_

- [x] 3.3 Implement ContainsFunction class
  - Create contains function for substring matching in DICOM attributes
  - Handle string conversion and case sensitivity
  - Write unit tests for string matching scenarios
  - _Requirements: 2.2_

- [x] 3.4 Implement ExistsFunction class
  - Create exists function to check DICOM attribute presence
  - Handle missing attributes gracefully
  - Write unit tests for presence/absence scenarios
  - _Requirements: 2.3_

- [x] 4. Create function registry system
  - Implement FunctionRegistry class for managing available functions
  - Register the three core functions (equals, contains, exists)
  - Write unit tests for function registration and retrieval
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 5. Implement DICOM symbol parsing
- [x] 5.1 Create DicomSymbol data class
  - Define structure for parsed DICOM attribute expressions
  - Implement parsing logic for Python function call syntax (attribute.function(argument))
  - Write unit tests for symbol parsing with various formats
  - _Requirements: 1.1, 2.4_

- [x] 5.2 Implement symbol-to-boolean conversion
  - Create method to convert DicomSymbol to boolean.py Symbol
  - Handle symbol evaluation against DICOM datasets using function registry
  - Write unit tests for symbol conversion and evaluation
  - _Requirements: 3.1, 3.2_

- [x] 6. Implement core Criterion class functionality
- [x] 6.1 Complete Criterion class constructor
  - Parse string expressions using boolean.py
  - Extract and validate DICOM symbols from expressions
  - Store parsed boolean expression tree
  - Write unit tests for constructor with valid/invalid expressions
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 3.1_

- [x] 6.2 Complete evaluate method implementation
  - Evaluate boolean expressions against pydicom Dataset objects
  - Handle symbol resolution and function execution
  - Return boolean results based on expression evaluation
  - Write unit tests for evaluation with various datasets
  - _Requirements: 3.2, 3.3_

- [x] 7. Create comprehensive integration tests
  - Test complex boolean expressions with multiple operators (and, or, not)
  - Test nested expressions with parentheses and precedence
  - Test combinations of all three DICOM functions
  - Verify error handling across the entire evaluation chain
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 8. Add example usage and documentation
  - Create example scripts demonstrating Criterion usage
  - Add comprehensive docstrings to all public methods and classes
  - Write integration tests that serve as usage examples
  - _Requirements: 1.1, 2.1, 2.2, 2.3, 3.1, 3.2_