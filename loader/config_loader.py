import streamlit as st
import os
import json

@st.cache_resource  # Cache to prevent reloading on reruns
def load_all_json_configs(config_dir="config"):
    configs = {}
    exceptions = ["project_log"]

    for filename in os.listdir(config_dir):
        if filename.endswith(".json") and filename not in exceptions:
            path = os.path.join(config_dir, filename)
            with open(path, 'r') as f:
                configs[filename[:-5]] = json.load(f)  # remove .json

    return configs

def config(key_string: str):
    """
    Retrieve nested config using dot-separated string.
    Example: config("database.host")
    """
    result = load_all_json_configs()
    
    for key in key_string.split('.'):
        try:
            result = result[key]
        except (KeyError, TypeError):
            raise KeyError(f"Invalid config key: '{key}' in path '{key_string}'")
    return result
