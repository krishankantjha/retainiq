"""
Logging configuration module.
Loads logging dictConfig parameters from configs/logging_config.yaml.
"""

import os
import logging
import logging.config
import yaml


def setup_logging() -> None:
    """
    Locates logging_config.yaml in the project configs directory,
    parses the YAML file, and initializes standard python dictConfig settings.
    """
    # Find relative location of configs/logging_config.yaml from this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.abspath(
        os.path.join(current_dir, "..", "..", "..", "configs", "logging_config.yaml")
    )

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            # Ensure the log file is written relative to the project root
            # rather than current working directory, if needed
            handlers = config.get("handlers", {})
            if "file" in handlers:
                log_file = handlers["file"].get("filename", "backend.log")
                if not os.path.isabs(log_file):
                    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
                    handlers["file"]["filename"] = os.path.join(project_root, log_file)

            logging.config.dictConfig(config)
            logging.info("Logging configured successfully from configs/logging_config.yaml")
        except Exception as e:
            logging.basicConfig(level=logging.INFO)
            logging.error(f"Failed to load logging config from {config_path}: {e}")
    else:
        # Fallback to basic configuration
        logging.basicConfig(level=logging.INFO)
        logging.warning(f"logging_config.yaml not found at {config_path}. Initialized basic config.")


# Automatically configure logging when module is imported
setup_logging()
