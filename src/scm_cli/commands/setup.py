"""Setup module commands for scm.

This module implements set, show, delete, load, and backup commands for setup-related
configurations such as folders, labels, snippets, variables, and devices.
"""

from datetime import datetime
from pathlib import Path

import typer
import yaml
from pydantic import ValidationError

from ..utils.config import load_from_yaml
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
NAME_OPTION = typer.Option(
    ...,
    "--name",
    help="Name of the resource",
)
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


def validate_container_params(folder: str | None = None, snippet: str | None = None, device: str | None = None) -> tuple[str, str]:
    """Validate that exactly one container parameter is provided.

    Returns:
        tuple: (container_type, container_value)

    """
    container_count = sum(1 for c in [folder, snippet, device] if c is not None)

    if container_count == 0:
        typer.echo("Error: One of --folder, --snippet, or --device must be specified", err=True)
        raise typer.Exit(code=1)
    elif container_count > 1:
        typer.echo("Error: Only one of --folder, --snippet, or --device can be specified", err=True)
        raise typer.Exit(code=1)

    if folder:
        return "folder", folder
    elif snippet:
        return "snippet", snippet
    else:
        assert device is not None
        return "device", device


def get_child_folder_names(parent_name: str) -> list[str]:
    """Return direct child folder names for a parent folder."""
    folders = scm_client.list_folders()
    return sorted(f.get("name", "N/A") for f in folders if f.get("parent") == parent_name)


# =============================================================================================================================================================================================
# FOLDER COMMANDS
# =============================================================================================================================================================================================


@set_app.command("folder")
def set_folder(
    name: str = NAME_OPTION,
    parent: str = PARENT_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    labels: list[str] | None = LABELS_OPTION,
    snippets: list[str] | None = SNIPPETS_OPTION,
):
    """Create or update a folder.

    Examples
    --------
        scm set setup folder --name Texas --parent "All"
        scm set setup folder --name Branch --parent Texas --description "Branch offices"

    """
    try:
        folder_model = Folder(
            name=name,
            parent=parent,
            description=description,
            labels=labels,
            snippets=snippets,
        )

        result = scm_client.create_folder(**folder_model.to_sdk_model())

        action = result.get("__action__", "created")
        if action == "no_change":
            typer.echo(f"No changes detected for folder: {name} (parent: {parent})")
        elif action == "updated":
            typer.echo(f"Updated folder: {name} (parent: {parent})")
        else:
            typer.echo(f"Created folder: {name} (parent: {parent})")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating folder: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("folder")
def show_folder(
    name: str | None = typer.Option(None, "--name", help="Name of the folder to show"),
):
    """Display folders.

    Examples
    --------
        scm show setup folder
        scm show setup folder --name Texas

    """
    try:
        if name:
            folder = scm_client.get_folder(name=name)

            typer.echo(f"\nFolder: {folder.get('name', 'N/A')}")
            typer.echo("=" * 80)
            typer.echo(f"Parent: {folder.get('parent', 'N/A')}")
            if folder.get("description"):
                typer.echo(f"Description: {folder['description']}")
            if folder.get("labels"):
                typer.echo(f"Labels: {', '.join(folder['labels'])}")
            if folder.get("snippets"):
                typer.echo(f"Snippets: {', '.join(folder['snippets'])}")
            if folder.get("id"):
                typer.echo(f"ID: {folder['id']}")
        else:
            folders = scm_client.list_folders()

            if not folders:
                typer.echo("No folders found")
                return

            typer.echo(f"\nFolders ({len(folders)}):")
            typer.echo("-" * 80)
            for f in folders:
                typer.echo(f"Name: {f.get('name', 'N/A')}")
                if f.get("display_name"):
                    typer.echo(f"  Display Name: {f['display_name']}")
                typer.echo(f"  Parent: {f.get('parent', 'N/A')}")
                if f.get("description"):
                    typer.echo(f"  Description: {f['description']}")
                typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error showing folders: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("folder")
