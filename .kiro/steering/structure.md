# Project Structure

## Root Directory Layout
```
dicom-criterion/
├── .git/                    # Git version control
├── .idea/                   # IDE configuration
├── .kiro/                   # Kiro AI assistant configuration
├── .venv/                   # Virtual environment (if using venv)
├── dicom_criterion/         # Main package source code
├── tests/                   # Test suite
├── .gitignore              # Git ignore patterns
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── README.md               # Project documentation
├── pyproject.toml          # Project configuration and dependencies
├── setup.cfg               # Tool configurations (mypy, pytest, flake8)
└── uv.lock                 # Dependency lock file
```

## Package Organization
- **dicom_criterion/**: Main package containing all source code
- **tests/**: Test files mirroring the package structure
- Configuration files are kept at project root following Python conventions

## File Naming Conventions
- Python modules: snake_case
- Package names: lowercase with underscores
- Test files: test_*.py or *_test.py

## Import Structure
- Application imports: `dicom_criterion`, `tests`
- Import order follows PyCharm style (configured in setup.cfg)
- Absolute imports preferred over relative imports