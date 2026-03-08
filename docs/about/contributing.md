# Contributing

Contributions to `pan-scm-cli` are welcome and appreciated. Whether you are fixing a bug, adding a feature, improving documentation, or providing suggestions, every contribution is valuable.

## Getting Started

Before you begin, make sure you have a GitHub account and are familiar with Git and GitHub workflows. If you are new to these tools, check out [GitHub's Help pages](https://help.github.com).

### Setting Up Your Environment

#### Fork and Clone

```bash
$ git clone https://github.com/YOUR_USERNAME/pan-scm-cli.git
$ cd pan-scm-cli
```

#### Install Dependencies

The project uses [Poetry](https://python-poetry.org/) for dependency management:

```bash
poetry install
```

#### Create a Branch

Create a branch for your changes:

```bash
git checkout -b your-feature-branch
```

## Contributing Guidelines

### Code Style

The project follows [PEP 8](https://www.python.org/dev/peps/pep-0008/) standards for Python code. Refer to the style guides in the `.claude/` directory for project-specific conventions:

- `.claude/STYLE_GUIDE.md` for command modules and general standards
- `.claude/SDK_CLIENT_STYLE_GUIDE.md` for SDK client patterns
- `.claude/VALIDATORS_STYLE_GUIDE.md` for validator patterns

### Pull Request Process

1. **Update Your Fork**: Sync your fork with the upstream repository before making changes.

    ```bash
    git remote add upstream https://github.com/cdot65/pan-scm-cli.git
    git fetch upstream
    git checkout main
    git merge upstream/main
    ```

2. **Make Your Changes**: Create your feature branch and make changes. Ensure your code passes all tests and linting checks.

3. **Commit Your Changes**: Use a clear and descriptive commit message.

    ```bash
    git commit -m "Add feature: your feature description"
    ```

4. **Push to Your Fork**: Push your changes to your fork on GitHub.

    ```bash
    git push origin your-feature-branch
    ```

5. **Create a Pull Request**: Go to the [pan-scm-cli repository](https://github.com/cdot65/pan-scm-cli) and create a new pull request from your feature branch.

6. **Address Review Feedback**: Respond to any feedback and make necessary changes.

### Running Tests

The project uses `pytest` for testing:

```bash
poetry run pytest
```

Run a specific test:

```bash
poetry run pytest tests/test_specific.py::test_name
```

### Running Quality Checks

Run all quality checks before submitting a pull request:

```bash
make quality
```

This runs linting, formatting, type checking, and tests.

### Documentation

If you are adding or modifying functionality, update the documentation to reflect the changes. The project uses [MkDocs](https://www.mkdocs.org/) with the [Material theme](https://squidfunk.github.io/mkdocs-material/).

Preview documentation changes locally:

```bash
poetry run mkdocs serve
```

!!! tip
    Follow the documentation style guide in `.claude/skills/docs-style/SKILL.md`
    when writing or modifying documentation pages.

## Adding New Commands

When adding new CLI commands:

1. **Follow existing patterns** in the appropriate command module under `src/scm_cli/commands/`
2. **Add Pydantic validators** in `utils/validators.py` if needed
3. **Register the command** in `main.py`
4. **Include helpful error messages** and proper input validation
5. **Add tests** in `tests/`
6. **Document the command** with examples in `docs/cli/`

## Bug Reports and Feature Requests

If you find a bug or have a feature request, create an issue on the [GitHub repository](https://github.com/cdot65/pan-scm-cli/issues) using the provided templates.

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code.
