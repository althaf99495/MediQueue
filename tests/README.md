# MediQueue Test Suite

Comprehensive test suite covering all testing types for the MediQueue hospital queue management system.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit Tests
│   ├── test_models.py       # Model unit tests
│   ├── test_queue_service.py # QueueService unit tests
│   ├── test_auth_routes.py  # Authentication route tests
│   ├── test_patient_routes.py # Patient route tests
│   ├── test_doctor_routes.py  # Doctor route tests
│   └── test_admin_routes.py   # Admin route tests
├── integration/             # Integration Tests
│   ├── test_top_down.py    # Top-down integration
│   ├── test_bottom_up.py    # Bottom-up integration
│   ├── test_sandwich.py     # Sandwich (hybrid) integration
│   └── test_big_bang.py     # Big bang integration
├── validation/              # Validation Tests
│   ├── test_alpha.py       # Alpha testing (internal)
│   └── test_beta.py        # Beta testing (user acceptance)
├── system/                  # System Tests
│   ├── test_performance.py # Performance tests
│   ├── test_usability.py   # Usability tests
│   ├── test_reliability.py # Reliability tests
│   └── test_security.py    # Security tests
└── regression/             # Regression Tests
    └── test_regression.py  # Regression test suite
```

## Test Types

### 1. Unit Testing
Tests individual modules or components in isolation.
- **Location**: `tests/unit/`
- **Coverage**: Models, Services, Route handlers
- **Run**: `pytest tests/unit`

### 2. Integration Testing
Tests combined modules to ensure they work together.
- **Location**: `tests/integration/`
- **Approaches**:
  - **Top-down**: `test_top_down.py` - Tests from routes down to models
  - **Bottom-up**: `test_bottom_up.py` - Tests from models up to routes
  - **Sandwich**: `test_sandwich.py` - Tests middle layers with mocked top/bottom
  - **Big Bang**: `test_big_bang.py` - Tests entire system integration
- **Run**: `pytest tests/integration`

### 3. Validation Testing
Ensures software meets customer requirements.
- **Location**: `tests/validation/`
- **Types**:
  - **Alpha Testing**: `test_alpha.py` - Internal testing of requirements
  - **Beta Testing**: `test_beta.py` - User acceptance testing
- **Run**: `pytest tests/validation`

### 4. System Testing
Entire integrated system is tested.
- **Location**: `tests/system/`
- **Coverage**:
  - **Performance**: `test_performance.py` - Response times, load handling
  - **Usability**: `test_usability.py` - UI, navigation, user experience
  - **Reliability**: `test_reliability.py` - Stability, error handling
  - **Security**: `test_security.py` - Authentication, authorization, security
- **Run**: `pytest tests/system`

### 5. Regression Testing
Ensures that changes do not affect existing functionality.
- **Location**: `tests/regression/`
- **Coverage**: All existing features and workflows
- **Run**: `pytest tests/regression`

## Running Tests

### Run All Tests
```bash
pytest tests
```

### Run Specific Test Type
```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# Validation tests
pytest tests/validation

# System tests
pytest tests/system

# Regression tests
pytest tests/regression
```

### Run Specific Test File
```bash
pytest tests/unit/test_models.py
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Specific Test
```bash
pytest tests/unit/test_models.py::TestUserModel::test_user_creation
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:
- `test_app`: Flask test application
- `client`: Test client
- `admin_user`: Test admin user
- `doctor_user`: Test doctor user
- `patient_user`: Test patient user
- `department`: Test department
- `queue_service_instance`: QueueService instance
- `authenticated_admin`: Authenticated admin client
- `authenticated_doctor`: Authenticated doctor client
- `authenticated_patient`: Authenticated patient client

## Test Coverage

The test suite aims for comprehensive coverage:
- **Unit Tests**: Individual components and methods
- **Integration Tests**: Component interactions
- **Validation Tests**: Requirements and business logic
- **System Tests**: End-to-end system behavior
- **Regression Tests**: Existing functionality preservation

## Continuous Integration

These tests can be integrated into CI/CD pipelines:
```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    pytest tests --cov=. --cov-report=xml
```

## Notes

- All tests use an in-memory SQLite database for isolation
- Tests are designed to be independent and can run in any order
- Fixtures ensure clean state between tests
- Mock objects are used where appropriate for isolation

