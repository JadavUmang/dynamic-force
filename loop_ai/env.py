"""Environment variable loader for Loop Engineering AI."""

import os
import pathlib
from typing import Optional


def load_dotenv(env_path: Optional[pathlib.Path] = None) -> None:
    """
    Loads key-value pairs from a .env file into os.environ without requiring external dependencies.
    Searches in specified path, current working directory, and package root.
    """
    search_paths = []
    if env_path:
        search_paths.append(pathlib.Path(env_path))
    else:
        search_paths.append(pathlib.Path.cwd() / ".env")
        search_paths.append(pathlib.Path(__file__).resolve().parent.parent / ".env")

    for path in search_paths:
        if path.exists() and path.is_file():
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        # Do not overwrite if already set in environment
                        if key and key not in os.environ:
                            os.environ[key] = val
                break
            except Exception:
                pass