def delete_folder(
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a folder.

    Example: scm delete setup folder --name Branch
    """
    try:
        if not force:
            typer.confirm(f"Delete folder '{name}'?", abort=True)

        child_folders = get_child_folder_names(name)
        if child_folders:
            child_list = ", ".join(child_folders)
            typer.echo(
                f"Cannot delete folder '{name}' because it contains child folder(s): {child_list}. Delete or move the child folder(s) first.",
                err=True,
            )
            raise typer.Exit(code=1)

        result = scm_client.delete_folder(name=name)

        if result:
            typer.echo(f"Deleted folder: {name}")
        else:
            typer.echo(f"Folder not found: {name}", err=True)
            raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error deleting folder: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("folder")
def load_folder(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load folders from a YAML file.

    Example: scm load setup folder --file folders.yaml
    """
    try:
        config = load_from_yaml(str(file), "folders")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["folders"]))
            return None

        results = []
        for folder_data in config["folders"]:
            folder_model = Folder(**folder_data)
            sdk_data = folder_model.to_sdk_model()
            result = scm_client.create_folder(**sdk_data)
            results.append(result)

            action = result.get("__action__", "created")
            if action == "no_change":
                typer.echo(f"No changes for folder: {folder_model.name}")
            elif action == "updated":
                typer.echo(f"Updated folder: {folder_model.name}")
            else:
                typer.echo(f"Created folder: {folder_model.name}")

        typer.echo(f"\nProcessed {len(results)} folders from {file}")
        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading folders: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("folder")
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

    try:
        folders = scm_client.list_folders()

        if not folders:
            typer.echo("No folders found")
            return None

        backup_data = []
        for f in folders:
            f_dict = f.copy()
            f_dict.pop("id", None)
            backup_data.append(f_dict)

        yaml_data = {"folders": backup_data}

        with open(file, "w") as fh:
            yaml.dump(yaml_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} folders to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up folders: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# LABEL COMMANDS
# =============================================================================================================================================================================================


@set_app.command("label")
def set_label(
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
):
    """Create or update a label.

    Examples
    --------
        scm set setup label --name production
        scm set setup label --name staging --description "Staging environment"

    """
    try:
        label_model = Label(
            name=name,
            description=description,
        )

        result = scm_client.create_label(**label_model.to_sdk_model())

        action = result.get("__action__", "created")
        if action == "no_change":
            typer.echo(f"No changes detected for label: {name}")
        elif action == "updated":
            typer.echo(f"Updated label: {name}")
        else:
            typer.echo(f"Created label: {name}")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating label: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("label")
def show_label(
    name: str | None = typer.Option(None, "--name", help="Name of the label to show"),
):
    """Display labels.

    Examples
    --------
        scm show setup label
        scm show setup label --name production

    """
    try:
        if name:
            label = scm_client.get_label(name=name)

            typer.echo(f"\nLabel: {label.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if label.get("description"):
                typer.echo(f"Description: {label['description']}")
            if label.get("id"):
                typer.echo(f"ID: {label['id']}")
        else:
            labels = scm_client.list_labels()

            if not labels:
                typer.echo("No labels found")
                return

            typer.echo(f"\nLabels ({len(labels)}):")
            typer.echo("-" * 80)
            for lbl in labels:
                typer.echo(f"Name: {lbl.get('name', 'N/A')}")
                if lbl.get("description"):
                    typer.echo(f"  Description: {lbl['description']}")
                typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error showing labels: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("label")
def delete_label(
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a label.

    Example: scm delete setup label --name staging
    """
    try:
        if not force:
            typer.confirm(f"Delete label '{name}'?", abort=True)
        result = scm_client.delete_label(name=name)

        if result:
            typer.echo(f"Deleted label: {name}")
        else:
            typer.echo(f"Label not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting label: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("label")
def load_label(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load labels from a YAML file.

    Example: scm load setup label --file labels.yaml
    """
    try:
        config = load_from_yaml(str(file), "labels")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["labels"]))
            return None

        results = []
        for label_data in config["labels"]:
            label_model = Label(**label_data)
            sdk_data = label_model.to_sdk_model()
            result = scm_client.create_label(**sdk_data)
            results.append(result)

            action = result.get("__action__", "created")
            if action == "no_change":
                typer.echo(f"No changes for label: {label_model.name}")
            elif action == "updated":
                typer.echo(f"Updated label: {label_model.name}")
            else:
                typer.echo(f"Created label: {label_model.name}")

        typer.echo(f"\nProcessed {len(results)} labels from {file}")
        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading labels: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("label")
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

    try:
        labels = scm_client.list_labels()

        if not labels:
            typer.echo("No labels found")
            return None

        backup_data = []
        for lbl in labels:
            lbl_dict = lbl.copy()
            lbl_dict.pop("id", None)
            backup_data.append(lbl_dict)

        yaml_data = {"labels": backup_data}

        with open(file, "w") as fh:
            yaml.dump(yaml_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} labels to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up labels: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# SNIPPET COMMANDS
