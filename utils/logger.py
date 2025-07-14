import logging
import os
from utils.constants import LOG_FORMAT, DEFAULT_LOG_LEVEL, LOGS_DIR
from logging.handlers import RotatingFileHandler

def get_logger(name, level=DEFAULT_LOG_LEVEL):
    """Get a logger with the specified name and level."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Only add handlers if they don't exist
        logger.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Create file handler
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
            
        log_file = os.path.join(LOGS_DIR, f"{name}.log")
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
