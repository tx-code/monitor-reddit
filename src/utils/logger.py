import logging
import os
from datetime import datetime
from typing import Optional

class LoggerSetup:
    """Centralized logger setup for the application"""
    
    @staticmethod
    def setup_logger(name: str = __name__, 
                    log_file: str = None, 
                    log_level: int = logging.INFO,
                    log_dir: str = "logs") -> logging.Logger:
        """
        Setup and configure logger
        
        Args:
            name: Logger name
            log_file: Log file name (if None, uses default naming)
            log_level: Logging level
            log_dir: Directory for log files
        
        Returns:
            Configured logger instance
        """
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate log file name if not provided
        if not log_file:
            timestamp = datetime.now().strftime('%Y%m%d')
            log_file = f"reddit_monitor_{timestamp}.log"
        
        log_path = os.path.join(log_dir, log_file)
        
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
        
        return logger

def get_logger(name: str = __name__, **kwargs) -> logging.Logger:
    """Convenience function to get a configured logger"""
    return LoggerSetup.setup_logger(name, **kwargs)