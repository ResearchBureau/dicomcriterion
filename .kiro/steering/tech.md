# Technology Stack

## Build System & Package Management
- **Package Manager**: uv (modern Python package manager)
- **Build System**: pyproject.toml (PEP 518 compliant)
- **Python Version**: Requires Python >=3.13

## Code Quality & Linting
- **Formatter**: Black (line length: 79 characters)
- **Linter**: Flake8 with extensions:
  - flake8-bugbear (B checks)
  - pep8-naming (N checks) 
  - flake8-docstrings (D checks)
  - mccabe complexity (max complexity: 10)
- **Type Checker**: MyPy with strict configuration
- **Pre-commit**: Automated code quality checks

## Testing
- **Framework**: pytest
- **Configuration**: No pytest doctest (using sybil instead)

## Common Commands
```bash
# Install dependencies
uv sync

# Run tests
pytest

# Type checking
mypy dicomcriterion

# Linting
flake8 dicomcriterion

# Format code
black dicomcriterion

# Run pre-commit hooks
pre-commit run --all-files
```

## Code Style Guidelines
- Line length: 79 characters (Black + Flake8)
- Docstring convention: NumPy style
- Import order: PyCharm style
- Strict type checking enabled