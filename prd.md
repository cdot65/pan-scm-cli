# Product Requirements Document (PRD): pan-scm-cli

## 1. Overview

### 1.1 Purpose
The pan-scm-cli is a command-line interface (CLI) tool designed to provision and manage configurations for Palo Alto Networks Strata Cloud Manager (SCM) using a network CLI-inspired syntax. It aims to streamline SCM configuration management within CI/CD pipelines while providing an intuitive interface for network engineers familiar with network CLI conventions.

### 1.2 Goals
- Enable programmatic configuration of SCM via set, delete, and load commands.
- Support YAML file-based configuration loading for CI/CD automation.
- Maintain high code quality standards through automated linting, formatting, and testing.
- Follow Python best practices with proper packaging, type hinting, and comprehensive documentation.
- Ensure security through pre-commit checks and scanning for secrets and vulnerabilities.

## 2. Technical Specifications

### 2.1 Architecture
- **Python Package**: Organized with a src/ layout following modern Python packaging practices.
- **Command Structure**: Uses Typer to create a hierarchical CLI command structure with subcommands.
- **Model Validation**: Leverages Pydantic for data validation and serialization.
- **SDK Interface**: Interacts with the pan-scm-sdk for communication with Strata Cloud Manager.

### 2.2 Code Quality Standards
- **Linting**: Enforced through Flake8 with a maximum line length of 128 characters.
- **Formatting**: Automatic code formatting using Ruff.
- **Security**: Security scanning with Checkov and Gitleaks for secret detection.
- **Testing**: Comprehensive test coverage using pytest with coverage reporting.
- **CI/CD**: GitHub Actions workflow for automated testing and code quality checks.
- **Pre-commit**: Enforced pre-commit hooks to maintain code quality standards.

### 2.3 Dependencies
- **Required Packages**: typer, pyyaml, pydantic, pan-scm-sdk
- **Development Dependencies**: pytest, pytest-cov, ruff, flake8, checkov, yamllint, pre-commit

## 3. Command Structure

### 3.1 Primary Commands
- `set`: Create or update configuration objects
- `delete`: Remove configuration objects
- `load`: Import configurations from YAML files

### 3.2 Resource Types
- **Deployment**: Bandwidth allocations
- **Network**: Zones, interfaces
- **Objects**: Address groups
- **Security**: Security rules

## 4. Implementation Details

### 4.1 Command Format
```
scm-cli <set|delete|load> <resource-type> <resource-name> [--parameters]
```

### 4.2 YAML Format
Structured hierarchical configuration that can be parsed and applied to SCM.

## 5. Development Guidelines

### 5.1 Coding Standards
- PEP 8 compliance (with 128-character line length)
- Type hints for all functions and classes
- Docstrings for all modules, classes, and functions
- Exception handling with proper error chaining
- Validation of all input parameters

### 5.2 Testing Requirements
- Unit tests for all components
- Integration tests for command workflows
- 80%+ code coverage target

## 6. Versioning and Release Strategy
- Semantic versioning (MAJOR.MINOR.PATCH)
- Release notes for each version
- Change log maintained in GitHub releases

## 7. User Stories
- As a Network Engineer, I want to use set and delete commands to configure SCM interactively, so I can manage settings like network-cli.
- As a DevOps Engineer, I want to use load with YAML files in a CI/CD pipeline, so I can automate SCM provisioning.
- As a User, I want clear error messages and dry-run options, so I can test changes safely.

## 8. Success Metrics
- 90% of SCM configurations manageable via CLI within 3 months.
- CI/CD pipeline integration completed with zero errors in dry-run mode.
- Positive feedback from at least 5 network engineers on usability.

## 9. Risks and Mitigation
- Risk: pan-scm-sdk limitations (e.g., no atomic operations).
  - Mitigation: Document limitations and plan for manual rollback.
- Risk: YAML parsing errors in CI/CD.
  - Mitigation: Robust validation with pydantic and detailed error messages.

## 10. Timeline
- Week 1-2: Prototype set, delete, and load for deployment module.
- Week 3-4: Expand to remaining modules and test CI/CD integration.
- Week 5: Finalize documentation and release v0.1.0.

## 11. Appendix
- Example YAML: See examples/bandwidth-example.yml.
- Pipeline Example: See CI/CD section.

This PRD provides a comprehensive blueprint for pan-scm-cli, emphasizing the load command for YAML-based CI/CD workflows while maintaining network-cli-inspired usability. Let me know if you need adjustments or additional sections!
