"""Setup module commands for scm.

This module implements set, show, delete, load, and backup commands for setup-related
configurations such as folders, labels, snippets, variables, and devices.
"""

from datetime import datetime
from pathlib import Path

import typer
import yaml
from pydantic import ValidationError

from ..utils import validate_location_params
from ..utils.bulk import run_bulk
from ..utils.config import load_from_yaml
from ..utils.decorators import handle_command_errors
from ..utils.output import OUTPUT_OPTION, OutputFormat, emit, error, info, success
from ..utils.sdk_client import scm_client
from ..utils.validators import Device, Folder, Label, Snippet, Variable

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update setup configurations")
delete_app = typer.Typer(help="Remove setup configurations")
load_app = typer.Typer(help="Load setup configurations from YAML files")
show_app = typer.Typer(help="Display setup configurations")
backup_app = typer.Typer(help="Backup setup configurations to YAML files")

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

# Common options
DESCRIPTION_OPTION = typer.Option(
    None,
    "--description",
    help="Description of the resource",
)
FILE_OPTION = typer.Option(
    ...,
    "--file",
    help="YAML file to load configurations from",
)
DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Simulate execution without applying changes",
)
BACKUP_FILE_OPTION = typer.Option(
    None,
    "--file",
    help="Output filename for backup (defaults to {object-type}_{timestamp}.yaml)",
)
MAX_RESULTS_OPTION = typer.Option(
    None,
    "--max-results",
    help="Maximum number of results to display",
)

# Folder-specific options
PARENT_OPTION = typer.Option(
    ...,
    "--parent",
    help="Parent folder name",
)
LABELS_OPTION = typer.Option(
    None,
    "--labels",
    help="Labels to apply to the resource",
)
SNIPPETS_OPTION = typer.Option(
    None,
    "--snippets",
    help="Snippet IDs to associate with the folder",
)

# Variable-specific options
FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Folder to scope the variable to",
)
SNIPPET_OPTION = typer.Option(
    None,
    "--snippet",
    help="Snippet to scope the variable to",
)
DEVICE_OPTION = typer.Option(
    None,
    "--device",
    help="Device to scope the variable to",
)
TYPE_OPTION = typer.Option(
    ...,
    "--type",
    help="Variable type (percent, count, ip-netmask, zone, ip-range, ip-wildcard, fqdn, port, egress-max, etc.)",
)
VALUE_OPTION = typer.Option(
    ...,
    "--value",
    help="Variable value",
)

# Snippet-specific options
ENABLE_PREFIX_OPTION = typer.Option(
    None,
    "--enable-prefix",
    help="Enable prefix for the snippet",
)


# =============================================================================================================================================================================================
# HELPER FUNCTIONS
# =============================================================================================================================================================================================


