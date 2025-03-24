# Courierica Testing Framework 🚀
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview 👀

Courierica Testing Framework is an API testing framework designed to automate testing for courier-related services. 
It supports end-to-end (E2E) testing, validation of API responses, and integration testing for various microservices.

This framework helps to:
* Ensure API stability and reliability
* Automate complex testing scenarios
* Save time and reduce costs by catching issues early
* Enable Continuous Integration (CI) and Continuous Deployment (CD)

## Project structure 🗂️

```
courierica_testing/
├── allure-report/                          # Allure test reports
├── allure-results/                         # Allure test results
├── data/                                   # Data models and constants
│   ├── company_dataclass.py                # Company data model
│   ├── delivery_dataclass.py               # Delivery data model
│   ├── endpoints.py                        # API endpoints
├── generator/                              # Data generators
│   ├── base_generator.py                   # Base data generator (uses Faker)
│   ├── company_generator.py                # Company data generator
│   ├── delivery_generator.py               # Delivery data generator
├── logs/                                   # Log storage
│   ├── logs.log                            # Main log file
├── services/                               # API service interactions
│   ├── auth_service.py                     # Authentication and token management
│   ├── delivery_service.py                 # Delivery operations
│   ├── courier_service.py                  # Courier operations
│   ├── company_service.py                  # Company management
│   ├── pickup_point_service.py             # Pickup points management
│   ├── route_service.py                    # Route planning
├── src/
│   ├── prepare_data/                       # Data preparation utilities
│   │   ├── prepare_basic_data.py           # General data preparation
│   │   ├── prepare_company_data.py         # Company data preparation
│   │   ├── prepare_delivery_data.py        # Delivery data preparation
│   ├── schemas/                            # API response validation schemas
│   │   ├── company_request_schema.py
│   │   ├── company_response_schema.py
│   │   ├── delivery_request_schema.py
│   │   ├── delivery_response_schema.py
│   ├── assertions.py                       # Assertion helpers
│   ├── http_methods.py                     # HTTP request utilities
│   ├── logger.py                           # Logging setup
│   ├── validator.py                        # Response validation
├── tests/                                  # Test suites
│   ├── e2e/                                # End-to-End tests
│   │   ├── config/
│   │   │   ├── geo_updates.json
│   │   │   ├── order_data.py
│   │   ├── test_delivery_courier_flow.py
│   ├── test_company/                       # Company API tests
│   │   ├── test_create_company.py
│   │   ├── test_update_company.py
│   │   ├── test_get_company.py
│   │   ├── test_get_companies.py
│   ├── test_delivery/                      # Delivery API tests
│   │   ├── test_create_delivery.py
├── .gitignore                              # Ignore files for Git
├── conftest.py                             # Pytest fixtures
├── functions.py                            # Helper functions
├── pytest.ini                              # Pytest configuration
├── requirements.txt                        # Dependencies
└── settings.py                             # Global settings
```

# Technologies Used ⭐

* `Python 3.x` – Main programming language
* `pytest` – Testing framework
* `httpx` – Asynchronous HTTP client for API calls
* `pydantic` – Data validation and serialization
* `allure-pytest` – Test reporting
* `python-dotenv` – Environment variable management
* `Faker` – Fake data generation

# Getting Started

## Installation 🐱‍💻

Clone the repository:
``` bash
git clone https://github.com/YuryHerasimau/courierica_testing.git
cd courierica_testing
```

Create and activate a virtual environment:
``` bash
python -m venv env
source env/bin/activate  # On Windows use: env\Scripts\activate
```

Install dependencies:
``` bash
pip install -r requirements.txt
```

## Running Tests 🧪

Run all tests:
``` bash
pytest -s -v --alluredir=allure-results
```

Run a specific test suite:
``` bash
pytest tests/test_company
```

Run a specific test:
``` bash
pytest -k test_multiple_deliveries_routing_flow
```

## Generate Allure Report 🧾

To generate the Allure report, you can use the following command:

```bash
allure generate allure-results -o allure-report --clean
```

After generating the report, you can view it by opening the index.html file in the [allure-report](allure-report) directory or by serving it with:

```bash
allure open allure-report
```

Alternatively, you can serve the report directly from the results directory using:

``` bash
allure serve allure-results
```

## CI/CD Integration 🌐

The framework is designed to run on CI/CD pipelines (e.g., GitHub Actions, GitLab CI, Jenkins):
* Automated test execution after each commit
* Allure reports for easy debugging
* Parallel test execution to speed up validation

Example GitHub Actions workflow:
``` yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: pytest --alluredir=allure-results
      - name: Upload Allure Report
        uses: actions/upload-artifact@v3
        with:
          name: allure-results
          path: allure-results
```

# Time ⏱️ & Cost Savings 💸

Automating tests with this framework results in:

* ✅ Faster bug detection – Immediate feedback on API changes
* ✅ Reduced manual testing effort – Save QA engineering hours
* ✅ Lower downtime costs – Catch critical errors before production
* ✅ Efficient debugging – Detailed logs and Allure reports simplify issue tracking

# Contact 📧

For questions or contributions, reach out to `yl.herasimau@gmail.com`.