# =============================================================================================================================================================================================


@set_app.command("snippet")
def set_snippet(
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    labels: list[str] | None = LABELS_OPTION,
    enable_prefix: bool | None = ENABLE_PREFIX_OPTION,
):
    """Create or update a snippet.

    Examples
    --------
        scm set setup snippet --name "DNS-Best-Practice"
        scm set setup snippet --name "Web-Security" --description "Web security config" --labels prod

    """
    try:
        snippet_model = Snippet(
            name=name,
            description=description,
            labels=labels,
            enable_prefix=enable_prefix,
        )

        result = scm_client.create_snippet(**snippet_model.to_sdk_model())

        action = result.get("__action__", "created")
        if action == "no_change":
            typer.echo(f"No changes detected for snippet: {name}")
        elif action == "updated":
            typer.echo(f"Updated snippet: {name}")
        else:
            typer.echo(f"Created snippet: {name}")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating snippet: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("snippet")
def show_snippet(
    name: str | None = typer.Option(None, "--name", help="Name of the snippet to show"),
):
    """Display snippets.

    Examples
    --------
        scm show setup snippet
        scm show setup snippet --name "DNS-Best-Practice"

    """
    try:
        if name:
            snippet = scm_client.get_snippet(name=name)

            typer.echo(f"\nSnippet: {snippet.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if snippet.get("description"):
                typer.echo(f"Description: {snippet['description']}")
            if snippet.get("type"):
                typer.echo(f"Type: {snippet['type']}")
            if snippet.get("labels"):
                typer.echo(f"Labels: {', '.join(snippet['labels'])}")
            if snippet.get("enable_prefix") is not None:
                typer.echo(f"Enable Prefix: {snippet['enable_prefix']}")
            if snippet.get("id"):
                typer.echo(f"ID: {snippet['id']}")
        else:
            snippets = scm_client.list_snippets()

            if not snippets:
                typer.echo("No snippets found")
                return

            typer.echo(f"\nSnippets ({len(snippets)}):")
            typer.echo("-" * 80)
            for s in snippets:
                typer.echo(f"Name: {s.get('name', 'N/A')}")
                if s.get("description"):
                    typer.echo(f"  Description: {s['description']}")
                if s.get("type"):
                    typer.echo(f"  Type: {s['type']}")
                typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error showing snippets: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("snippet")
def delete_snippet(
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a snippet.

    Example: scm delete setup snippet --name "DNS-Best-Practice"
    """
    try:
        if not force:
            typer.confirm(f"Delete snippet '{name}'?", abort=True)
        result = scm_client.delete_snippet(name=name)

        if result:
            typer.echo(f"Deleted snippet: {name}")
        else:
            typer.echo(f"Snippet not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting snippet: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("snippet")
def load_snippet(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load snippets from a YAML file.

    Example: scm load setup snippet --file snippets.yaml
    """
    try:
        config = load_from_yaml(str(file), "snippets")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["snippets"]))
            return None

        results = []
        for snippet_data in config["snippets"]:
            snippet_model = Snippet(**snippet_data)
            sdk_data = snippet_model.to_sdk_model()
            result = scm_client.create_snippet(**sdk_data)
            results.append(result)

            action = result.get("__action__", "created")
            if action == "no_change":
                typer.echo(f"No changes for snippet: {snippet_model.name}")
            elif action == "updated":
                typer.echo(f"Updated snippet: {snippet_model.name}")
            else:
                typer.echo(f"Created snippet: {snippet_model.name}")

        typer.echo(f"\nProcessed {len(results)} snippets from {file}")
        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading snippets: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("snippet")
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

    try:
        snippets = scm_client.list_snippets()

        if not snippets:
            typer.echo("No snippets found")
            return None

        backup_data = []
        for s in snippets:
            s_dict = s.copy()
            s_dict.pop("id", None)
            backup_data.append(s_dict)

        yaml_data = {"snippets": backup_data}

        with open(file, "w") as fh:
            yaml.dump(yaml_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} snippets to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up snippets: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# VARIABLE COMMANDS
