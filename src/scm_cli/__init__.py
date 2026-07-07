"""pan-scm-cli: CLI for Palo Alto Networks Strata Cloud Manager."""


def __getattr__(name: str):
    """Resolve __version__ lazily — importlib.metadata costs ~30ms at import."""
    if name == "__version__":
        from importlib.metadata import version

        return version("pan-scm-cli")
    raise AttributeError(name)


def main():
    """Entry point for the scm command."""
    from .main import app

    app()
