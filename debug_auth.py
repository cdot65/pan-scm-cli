#!/usr/bin/env python3
"""Debug script to test authentication configuration loading."""

import os
import sys
import yaml
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from scm_cli.utils.config import get_auth_config, HOME_CONFIG_PATH

print(f"Checking authentication configuration...")
print(f"Home config path: {HOME_CONFIG_PATH}")
print(f"Home config exists: {os.path.exists(HOME_CONFIG_PATH)}")

# Try to load the home config file directly
if os.path.exists(HOME_CONFIG_PATH):
    try:
        with open(HOME_CONFIG_PATH) as f:
            home_config = yaml.safe_load(f) or {}
            print(f"Direct home config read: {home_config}")
    except Exception as e:
        print(f"Error directly reading home config: {e}")

# Try to get authentication config using our utility
try:
    auth_config = get_auth_config()
    print(f"Auth config from get_auth_config(): {auth_config}")
    
    # Check environment variables
    print("\nEnvironment variables:")
    for env_var in ["SCM_CLIENT_ID", "SCM_CLIENT_SECRET", "SCM_TSG_ID"]:
        if env_var in os.environ:
            print(f"  {env_var}: Set (value hidden)")
        else:
            print(f"  {env_var}: Not set")
            
    print("\nAuthentication parameters:")
    for key, value in auth_config.items():
        # Print first few characters of sensitive values
        if value and isinstance(value, str):
            display_val = value[:4] + "..." if len(value) > 4 else "..."
        else:
            display_val = "None"
        print(f"  {key}: {display_val}")
        
except Exception as e:
    print(f"Error getting auth config: {e}")
