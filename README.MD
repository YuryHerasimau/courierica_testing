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

### Project architecture

```mermaid
graph TD
    A[DeliveryGenerator/IikoDeliveryGenerator] -->|Generates DeliveryDataClass/IikoDeliveryDataClass| B[PrepareDeliveryData/PrepareIikoDeliveryData]
    B -->|Generates JSON| C[MyRequests]
    C -->|Sends request| D{API}
    D -->|SAAS API| E[SAAS Endpoints: Delivery/ Courier/ PickupPoint/ Company etc]
    D -->|External API| F[IIKO Endpoints: create_order/ check_status/ update_order_status]
    D -->|Returns response| G[Validator]
    G -->|Validates via GetDeliverySchemas| H[Allure Report]
    
    subgraph Data Layer
    A
    style A fill:#f9f,stroke:#333
    end
    
    subgraph Preparation Layer
    B
    style B fill:#bbf,stroke:#333
    end
    
    subgraph Client Layer
    C
    style C fill:#9f9,stroke:#333
    end
    
    subgraph API Targets
    E
    F
    style E fill:#f96,stroke:#333
    style F fill:#f96,stroke:#333
    end
    
    subgraph Validation Layer
    G
    style G fill:#ff9,stroke:#333
    end
```

### System components

| Component  | Project Path | Purpose |
| ------------- | ------------- | ------------- |
| DeliveryGenerator | generator/delivery_generator.py | Generating data for SAAS orders |
| IikoDeliveryGenerator | generator/iiko_delivery_generator.py | Generating data for IIKO orders |
| PrepareDeliveryData | src/prepare_data/prepare_delivery_data.py, src/prepare_data/prepare_iiko_delivery_data.py | Preparing data for API |
| MyRequests | src/http_methods.py | Custom HTTP client (httpx wrapper) |
| Validator | src/validator.py | Validating responses with Pydantic |
| conftest.py | courierica_testing/conftest.py | Global pytest fixtures, setting up the environment |
| settings.py | courierica_testing/settings.py | Project configurations, environment variables |
| .env | courierica_testing/.env | Personal environment variables (not under git) |

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

# Time ⏱️ & Cost Savings 💸

Automating tests with this framework results in:

* ✅ Faster bug detection – Immediate feedback on API changes
* ✅ Reduced manual testing effort – Save QA engineering hours
* ✅ Lower downtime costs – Catch critical errors before production
* ✅ Efficient debugging – Detailed logs and Allure reports simplify issue tracking

# Contact 📧

For questions or contributions, please <a href="mailto:yl.herasimau@gmail.com">contact us</a>.

