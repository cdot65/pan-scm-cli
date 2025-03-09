"""Configuration module for SCM CLI."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv
from rich.console import Console

# Initialize console for error messages
console = Console(stderr=True)


@dataclass
class SCMConfig:
    """Configuration class for SCM API credentials."""

    client_id: str
    client_secret: str
    tsg_id: str
    base_url: str = "https://api.strata.paloaltonetworks.com"
    verify_ssl: bool = True


def load_oauth_credentials() -> Tuple[bool, Optional[SCMConfig]]:
    """Load OAuth credentials from .env file.
    
    Returns:
        Tuple containing success flag and config object if successful
    """
    # Look for .env file in current directory
    env_path = Path(".env")
    
    if not env_path.exists():
        console.print("[bold red]Error:[/bold red] .env file not found in current directory", style="red")
        console.print("Please create a .env file with the following variables:", style="yellow")
        console.print("  SCM_CLIENT_ID=your_client_id", style="yellow")
        console.print("  SCM_CLIENT_SECRET=your_client_secret", style="yellow")
        console.print("  SCM_TSG_ID=your_tsg_id", style="yellow")
        return False, None
    
    # Load environment variables from .env file
    load_dotenv(env_path)

    # Get values from environment
    client_id = os.getenv("SCM_CLIENT_ID", "")
    client_secret = os.getenv("SCM_CLIENT_SECRET", "")
    tsg_id = os.getenv("SCM_TSG_ID", "")
    
    # Check if any required variables are missing
    missing_vars = []
    if not client_id:
        missing_vars.append("SCM_CLIENT_ID")
    if not client_secret:
        missing_vars.append("SCM_CLIENT_SECRET")
    if not tsg_id:
        missing_vars.append("SCM_TSG_ID")
        
    # If any vars are missing, display error and return
    if missing_vars:
        console.print(f"[bold red]Error:[/bold red] Missing required environment variables: {', '.join(missing_vars)}", style="red")
        console.print("Please update your .env file with these variables:", style="yellow")
        for var in missing_vars:
            console.print(f"  {var}=your_{var.lower()}", style="yellow")
        return False, None
    
    # Create config object
    base_url = os.getenv("SCM_BASE_URL", "https://api.strata.paloaltonetworks.com")
    verify_ssl = os.getenv("SCM_VERIFY_SSL", "true").lower() != "false"
    
    config = SCMConfig(
        client_id=client_id,
        client_secret=client_secret,
        tsg_id=tsg_id,
        base_url=base_url,
        verify_ssl=verify_ssl,
    )
    
    return True, config