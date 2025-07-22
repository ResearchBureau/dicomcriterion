# Requirements Document

## Introduction

This feature involves renaming the main package from `dicom_criterion` to `dicomcriterion` to eliminate underscores from importable names. This refactoring will improve the package's import ergonomics by using a single word without separators, making it more consistent with Python naming conventions for packages that are frequently imported.

## Requirements

### Requirement 1

**User Story:** As a developer using the DICOM Criterion library, I want to import the package using a clean name without underscores, so that my import statements are more readable and follow Python naming best practices.

#### Acceptance Criteria

1. WHEN importing the package THEN the import statement SHALL use `import dicomcriterion` instead of `import dicom_criterion`
2. WHEN accessing package components THEN they SHALL be available as `dicomcriterion.Criterion` instead of `dicom_criterion.Criterion`
3. WHEN the package is installed THEN it SHALL be installable and importable as `dicomcriterion`

### Requirement 2

**User Story:** As a developer maintaining the codebase, I want all internal imports and references to use the new package name, so that the codebase is consistent and functional after the rename.

#### Acceptance Criteria

1. WHEN examining the source code THEN all internal imports SHALL use the new `dicomcriterion` package name
2. WHEN running tests THEN all test imports SHALL reference `dicomcriterion` instead of `dicom_criterion`
3. WHEN checking example files THEN all example imports SHALL use the new package name
4. WHEN reviewing documentation THEN all code examples SHALL show the new import syntax

### Requirement 3

**User Story:** As a user of the library, I want all existing functionality to remain unchanged after the package rename, so that my code continues to work with only import statement changes.

#### Acceptance Criteria

1. WHEN using the Criterion class THEN it SHALL function identically to before the rename
2. WHEN using built-in functions (equals, contains, exists) THEN they SHALL work exactly as before
3. WHEN running existing test suites THEN all tests SHALL pass with the new package name
4. WHEN using custom function registries THEN they SHALL continue to work without modification

### Requirement 4

**User Story:** As a developer working with the project configuration, I want all build and configuration files to reflect the new package name, so that the project builds and installs correctly.

#### Acceptance Criteria

1. WHEN examining pyproject.toml THEN the package name SHALL be updated to `dicomcriterion`
2. WHEN checking setup.cfg THEN any package references SHALL use the new name
3. WHEN reviewing directory structure THEN the main package directory SHALL be named `dicomcriterion`
4. WHEN building the package THEN it SHALL create a distribution with the correct new name

### Requirement 5

**User Story:** As a developer reading project documentation, I want all documentation to reflect the new package name, so that I can follow current and accurate examples.

#### Acceptance Criteria

1. WHEN reading README.md THEN all code examples SHALL show `import dicomcriterion`
2. WHEN examining example files THEN they SHALL demonstrate the new import syntax
3. WHEN reviewing docstrings THEN they SHALL reference the correct package name where applicable
4. WHEN checking comments THEN they SHALL use the updated package name in relevant contexts