import streamlit as st
import tomllib
from pathlib import Path
from typing import Any, Optional, Dict
from functools import lru_cache

class EnvHelper:
    """Flexible environment access for multiple TOML files"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        # Pre-load common files
        self._ensure_loaded('config')
        self._ensure_loaded('secrets')
    
    @lru_cache(maxsize=256)
    def __call__(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Access variables from any TOML file using dot notation:
        env("config.theme.primaryColor")
        env("secrets.database.url")
        env("custom.file.section.value")
        """
        try:
            parts = key.split('.')
            if len(parts) < 2:
                return default
            
            file_name = parts[0]
            rest_keys = parts[1:]
            
            # Load the file if not already loaded
            data = self._ensure_loaded(file_name)
            
            # Get nested value
            return self._get_nested_value(data, rest_keys) or default
            
        except Exception as e:
            st.error(f"Error accessing {key}: {e}")
            return default
    
    def _ensure_loaded(self, file_name: str) -> Dict:
        """Ensure a file is loaded into cache"""
        if file_name not in self._cache:
            file_path = f".streamlit/{file_name}.toml"
            self._cache[file_name] = self._load_toml_file(file_path)
        
        return self._cache[file_name]
    
    def _load_toml_file(self, file_path: str) -> Dict:
        """Load a TOML file safely"""
        path = Path(file_path)
        if not path.exists():
            return {}
        
        try:
            with open(path, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            st.error(f"Error loading {file_path}: {e}")
            return {}
    
    def _get_nested_value(self, data: Dict, keys: list) -> Any:
        """Get nested value from dictionary"""
        if not data or not keys:
            return None
        
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def reload(self, file_name: str = None):
        """Reload one or all files"""
        if file_name:
            if file_name in self._cache:
                del self._cache[file_name]
                self.__call__.cache_clear()  # Clear function cache
        else:
            self._cache.clear()
            self.__call__.cache_clear()