def get_default_backup_filename(object_type: str) -> str:
    """Generate the default backup filename.

    Args:
        object_type: Type of object (e.g., "folder", "label")

    Returns:
        str: Default filename

    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{object_type}_{timestamp}.yaml"


def get_child_folder_names(parent_name: str) -> list[str]:
    """Return direct child folder names for a parent folder."""
    folders = scm_client.list_folders()
    return sorted(f.get("name", "N/A") for f in folders if f.get("parent") == parent_name)


# =============================================================================================================================================================================================
# FOLDER COMMANDS
# =============================================================================================================================================================================================


@set_app.command("folder")
@handle_command_errors("creating folder")
def set_folder(
    name: str = typer.Argument(..., help="Name of the folder"),
    parent: str = PARENT_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    labels: list[str] | None = LABELS_OPTION,
    snippets: list[str] | None = SNIPPETS_OPTION,
):
    """Create or update a folder.

    Examples
    --------
        scm set setup folder Texas --parent "All"
        scm set setup folder Branch --parent Texas --description "Branch offices"

    """
    try:
        folder_model = Folder(
            name=name,
            parent=parent,
            description=description,
            labels=labels,
            snippets=snippets,
        )
    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e

    result = scm_client.create_folder(**folder_model.to_sdk_model())

    action = result.get("__action__", "created")
    if action == "no_change":
        info(f"No changes detected for folder: {name} (parent: {parent})")
    elif action == "updated":
        success(f"Updated folder: {name} (parent: {parent})")
    else:
        success(f"Created folder: {name} (parent: {parent})")
    return result


@show_app.command("folder")
@handle_command_errors("showing folders")
def show_folder(
    name: str | None = typer.Argument(None, help="Name of the folder to show; omit to list all"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = MAX_RESULTS_OPTION,
):
    """Display folders.

    Examples
    --------
        scm show setup folder
        scm show setup folder Texas

    """
    if name:
        folder = scm_client.get_folder(name=name)
        emit(folder, output, title=f"Folder: {name}")
        return

    folders = scm_client.list_folders()
    if max_results is not None:
        folders = folders[:max_results]
    emit(folders, output, columns=["name", "display_name", "parent", "description"], title="Folders")


@delete_app.command("folder")
@handle_command_errors("deleting folder")
def delete_folder(
    name: str = typer.Argument(..., help="Name of the folder"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a folder.

    Example: scm delete setup folder Branch
    """
    if not force:
        typer.confirm(f"Delete folder '{name}'?", abort=True)

    child_folders = get_child_folder_names(name)
    if child_folders:
        child_list = ", ".join(child_folders)
        error(f"Cannot delete folder '{name}' because it contains child folder(s): {child_list}. Delete or move the child folder(s) first.")
        raise typer.Exit(code=1)

    result = scm_client.delete_folder(name=name)

    if result:
        success(f"Deleted folder: {name}")
    else:
        error(f"Folder not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("folder")
@handle_command_errors("loading folders")
def load_folder(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load folders from a YAML file.

    Example: scm load setup folder --file folders.yaml
    """
    config = load_from_yaml(str(file), "folders")

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        typer.echo(yaml.dump(config["folders"]))
        return None

    # sequential: folder hierarchy — a child folder may reference a parent defined earlier in the same file
    results = []
    for folder_data in config["folders"]:
        try:
            folder_model = Folder(**folder_data)
        except ValidationError as e:
            error(f"Validation error: {e}")
            raise typer.Exit(code=1) from e
        sdk_data = folder_model.to_sdk_model()
        result = scm_client.create_folder(**sdk_data)
        results.append(result)

        action = result.get("__action__", "created")
        if action == "no_change":
            info(f"No changes for folder: {folder_model.name}")
        elif action == "updated":
            success(f"Updated folder: {folder_model.name}")
        else:
            success(f"Created folder: {folder_model.name}")

    success(f"Processed {len(results)} folders from {file}")
    return results


@backup_app.command("folder")
@handle_command_errors("backing up folders")
def backup_folder(
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all folders to a YAML file.

    Examples
    --------
        scm backup setup folder
        scm backup setup folder --file my-folders.yaml

    """
    if not file:
        file = get_default_backup_filename("folders")

    folders = scm_client.list_folders()

    if not folders:
        info("No folders found")
        return None

    backup_data = []
    for f in folders:
        f_dict = f.copy()
        f_dict.pop("id", None)
        backup_data.append(f_dict)

    yaml_data = {"folders": backup_data}

    with open(file, "w") as fh:
        yaml.dump(yaml_data, fh, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} folders to {file}")
    return file


# =============================================================================================================================================================================================
# LABEL COMMANDS
# =============================================================================================================================================================================================


@set_app.command("label")
@handle_command_errors("creating label")
def set_label(
    name: str = typer.Argument(..., help="Name of the label"),
    description: str | None = DESCRIPTION_OPTION,
):
    """Create or update a label.

    Examples
    --------
        scm set setup label production
        scm set setup label staging --description "Staging environment"

    """
    try:
        label_model = Label(
            name=name,
            description=description,
        )
    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e

    result = scm_client.create_label(**label_model.to_sdk_model())

    action = result.get("__action__", "created")
    if action == "no_change":
        info(f"No changes detected for label: {name}")
    elif action == "updated":
        success(f"Updated label: {name}")
    else:
        success(f"Created label: {name}")
    return result


@show_app.command("label")
@handle_command_errors("showing labels")
def show_label(
    name: str | None = typer.Argument(None, help="Name of the label to show; omit to list all"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = MAX_RESULTS_OPTION,
):
    """Display labels.

    Examples
    --------
        scm show setup label
        scm show setup label production

    """
    if name:
        label = scm_client.get_label(name=name)
        emit(label, output, title=f"Label: {name}")
        return

    labels = scm_client.list_labels()
    if max_results is not None:
        labels = labels[:max_results]
    emit(labels, output, columns=["name", "description"], title="Labels")


@delete_app.command("label")
@handle_command_errors("deleting label")
def delete_label(
    name: str = typer.Argument(..., help="Name of the label"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a label.

    Example: scm delete setup label staging
    """
    if not force:
        typer.confirm(f"Delete label '{name}'?", abort=True)
    result = scm_client.delete_label(name=name)

    if result:
        success(f"Deleted label: {name}")
    else:
        error(f"Label not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("label")
@handle_command_errors("loading labels")
def load_label(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load labels from a YAML file.

    Example: scm load setup label --file labels.yaml
    """
    config = load_from_yaml(str(file), "labels")

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        typer.echo(yaml.dump(config["labels"]))
        return None

    def _apply(label_data: dict):
        label_model = Label(**label_data)
        return label_model, scm_client.create_label(**label_model.to_sdk_model())

    # Apply each label concurrently, reporting outcomes in input order
    results = []
    for _label_data, outcome, exc in run_bulk(config["labels"], _apply):
        if isinstance(exc, ValidationError):
            error(f"Validation error: {exc}")
            raise typer.Exit(code=1) from exc
        if exc is not None:
            raise exc  # abort on first error, matching the previous sequential loop
        label_model, result = outcome
        results.append(result)

        action = result.get("__action__", "created")
        if action == "no_change":
            info(f"No changes for label: {label_model.name}")
        elif action == "updated":
            success(f"Updated label: {label_model.name}")
        else:
            success(f"Created label: {label_model.name}")

    success(f"Processed {len(results)} labels from {file}")
    return results


@backup_app.command("label")
@handle_command_errors("backing up labels")
def backup_label(
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all labels to a YAML file.

    Examples
    --------
        scm backup setup label
        scm backup setup label --file my-labels.yaml

    """
    if not file:
        file = get_default_backup_filename("labels")

    labels = scm_client.list_labels()

    if not labels:
        info("No labels found")
        return None

    backup_data = []
    for lbl in labels:
        lbl_dict = lbl.copy()
        lbl_dict.pop("id", None)
        backup_data.append(lbl_dict)

    yaml_data = {"labels": backup_data}

    with open(file, "w") as fh:
        yaml.dump(yaml_data, fh, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} labels to {file}")
    return file


# =============================================================================================================================================================================================
# SNIPPET COMMANDS
# =============================================================================================================================================================================================


@set_app.command("snippet")
@handle_command_errors("creating snippet")
def set_snippet(
    name: str = typer.Argument(..., help="Name of the snippet"),
    description: str | None = DESCRIPTION_OPTION,
    labels: list[str] | None = LABELS_OPTION,
    enable_prefix: bool | None = ENABLE_PREFIX_OPTION,
):
    """Create or update a snippet.

    Examples
    --------
        scm set setup snippet "DNS-Best-Practice"
        scm set setup snippet "Web-Security" --description "Web security config" --labels prod

    """
    try:
        snippet_model = Snippet(
            name=name,
            description=description,
            labels=labels,
            enable_prefix=enable_prefix,
        )
    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e

    result = scm_client.create_snippet(**snippet_model.to_sdk_model())

    action = result.get("__action__", "created")
    if action == "no_change":
        info(f"No changes detected for snippet: {name}")
    elif action == "updated":
        success(f"Updated snippet: {name}")
    else:
        success(f"Created snippet: {name}")
    return result


@show_app.command("snippet")
@handle_command_errors("showing snippets")
def show_snippet(
    name: str | None = typer.Argument(None, help="Name of the snippet to show; omit to list all"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = MAX_RESULTS_OPTION,
):
    """Display snippets.

    Examples
    --------
        scm show setup snippet
        scm show setup snippet "DNS-Best-Practice"

    """
    if name:
        snippet = scm_client.get_snippet(name=name)
        emit(snippet, output, title=f"Snippet: {name}")
        return

    snippets = scm_client.list_snippets()
    if max_results is not None:
        snippets = snippets[:max_results]
    emit(snippets, output, columns=["name", "type", "description"], title="Snippets")


@delete_app.command("snippet")
@handle_command_errors("deleting snippet")
def delete_snippet(
    name: str = typer.Argument(..., help="Name of the snippet"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a snippet.

    Example: scm delete setup snippet "DNS-Best-Practice"
    """
    if not force:
        typer.confirm(f"Delete snippet '{name}'?", abort=True)
    result = scm_client.delete_snippet(name=name)

    if result:
        success(f"Deleted snippet: {name}")
    else:
        error(f"Snippet not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("snippet")
@handle_command_errors("loading snippets")
def load_snippet(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load snippets from a YAML file.

    Example: scm load setup snippet --file snippets.yaml
    """
    config = load_from_yaml(str(file), "snippets")

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        typer.echo(yaml.dump(config["snippets"]))
        return None

    def _apply(snippet_data: dict):
        snippet_model = Snippet(**snippet_data)
        return snippet_model, scm_client.create_snippet(**snippet_model.to_sdk_model())

    # Apply each snippet concurrently, reporting outcomes in input order
    results = []
    for _snippet_data, outcome, exc in run_bulk(config["snippets"], _apply):
        if isinstance(exc, ValidationError):
            error(f"Validation error: {exc}")
            raise typer.Exit(code=1) from exc
        if exc is not None:
            raise exc  # abort on first error, matching the previous sequential loop
        snippet_model, result = outcome
        results.append(result)

        action = result.get("__action__", "created")
        if action == "no_change":
            info(f"No changes for snippet: {snippet_model.name}")
        elif action == "updated":
            success(f"Updated snippet: {snippet_model.name}")
        else:
            success(f"Created snippet: {snippet_model.name}")

    success(f"Processed {len(results)} snippets from {file}")
    return results


@backup_app.command("snippet")
@handle_command_errors("backing up snippets")
def backup_snippet(
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all snippets to a YAML file.

    Examples
    --------
        scm backup setup snippet
        scm backup setup snippet --file my-snippets.yaml

    """
    if not file:
        file = get_default_backup_filename("snippets")

    snippets = scm_client.list_snippets()

    if not snippets:
        info("No snippets found")
        return None

    backup_data = []
    for s in snippets:
        s_dict = s.copy()
        s_dict.pop("id", None)
        backup_data.append(s_dict)

    yaml_data = {"snippets": backup_data}

    with open(file, "w") as fh:
        yaml.dump(yaml_data, fh, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} snippets to {file}")
    return file


# =============================================================================================================================================================================================
# VARIABLE COMMANDS
# =============================================================================================================================================================================================


@set_app.command("variable")
@handle_command_errors("creating variable")
def set_variable(
    name: str = typer.Argument(..., help="Name of the variable"),
    type: str = TYPE_OPTION,
    value: str = VALUE_OPTION,
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    description: str | None = DESCRIPTION_OPTION,
):
    r"""Create or update a variable.

    Examples
    --------
        scm set setup variable "\$egress-max" --type egress-max --value 1000 --folder Texas
        scm set setup variable "\$dns-server" --type fqdn --value dns.example.com --snippet "DNS-Config"

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        variable_model = Variable(
            name=name,
            type=type,
            value=value,
            folder=folder,
            snippet=snippet,
            device=device,
            description=description,
        )
    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e

    result = scm_client.create_variable(**variable_model.to_sdk_model())

    action = result.get("__action__", "created")
    if action == "no_change":
        info(f"No changes detected for variable: {name} in {location_type} {location_value}")
    elif action == "updated":
        success(f"Updated variable: {name} in {location_type} {location_value}")
    else:
        success(f"Created variable: {name} in {location_type} {location_value}")
    return result


@show_app.command("variable")
@handle_command_errors("showing variables")
def show_variable(
    name: str | None = typer.Argument(None, help="Name of the variable to show; omit to list all"),
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = MAX_RESULTS_OPTION,
):
    r"""Display variables.

    Examples
    --------
        scm show setup variable --folder Texas
        scm show setup variable "\$egress-max" --folder Texas

    """
    _, location_value = validate_location_params(folder, snippet, device)

    if name:
        variable = scm_client.get_variable(name=name, folder=folder, snippet=snippet, device=device)
        emit(variable, output, title=f"Variable: {name}")
        return

    variables = scm_client.list_variables(folder=folder, snippet=snippet, device=device)
    if max_results is not None:
        variables = variables[:max_results]
    emit(variables, output, columns=["name", "type", "value", "description"], title=f"Variables in {location_value}")


@delete_app.command("variable")
@handle_command_errors("deleting variable")
def delete_variable(
    name: str = typer.Argument(..., help="Name of the variable"),
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    r"""Delete a variable.

    Example: scm delete setup variable "\$egress-max" --folder Texas
    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    if not force:
        typer.confirm(f"Delete variable '{name}' from {location_type} '{location_value}'?", abort=True)
    result = scm_client.delete_variable(name=name, folder=folder, snippet=snippet, device=device)

    if result:
        success(f"Deleted variable: {name} from {location_type} {location_value}")
    else:
        error(f"Variable not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("variable")
@handle_command_errors("loading variables")
def load_variable(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load variables from a YAML file.

    Example: scm load setup variable --file variables.yaml
    """
    config = load_from_yaml(str(file), "variables")

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        typer.echo(yaml.dump(config["variables"]))
        return None

    def _apply(var_data: dict):
        variable_model = Variable(**var_data)
        return variable_model, scm_client.create_variable(**variable_model.to_sdk_model())

    # Apply each variable concurrently, reporting outcomes in input order
    results = []
    for _var_data, outcome, exc in run_bulk(config["variables"], _apply):
        if isinstance(exc, ValidationError):
            error(f"Validation error: {exc}")
            raise typer.Exit(code=1) from exc
        if exc is not None:
            raise exc  # abort on first error, matching the previous sequential loop
        variable_model, result = outcome
        results.append(result)

        action = result.get("__action__", "created")
        if action == "no_change":
            info(f"No changes for variable: {variable_model.name}")
        elif action == "updated":
            success(f"Updated variable: {variable_model.name}")
        else:
            success(f"Created variable: {variable_model.name}")

    success(f"Processed {len(results)} variables from {file}")
    return results


@backup_app.command("variable")
@handle_command_errors("backing up variables")
def backup_variable(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
):
    """Backup variables to a YAML file.

    Examples
    --------
        scm backup setup variable --folder Texas
        scm backup setup variable --snippet "DNS-Config" --file my-variables.yaml

    """
    if not file:
        file = get_default_backup_filename("variables")

    variables = scm_client.list_variables(folder=folder, snippet=snippet, device=device)

    if not variables:
        info("No variables found")
        return None

    backup_data = []
    for v in variables:
        v_dict = v.copy()
        v_dict.pop("id", None)
        backup_data.append(v_dict)

    yaml_data = {"variables": backup_data}

    with open(file, "w") as fh:
        yaml.dump(yaml_data, fh, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} variables to {file}")
    return file


# =============================================================================================================================================================================================
# DEVICE COMMANDS
# =============================================================================================================================================================================================

DISPLAY_NAME_OPTION = typer.Option(
    None,
    "--display-name",
    help="Display name for the device",
)
DEVICE_FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Folder to move the device into",
)


@show_app.command("device")
@handle_command_errors("showing devices")
def show_device(
    name: str | None = typer.Argument(None, help="Name or serial number of the device to show; omit to list all"),
    folder: str | None = typer.Option(None, "--folder", help="Filter devices by folder"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = MAX_RESULTS_OPTION,
):
    """Display devices.

    Examples
    --------
        scm show setup device
        scm show setup device "PA-VM-01"
        scm show setup device --folder Texas

    """
    if name:
        device = scm_client.get_device(name=name)
        emit(device, output, title=f"Device: {device.get('name', device.get('hostname', name))}")
        return

    devices = scm_client.list_devices(folder=folder)
    if max_results is not None:
        devices = devices[:max_results]
    title = f"Devices in {folder}" if folder else "Devices"
    emit(devices, output, columns=["name", "serial_number", "model", "folder", "labels", "is_connected"], title=title)


@set_app.command("device")
@handle_command_errors("updating device")
def set_device(
    name: str = typer.Argument(..., help="Name or serial number of the device"),
    display_name: str | None = DISPLAY_NAME_OPTION,
    folder: str | None = DEVICE_FOLDER_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    labels: list[str] | None = LABELS_OPTION,
    snippets: list[str] | None = SNIPPETS_OPTION,
):
    """Update a device's writable fields (device must already exist).

    Devices cannot be created or deleted via the CLI — they are registered by
    the firewall itself. Use this command to update display_name, folder,
    description, labels, and/or snippets on an existing device.

    Examples
    --------
        scm set setup device PA-VM-01 --labels production --labels west
        scm set setup device 0123456789 --folder Austin
        scm set setup device PA-VM-01 --description "Edge firewall"

    """
    try:
        device_model = Device(
            name=name,
            display_name=display_name,
            folder=folder,
            description=description,
            labels=labels,
            snippets=snippets,
        )
    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e

    result = scm_client.update_device(**device_model.to_sdk_model())

    action = result.get("__action__", "updated")
    if action == "no_change":
        info(f"No changes detected for device: {name}")
    else:
        success(f"Updated device: {name}")
    return result


@load_app.command("device")
@handle_command_errors("loading devices")
def load_device(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load device updates from a YAML file.

    Devices must already exist — loading will error on any unknown device
    rather than creating one. Read-only fields in the YAML (serial_number,
    model, hostname, is_connected, etc.) are silently ignored.

    Example: scm load setup device --file devices.yaml
    """
    config = load_from_yaml(str(file), "devices")

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        typer.echo(yaml.dump(config["devices"]))
        return None

    def _apply(device_data: dict):
        device_model = Device(**device_data)
        return device_model, scm_client.update_device(**device_model.to_sdk_model())

    # Apply each device concurrently, reporting outcomes in input order
    results = []
    for _device_data, outcome, exc in run_bulk(config["devices"], _apply):
        if isinstance(exc, ValidationError):
            error(f"Validation error: {exc}")
            raise typer.Exit(code=1) from exc
        if exc is not None:
            raise exc  # abort on first error, matching the previous sequential loop
        device_model, result = outcome
        results.append(result)

        action = result.get("__action__", "updated")
        if action == "no_change":
            info(f"No changes for device: {device_model.name}")
        else:
            success(f"Updated device: {device_model.name}")

    success(f"Processed {len(results)} devices from {file}")
    return results


@backup_app.command("device")
@handle_command_errors("backing up devices")
def backup_device(
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all devices to a YAML file.

    Includes read-only fields (serial_number, model, hostname, etc.) for
    reference. Those fields are ignored on `scm load setup device`.

    Examples
    --------
        scm backup setup device
        scm backup setup device --file my-devices.yaml

    """
    if not file:
        file = get_default_backup_filename("devices")

    devices = scm_client.list_devices()

    if not devices:
        info("No devices found")
        return None

    backup_data = []
    for d in devices:
        d_dict = d.copy()
        d_dict.pop("id", None)
        backup_data.append(d_dict)

    yaml_data = {"devices": backup_data}

    with open(file, "w") as fh:
        yaml.dump(yaml_data, fh, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} devices to {file}")
    return file
