"""
Enhanced logging system for HAI with per-server logging and structured logging.

This module provides:
1. Centralized logging configuration
2. Per-server log files
3. Structured logging with context
4. Log rotation and management
5. Performance metrics logging
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from utils.constants import (
    LOGS_DIR, LOG_FORMAT, LOG_DATE_FORMAT,
    DEFAULT_LOG_LEVEL, ENHANCED_LOG_BUFFER_SIZE, MAX_OUTPUT_LENGTH, MAX_RESULT_LENGTH
)


class EnhancedLogger:
    """Enhanced logger with buffering and structured logging capabilities."""
    
    def __init__(self, name="hai", level=DEFAULT_LOG_LEVEL, buffer_size=ENHANCED_LOG_BUFFER_SIZE):
        self.name = name
        self.buffer_size = buffer_size
        self.log_buffer = []
        self.logger = self._create_logger(name, level)
    
    def _create_logger(self, name, level):
        """Create and configure a logger."""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # File handler
            log_file = Path(LOGS_DIR) / f"{name}.log"
            log_file.parent.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Formatter
            formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            # Add handlers
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
        
        return logger
    
    def log(self, level, message, server_name=None):
        """Log a message with optional server context."""
        if server_name:
            message = f"[{server_name}] {message}"
        
        # Add to buffer
        self.log_buffer.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'server': server_name
        })
        
        # Flush buffer if it's full
        if len(self.log_buffer) >= self.buffer_size:
            self.flush_buffer()
        
        # Log immediately
        getattr(self.logger, level.lower())(message)
    
    def debug(self, message, server_name=None):
        self.log('DEBUG', message, server_name)
    
    def info(self, message, server_name=None):
        self.log('INFO', message, server_name)
    
    def warning(self, message, server_name=None):
        self.log('WARNING', message, server_name)
    
    def error(self, message, server_name=None):
        self.log('ERROR', message, server_name)
    
    def critical(self, message, server_name=None):
        self.log('CRITICAL', message, server_name)
    
    def flush_buffer(self):
        """Flush the log buffer to persistent storage."""
        if not self.log_buffer:
            return
        
        # Write buffer to a separate file
        buffer_file = Path(LOGS_DIR) / f"{self.name}_buffer.log"
        with open(buffer_file, 'a') as f:
            for entry in self.log_buffer:
                f.write(f"{entry['timestamp']} - {entry['level']} - {entry['message']}\n")
        
        # Clear buffer
        self.log_buffer.clear()
    
    def close(self):
        """Close the logger and flush any remaining buffer."""
        self.flush_buffer()
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
    
    def log_info(self, message, context=None):
        """Log info message with optional context."""
        if context:
            message = f"{message} | Context: {json.dumps(context)}"
        self.info(message)
    
    def log_warning(self, message, context=None):
        """Log warning message with optional context."""
        if context:
            message = f"{message} | Context: {json.dumps(context)}"
        self.warning(message)
    
    def log_error(self, message, context=None):
        """Log error message with optional context."""
        if context:
            message = f"{message} | Context: {json.dumps(context)}"
        self.error(message)
    
    def log_operation_start(self, operation, servers_count=None):
        """Log the start of an operation."""
        message = f"Starting operation: {operation}"
        if servers_count:
            message += f" on {servers_count} servers"
        self.info(message)
    
    def log_operation_complete(self, operation, results):
        """Log the completion of an operation."""
        message = f"Completed operation: {operation}"
        if results:
            message += f" | Results: {json.dumps(results)}"
        self.info(message)
    
    def log_command(self, command, output=None, error=None, execution_time=None):
        """Log command execution details."""
        message = f"Command executed: {command}"
        if execution_time:
            message += f" (took {execution_time:.2f}s)"
        if output:
            # Truncate output if too long
            if len(output) > MAX_OUTPUT_LENGTH:
                output = output[:MAX_OUTPUT_LENGTH] + "..."
            message += f" | Output: {output}"
        if error:
            message += f" | Error: {error}"
        self.info(message)
    
    def log_file_transfer(self, operation, local_path, remote_path, status, file_size=None, execution_time=None, error=None):
        """Log file transfer details."""
        message = f"File {operation}: {local_path} -> {remote_path} | Status: {status}"
        if execution_time:
            message += f" (took {execution_time:.2f}s)"
        if file_size:
            message += f" | Size: {file_size} bytes"
        if error:
            message += f" | Error: {error}"
        self.info(message)


# Global logger instance
_enhanced_logger = None

def get_enhanced_logger(name="hai", level=DEFAULT_LOG_LEVEL):
    """Get or create the global enhanced logger instance."""
    global _enhanced_logger
    if _enhanced_logger is None:
        _enhanced_logger = EnhancedLogger(name, level)
    return _enhanced_logger

def get_server_logger(server_name: str, server_ip: str = None):
    """Get a logger for a specific server."""
    return get_enhanced_logger(f"server.{server_name}")

# Convenience functions
def log_operation_start(operation: str, servers_count: int = None):
    get_enhanced_logger().log_operation_start(operation, servers_count)

def log_operation_complete(operation: str, results: Dict[str, Any]):
    get_enhanced_logger().log_operation_complete(operation, results)

def log_error(error: str, context: Dict[str, Any] = None):
    get_enhanced_logger().log_info(f"ERROR: {error}", context)

def log_warning(warning: str, context: Dict[str, Any] = None):
    get_enhanced_logger().log_info(f"WARNING: {warning}", context)

def log_info(message: str, context: Dict[str, Any] = None):
    get_enhanced_logger().log_info(message, context)

def log_debug(message: str, context: Dict[str, Any] = None):
    get_enhanced_logger().log_info(f"DEBUG: {message}", context)

def log_performance(operation: str, duration: float, servers_count: int = None):
    """Log performance metrics."""
    message = f"Performance: {operation} took {duration:.2f}s"
    if servers_count:
        message += f" for {servers_count} servers"
    get_enhanced_logger().info(message)

def log_server_operation(server_name: str, operation: str, status: str, details: str = None):
    """Log server-specific operation details."""
    message = f"Server {server_name}: {operation} - {status}"
    if details:
        message += f" | {details}"
    get_enhanced_logger().info(message, {"server": server_name, "operation": operation, "status": status}) 