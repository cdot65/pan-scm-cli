# Contributing to `pan-scm-cli`

We're thrilled that you're interested in contributing to the `pan-scm-cli` project! Your contributions are essential for
making this project better and more effective. Whether you're fixing a bug, adding a new command, improving the
documentation, or just giving suggestions, every contribution is valuable.

---

## Getting Started

Before you begin, make sure you have a GitHub account and are familiar with Git and GitHub workflows. If you're new to
these tools, you might want to check out some tutorials on [GitHub's Help pages](https://help.github.com).

### Setting Up Your Environment

1. **Fork the Repository**: Start by forking the [pan-scm-cli repository](https://github.com/cdot65/pan-scm-cli) to your
   GitHub account.

2. **Clone Your Fork**: Clone your fork to your local machine.
   ```bash
   git clone https://github.com/YOUR_USERNAME/pan-scm-cli.git
   cd pan-scm-cli
   ```

3. **Set Up Poetry Environment**: We use [Poetry](https://python-poetry.org/) for dependency management. If you don't have it installed, follow the instructions on the Poetry website.
   ```bash
   poetry install
   ```

4. **Create a Branch**: Create a branch for your changes.
   ```bash
   git checkout -b your-feature-branch
   ```

## Contributing Guidelines

### Code Style

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) standards for Python code. Please ensure your code adheres to these standards.

### Pull Request Process

1. **Update Your Fork**: Before making changes, sync your fork with the upstream repository.
   ```bash
   git remote add upstream https://github.com/cdot65/pan-scm-cli.git
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Make Your Changes**: Create your feature branch and make your changes. Ensure that your code passes all tests and linting checks.

3. **Commit Your Changes**: Commit your changes with a clear and descriptive commit message.
   ```bash
   git commit -m "Add feature: your feature description"
   ```

4. **Push to Your Fork**: Push your changes to your fork on GitHub.
   ```bash
   git push origin your-feature-branch
   ```

5. **Create a Pull Request**: Go to the [pan-scm-cli repository](https://github.com/cdot65/pan-scm-cli) and create a new pull request from your feature branch.

6. **Address Review Feedback**: Respond to any feedback from the review process and make necessary changes.

### Testing

Please include appropriate tests for your changes. We use `pytest` for testing.

```bash
poetry run pytest
```

### Documentation

If you're adding or modifying functionality, please update the documentation to reflect these changes. We use [MkDocs](https://www.mkdocs.org/) with the [Material theme](https://squidfunk.github.io/mkdocs-material/) for our documentation.

You can preview your documentation changes locally by running:

```bash
poetry run mkdocs serve
```

## Adding New Commands

When adding new CLI commands:

1. Follow the existing command structure patterns
2. Ensure proper input validation
3. Include helpful error messages
4. Document the command with examples
5. Add tests for the new command

## Bug Reports and Feature Requests

If you find a bug or have a feature request, please create an issue on the [GitHub repository](https://github.com/cdot65/pan-scm-cli/issues) using the provided templates.

## Code of Conduct

Please note that this project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

Thank you for contributing to `pan-scm-cli`! Your efforts help make this tool better for everyone.
