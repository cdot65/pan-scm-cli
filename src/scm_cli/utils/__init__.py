"""Utility modules for the pan-scm-cli tool."""


def parse_comma_separated_list(values: list[str]) -> list[str]:
    """Split comma-separated values in list options.

    Allows both `--members a,b,c` and `--members a --members b --members c`.

    Args:
        values: List of string values, possibly containing commas.

    Returns:
        list[str]: Flattened list of stripped, non-empty values.

    """
    result = []
    for value in values:
        for item in value.split(","):
            stripped = item.strip()
            if stripped:
                result.append(stripped)
    return result


def format_container_location(obj: dict, include_rulebase: str | None = None) -> str:
    """Format the container location (folder, snippet, or device) for display.

    Args:
        obj: The object dictionary containing container information
        include_rulebase: Optional rulebase to include in the location string

    Returns:
        str: Formatted location string

    """
    location_parts = []

    if obj.get("folder"):
        location_parts.append(f"Folder '{obj['folder']}'")
    elif obj.get("snippet"):
        location_parts.append(f"Snippet '{obj['snippet']}'")
    elif obj.get("device"):
        location_parts.append(f"Device '{obj['device']}'")
    else:
        location_parts.append("N/A")

    if include_rulebase:
        location_parts.append(f"Rulebase '{include_rulebase}'")

    return " / ".join(location_parts)
