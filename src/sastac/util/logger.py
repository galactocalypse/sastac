import logging
import sys
from sastac.util.service import InternalFileService

import os
from pathlib import Path
from sastac.util.service import EnvService

def setup_logger(name: str = "sastac") -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Ensure environment is loaded
    EnvService.load_env()
    
    log_level_str = os.environ.get("SASTAC_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers if setup_logger is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        InternalFileService.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = InternalFileService.LOGS_DIR / "application.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Don't propagate to the root logger to avoid duplicate console output
        logger.propagate = False

    return logger

logger = setup_logger()
get_logger = setup_logger