# =============================================================================================================================================================================================


@set_app.command("variable")
def set_variable(
    name: str = NAME_OPTION,
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
        scm set setup variable --name "\$egress-max" --type egress-max --value 1000 --folder Texas
        scm set setup variable --name "\$dns-server" --type fqdn --value dns.example.com --snippet "DNS-Config"

    """
    try:
        container_type, container_value = validate_container_params(folder, snippet, device)

        variable_model = Variable(
            name=name,
            type=type,
            value=value,
            folder=folder,
            snippet=snippet,
            device=device,
            description=description,
        )

        result = scm_client.create_variable(**variable_model.to_sdk_model())

        action = result.get("__action__", "created")
        if action == "no_change":
            typer.echo(f"No changes detected for variable: {name} in {container_type} {container_value}")
        elif action == "updated":
            typer.echo(f"Updated variable: {name} in {container_type} {container_value}")
        else:
            typer.echo(f"Created variable: {name} in {container_type} {container_value}")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating variable: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("variable")
def show_variable(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the variable to show"),
):
    r"""Display variables.

    Examples
    --------
        scm show setup variable --folder Texas
        scm show setup variable --folder Texas --name "\$egress-max"

    """
    try:
        if name:
            variable = scm_client.get_variable(name=name, folder=folder, snippet=snippet, device=device)

            typer.echo(f"\nVariable: {variable.get('name', 'N/A')}")
            typer.echo("=" * 80)
            typer.echo(f"Type: {variable.get('type', 'N/A')}")
            typer.echo(f"Value: {variable.get('value', 'N/A')}")
            if variable.get("description"):
                typer.echo(f"Description: {variable['description']}")
            if variable.get("folder"):
                typer.echo(f"Folder: {variable['folder']}")
            if variable.get("snippet"):
                typer.echo(f"Snippet: {variable['snippet']}")
            if variable.get("device"):
                typer.echo(f"Device: {variable['device']}")
            if variable.get("id"):
                typer.echo(f"ID: {variable['id']}")
        else:
            variables = scm_client.list_variables(folder=folder, snippet=snippet, device=device)

            if not variables:
                typer.echo("No variables found")
                return

            typer.echo(f"\nVariables ({len(variables)}):")
            typer.echo("-" * 80)
            for v in variables:
                typer.echo(f"Name: {v.get('name', 'N/A')}")
                typer.echo(f"  Type: {v.get('type', 'N/A')}")
                typer.echo(f"  Value: {v.get('value', 'N/A')}")
                if v.get("description"):
                    typer.echo(f"  Description: {v['description']}")
                typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error showing variables: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("variable")
def delete_variable(
    name: str = NAME_OPTION,
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    r"""Delete a variable.

    Example: scm delete setup variable --name "\$egress-max" --folder Texas
    """
    try:
        container_type, container_value = validate_container_params(folder, snippet, device)
        if not force:
            typer.confirm(f"Delete variable '{name}' from {container_type} '{container_value}'?", abort=True)
        result = scm_client.delete_variable(name=name, folder=folder, snippet=snippet, device=device)

        if result:
            typer.echo(f"Deleted variable: {name} from {container_type} {container_value}")
        else:
            typer.echo(f"Variable not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting variable: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("variable")
def load_variable(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load variables from a YAML file.

    Example: scm load setup variable --file variables.yaml
    """
    try:
        config = load_from_yaml(str(file), "variables")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["variables"]))
            return None

        results = []
        for var_data in config["variables"]:
            variable_model = Variable(**var_data)
            sdk_data = variable_model.to_sdk_model()
            result = scm_client.create_variable(**sdk_data)
            results.append(result)

            action = result.get("__action__", "created")
            if action == "no_change":
                typer.echo(f"No changes for variable: {variable_model.name}")
            elif action == "updated":
                typer.echo(f"Updated variable: {variable_model.name}")
            else:
                typer.echo(f"Created variable: {variable_model.name}")

        typer.echo(f"\nProcessed {len(results)} variables from {file}")
        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading variables: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("variable")
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

    try:
        variables = scm_client.list_variables(folder=folder, snippet=snippet, device=device)

        if not variables:
            typer.echo("No variables found")
            return None

        backup_data = []
        for v in variables:
            v_dict = v.copy()
            v_dict.pop("id", None)
            backup_data.append(v_dict)

        yaml_data = {"variables": backup_data}

        with open(file, "w") as fh:
            yaml.dump(yaml_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} variables to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up variables: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


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
def show_device(
    name: str | None = typer.Option(None, "--name", help="Name or serial number of the device to show"),
    folder: str | None = typer.Option(None, "--folder", help="Filter devices by folder"),
):
    """Display devices.

    Examples
    --------
        scm show setup device
        scm show setup device --name "PA-VM-01"
        scm show setup device --folder Texas

    """
    try:
        if name:
            device = scm_client.get_device(name=name)

            typer.echo(f"\nDevice: {device.get('name', device.get('hostname', 'N/A'))}")
            typer.echo("=" * 80)
            if device.get("serial_number"):
                typer.echo(f"Serial Number: {device['serial_number']}")
            if device.get("model"):
                typer.echo(f"Model: {device['model']}")
            if device.get("family"):
                typer.echo(f"Family: {device['family']}")
            if device.get("hostname"):
                typer.echo(f"Hostname: {device['hostname']}")
            if device.get("display_name"):
                typer.echo(f"Display Name: {device['display_name']}")
            if device.get("description"):
                typer.echo(f"Description: {device['description']}")
            if device.get("labels"):
                typer.echo(f"Labels: {', '.join(device['labels'])}")
            if device.get("snippets"):
                typer.echo(f"Snippets: {', '.join(device['snippets'])}")
            if device.get("ip_address"):
                typer.echo(f"IP Address: {device['ip_address']}")
            if device.get("folder"):
                typer.echo(f"Folder: {device['folder']}")
            if device.get("software_version"):
                typer.echo(f"Software Version: {device['software_version']}")
            if device.get("is_connected") is not None:
                typer.echo(f"Connected: {device['is_connected']}")
            if device.get("uptime"):
                typer.echo(f"Uptime: {device['uptime']}")
            if device.get("id"):
                typer.echo(f"ID: {device['id']}")
        else:
            devices = scm_client.list_devices(folder=folder)

            if not devices:
                typer.echo("No devices found")
                return

            typer.echo(f"\nDevices ({len(devices)}):")
            typer.echo("-" * 80)
            for d in devices:
                display_name = d.get("name", d.get("hostname", "N/A"))
                typer.echo(f"Name: {display_name}")
                if d.get("serial_number"):
                    typer.echo(f"  Serial: {d['serial_number']}")
                if d.get("model"):
                    typer.echo(f"  Model: {d['model']}")
                if d.get("folder"):
                    typer.echo(f"  Folder: {d['folder']}")
                if d.get("labels"):
                    typer.echo(f"  Labels: {', '.join(d['labels'])}")
                if d.get("is_connected") is not None:
                    typer.echo(f"  Connected: {d['is_connected']}")
                typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error showing devices: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("device")
