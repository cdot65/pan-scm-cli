"""pan-scm-cli: CLI for Palo Alto Networks Strata Cloud Manager."""

from importlib.metadata import version

__version__ = version("pan-scm-cli")

from .main import app


def main():
    """Entry point for the scm command."""
    app()
