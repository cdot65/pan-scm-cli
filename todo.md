# To-Do List: `pan-scm-cli` Authentication Enhancement

## Step 1: Set Up Project Environment
- [ ] Ensure the project repository is cloned locally (`git clone https://github.com/cdot65/pan-scm-cli.git`).
- [ ] Navigate to the project directory (`cd pan-scm-cli`).
- [ ] Install dependencies using Poetry (`poetry install`).
- [ ] Activate the virtual environment (`poetry shell`).
- [ ] Verify existing setup by running `scm-cli --help`.

## Step 2: Create Configuration Module
- [ ] Create a new file `src/scm_cli/config.py`.
- [ ] Import `dynaconf` and `pathlib.Path` in `config.py`.
- [ ] Initialize a Dynaconf instance with:
  - `envvar_prefix="SCM"`.
  - `settings_files=[Path.home() / ".scm-cli" / "config.yaml"]`.
- [ ] Define a `get_auth_config()` function that:
  - Retrieves `client_id`, `client_secret`, and `tsg_id` from Dynaconf.
  - Validates all fields are present and raises a `ValueError` with missing keys if not.
- [ ] Add a docstring to `get_auth_config()` explaining its purpose.

## Step 3: Create SCM Client Module
- [ ] Create a new file `src/scm_cli/client.py`.
- [ ] Import `StrataCloudManager` from `pan_scm_sdk` and `get_auth_config` from `.config`.
- [ ] Define a `get_scm_client(mock=False)` function that:
  - Returns a `MockSCMClient` instance if `mock` is `True`.
  - Calls `get_auth_config()` and initializes `StrataCloudManager` with the credentials if `mock` is `False`.
- [ ] Implement a `MockSCMClient` class that:
  - Uses `__getattr__` to return mock methods.
  - Returns a dict with `{"status": "success", "message": f"Mock {name} call"}` for any method call.
- [ ] Add docstrings to `get_scm_client()` and `MockSCMClient`.

## Step 4: Update Main CLI
- [ ] Open `src/scm_cli/main.py`.
- [ ] Import `get_scm_client` from `.client`.
- [ ] Add a new `test_auth` command using Typer:
  - Accept a `--mock` option (`bool`, default `False`).
  - Call `get_scm_client(mock=mock)` and store the result.
  - Output "Authentication successful" if `mock` is `True`, or "Client initialized: {client}" if `False`.
- [ ] Ensure the command is registered with the main `app` instance.
- [ ] Update the main docstring to mention the `test-auth` command as an example.

## Step 5: Update Command Modules
- [ ] For each command module (e.g., `src/scm_cli/commands/objects/set.py`):
  - Import `get_scm_client` from `...client`.
  - Replace any direct SCM client initialization with a call to `get_scm_client(mock=mock)`.
  - Pass the `--mock` option to the client where applicable (e.g., from command arguments).
- [ ] Verify all existing commands (e.g., `set objects address`) use the new client logic.

## Step 6: Add Tests
- [ ] Create a new test file `tests/test_config.py`.
- [ ] Write unit tests for `config.py`:
  - Test `get_auth_config()` with environment variables only (set `SCM_*` vars, no config file).
  - Test `get_auth_config()` with `config.yaml` only (unset env vars, create temp config file).
  - Test `get_auth_config()` with both (ensure env vars override config file).
  - Test error case when all credentials are missing.
- [ ] Write integration tests in `tests/test_config.py`:
  - Test `get_scm_client(mock=True)` returns a `MockSCMClient`.
  - Test `get_scm_client(mock=False)` with valid credentials (mock `StrataCloudManager` if needed).
- [ ] Update existing command tests to use `get_scm_client` with mock mode.

## Step 7: Update Documentation
- [ ] Open `README.md`.
- [ ] Replace the **Authentication** section with:
  - Explanation of prioritization (env vars over config file).
  - Updated examples for environment variables and `config.yaml`.
  - Security note for `chmod 600 ~/.scm-cli/config.yaml`.
  - Instructions for `scm-cli test-auth` and `scm-cli test-auth --mock`.
- [ ] Verify all example commands in the README still work with the new client logic.
- [ ] Update the GitHub Pages site (`docs/`) if necessary to reflect the new authentication details.

## Step 8: Validate Implementation
- [ ] Test with environment variables:
  - Set `SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, `SCM_TSG_ID` in the shell.
  - Run `scm-cli test-auth` and confirm success.
- [ ] Test with config file:
  - Unset environment variables.
  - Create `~/.scm-cli/config.yaml` with valid credentials.
  - Run `scm-cli test-auth` and confirm success.
- [ ] Test prioritization:
  - Set environment variables and create `config.yaml` with different values.
  - Run `scm-cli test-auth` and confirm env vars are used.
- [ ] Test mock mode:
  - Run `scm-cli test-auth --mock` and confirm mock output.

## Step 9: Finalize and Commit
- [ ] Run linting checks (`make lint`) and fix any issues.
- [ ] Run formatting (`make format`) to ensure consistency.
- [ ] Run tests (`make test`) and verify 100% coverage for new code.
- [ ] Run pre-commit hooks (`make pre-commit-all`) to catch any issues.
- [ ] Commit changes with a message like: "Add config.yaml authentication support with Dynaconf".
- [ ] Push changes to a feature branch (`git push origin feature/auth-config`).
- [ ] Open a Pull Request on GitHub with a description linking to this enhancement.