def set_device(
    name: str = NAME_OPTION,
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
        scm set setup device --name PA-VM-01 --labels production --labels west
        scm set setup device --name 0123456789 --folder Austin
        scm set setup device --name PA-VM-01 --description "Edge firewall"

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
        result = scm_client.update_device(**device_model.to_sdk_model())

        action = result.get("__action__", "updated")
        if action == "no_change":
            typer.echo(f"No changes detected for device: {name}")
        else:
            typer.echo(f"Updated device: {name}")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error updating device: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("device")
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
    try:
        config = load_from_yaml(str(file), "devices")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["devices"]))
            return None

        results = []
        for device_data in config["devices"]:
            device_model = Device(**device_data)
            result = scm_client.update_device(**device_model.to_sdk_model())
            results.append(result)

            action = result.get("__action__", "updated")
            if action == "no_change":
                typer.echo(f"No changes for device: {device_model.name}")
            else:
                typer.echo(f"Updated device: {device_model.name}")

        typer.echo(f"\nProcessed {len(results)} devices from {file}")
        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading devices: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("device")
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

    try:
        devices = scm_client.list_devices()

        if not devices:
            typer.echo("No devices found")
            return None

        backup_data = []
        for d in devices:
            d_dict = d.copy()
            d_dict.pop("id", None)
            backup_data.append(d_dict)

        yaml_data = {"devices": backup_data}

        with open(file, "w") as fh:
            yaml.dump(yaml_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} devices to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up devices: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
