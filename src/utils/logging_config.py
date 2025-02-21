import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """Configure le système de logging"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "mantcare.log")
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler fichier avec rotation
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configuration root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)