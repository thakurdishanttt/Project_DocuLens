"""
Logging configuration for the application.

This module sets up the application-wide logging system with both file and console handlers.
It configures log formatting, rotation policies, and log levels for different handlers,
providing a consistent logging interface throughout the application.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(log_file: str = "logs/document_processor.log") -> logging.Logger:
    """
    Configure application-wide logging with both file and console handlers.
    
    Args:
        log_file (str): Path to the log file. Defaults to logs/document_processor.log
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("document_processor")
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s:%(lineno)d] - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler (with rotation)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    try:
        logger.info("Logging has been set up successfully.")
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
    
    return logger

# Create and configure the logger
logger = setup_logging()
