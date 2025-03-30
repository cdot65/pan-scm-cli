"""pan-scm-cli: CLI for Palo Alto Networks Strata Cloud Manager."""

__version__ = "0.2.0"

from .main import app


def main():
    """Entry point for the scm-cli command."""
    app()
