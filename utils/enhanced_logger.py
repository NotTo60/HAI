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
    DEFAULT_LOG_LEVEL, DEFAULT_LOG_MAX_SIZE, DEFAULT_LOG_BACKUP_COUNT, ENHANCED_LOG_BUFFER_SIZE, MAX_OUTPUT_LENGTH, MAX_RESULT_LENGTH
)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with context."""
    
    def __init__(self, include_context: bool = True):
        super().__init__(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        self.include_context = include_context
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with additional context."""
        # Add structured data if available
        if hasattr(record, 'context') and self.include_context:
            context_str = f" | Context: {json.dumps(record.context)}"
        else:
            context_str = ""
        
        # Format the base message
        formatted = super().format(record)
        
        # Add context if available
        if context_str:
            formatted += context_str
        
        return formatted


class ServerLogger:
    """Per-server logger that creates individual log files for each server."""
    
    def __init__(self, server_name: str, server_ip: str, log_dir: Optional[Path] = None):
        """
        Initialize server-specific logger.
        
        Args:
            server_name: Name of the server
            server_ip: IP address of the server
            log_dir: Directory for server logs (defaults to logs/servers/)
        """
        self.server_name = server_name
        self.server_ip = server_ip
        self.log_dir = log_dir or Path(LOGS_DIR) / "servers"
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(f"server.{server_name}")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up file and console handlers for server logger."""
        # File handler with rotation
        log_file = self.log_dir / f"{self.server_name}_{self.server_ip}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=DEFAULT_LOG_MAX_SIZE,
            backupCount=DEFAULT_LOG_BACKUP_COUNT
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = StructuredFormatter()
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_operation(self, operation: str, status: str, details: Dict[str, Any] = None, 
                     execution_time: float = None, error: str = None):
        """
        Log an operation with structured data.
        
        Args:
            operation: Name of the operation
            status: Success/failure status
            details: Additional operation details
            execution_time: Time taken for operation
            error: Error message if failed
        """
        context = {
            "server": self.server_name,
            "ip": self.server_ip,
            "operation": operation,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            context.update(details)
        
        if execution_time is not None:
            context["execution_time"] = f"{execution_time:.2f}s"
        
        if error:
            context["error"] = error
        
        # Create log record with context
        record = logging.LogRecord(
            name=self.logger.name,
            level=logging.INFO if status == "SUCCESS" else logging.ERROR,
            pathname="",
            lineno=0,
            msg=f"Operation: {operation} | Status: {status}",
            args=(),
            exc_info=None
        )
        record.context = context
        
        if status == "SUCCESS":
            self.logger.info(record.msg, extra={"context": context})
        else:
            self.logger.error(record.msg, extra={"context": context})
    
    def log_command(self, command: str, output: str = None, error: str = None, 
                   execution_time: float = None):
        """Log command execution."""
        status = "SUCCESS" if not error else "FAILED"
        details = {"command": command}
        
        if output:
            details["output"] = output[:MAX_OUTPUT_LENGTH] + "..." if len(output) > MAX_OUTPUT_LENGTH else output
        
        self.log_operation("command_execution", status, details, execution_time, error)
    
    def log_file_transfer(self, operation: str, local_path: str, remote_path: str,
                         status: str, file_size: int = None, execution_time: float = None,
                         error: str = None):
        """Log file transfer operations."""
        details = {
            "operation": operation,
            "local_path": local_path,
            "remote_path": remote_path
        }
        
        if file_size:
            details["file_size"] = f"{file_size} bytes"
        
        self.log_operation("file_transfer", status, details, execution_time, error)
    
    def log_connection(self, status: str, method: str, execution_time: float = None,
                      error: str = None):
        """Log connection attempts."""
        details = {"connection_method": method}
        self.log_operation("connection", status, details, execution_time, error)
    
    def log_custom_operation(self, operation_name: str, status: str, 
                           result: Any = None, execution_time: float = None,
                           error: str = None):
        """Log custom operations."""
        details = {"operation_name": operation_name}
        
        if result:
            details["result"] = str(result)[:MAX_RESULT_LENGTH] + "..." if len(str(result)) > MAX_RESULT_LENGTH else str(result)
        
        self.log_operation("custom_operation", status, details, execution_time, error)


class PerformanceLogger:
    """Logger for performance metrics and statistics."""
    
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or Path(LOGS_DIR) / "performance.log"
        self.logger = logging.getLogger("performance")
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up performance logger handlers."""
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        file_handler.setFormatter(formatter)
        
        # Add handler
        self.logger.addHandler(file_handler)
    
    def log_batch_operation(self, operation_type: str, total_servers: int,
                           successful: int, failed: int, execution_time: float,
                           avg_time_per_server: float = None):
        """Log batch operation performance metrics."""
        context = {
            "operation_type": operation_type,
            "total_servers": total_servers,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/total_servers)*100:.1f}%" if total_servers > 0 else "0%",
            "execution_time": f"{execution_time:.2f}s",
            "avg_time_per_server": f"{avg_time_per_server:.2f}s" if avg_time_per_server else "N/A",
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"Batch operation completed: {operation_type}", extra={"context": context})


class EnhancedLogger:
    """Enhanced logger with per-server logging and buffering capabilities."""
    
    def __init__(self, name="hai", level=DEFAULT_LOG_LEVEL, buffer_size=ENHANCED_LOG_BUFFER_SIZE):
        self.name = name
        self.level = level
        self.buffer_size = buffer_size
        self.log_buffer = []
        self.server_loggers = {}
        
        # Create main logger
        self.logger = self._create_logger(name, level)
        
    def _create_logger(self, name, level):
        """Create a logger with console and file handlers."""
        logger = logging.getLogger(name)
        
        if not logger.handlers:
            logger.setLevel(level)
            
            # Create formatter
            formatter = logging.Formatter(LOG_FORMAT)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler
            if not os.path.exists(LOGS_DIR):
                os.makedirs(LOGS_DIR)
                
            log_file = os.path.join(LOGS_DIR, f"{name}.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _create_server_logger(self, server_name):
        """Create a dedicated logger for a specific server."""
        if server_name in self.server_loggers:
            return self.server_loggers[server_name]
        
        # Create server-specific log directory
        server_log_dir = os.path.join(LOGS_DIR, "servers")
        if not os.path.exists(server_log_dir):
            os.makedirs(server_log_dir)
        
        # Create server logger
        server_logger = logging.getLogger(f"{self.name}.{server_name}")
        server_logger.setLevel(self.level)
        
        # Clear any existing handlers
        server_logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT)
        
        # Console handler (inherits from parent)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(formatter)
        server_logger.addHandler(console_handler)
        
        # Server-specific file handler
        server_log_file = os.path.join(server_log_dir, f"{server_name}.log")
        file_handler = logging.FileHandler(server_log_file)
        file_handler.setLevel(self.level)
        file_handler.setFormatter(formatter)
        server_logger.addHandler(file_handler)
        
        self.server_loggers[server_name] = server_logger
        return server_logger
    
    def log(self, level, message, server_name=None):
        """Log a message with optional server-specific logging."""
        # Add to buffer
        log_entry = {
            'timestamp': datetime.now(),
            'level': level,
            'message': message,
            'server': server_name
        }
        self.log_buffer.append(log_entry)
        
        # Flush buffer if it's full
        if len(self.log_buffer) >= self.buffer_size:
            self.flush_buffer()
        
        # Log to appropriate logger
        if server_name:
            server_logger = self._create_server_logger(server_name)
            server_logger.log(level, f"[{server_name}] {message}")
        else:
            self.logger.log(level, message)
    
    def debug(self, message, server_name=None):
        self.log(logging.DEBUG, message, server_name)
    
    def info(self, message, server_name=None):
        self.log(logging.INFO, message, server_name)
    
    def warning(self, message, server_name=None):
        self.log(logging.WARNING, message, server_name)
    
    def error(self, message, server_name=None):
        self.log(logging.ERROR, message, server_name)
    
    def critical(self, message, server_name=None):
        self.log(logging.CRITICAL, message, server_name)
    
    def flush_buffer(self):
        """Flush the log buffer to disk."""
        if not self.log_buffer:
            return
        
        # Write buffer to a separate buffer file
        buffer_file = os.path.join(LOGS_DIR, f"{self.name}_buffer.log")
        with open(buffer_file, 'a') as f:
            for entry in self.log_buffer:
                timestamp = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                level_name = logging.getLevelName(entry['level'])
                server_info = f"[{entry['server']}] " if entry['server'] else ""
                f.write(f"[{timestamp}] [{level_name}] {server_info}{entry['message']}\n")
        
        # Clear buffer
        self.log_buffer.clear()
    
    def get_server_logger(self, server_name):
        """Get a dedicated logger for a specific server."""
        return self._create_server_logger(server_name)
    
    def close(self):
        """Close all loggers and flush buffer."""
        self.flush_buffer()
        
        # Close all server loggers
        for logger in self.server_loggers.values():
            for handler in logger.handlers:
                handler.close()
        
        # Close main logger
        for handler in self.logger.handlers:
            handler.close()
    
    def log_info(self, message, context=None):
        self.logger.info(message)
    
    def log_operation_start(self, operation, servers_count=None):
        msg = f"Operation '{operation}' started. Servers: {servers_count}" if servers_count else f"Operation '{operation}' started."
        self.logger.info(msg)
    
    def log_operation_complete(self, operation, results):
        self.logger.info(f"Operation '{operation}' complete. Results: {results}")

# Global enhanced logger instance
enhanced_logger = EnhancedLogger()

def get_enhanced_logger(name="hai", level=DEFAULT_LOG_LEVEL):
    """Get the global enhanced logger instance."""
    return enhanced_logger


def get_server_logger(server_name: str) -> ServerLogger:
    """Get a server-specific logger."""
    return ServerLogger(server_name, server_ip=None)


def log_operation_start(operation: str, servers_count: int = None):
    """Log operation start using global logger."""
    get_enhanced_logger().log_operation_start(operation, servers_count)


def log_operation_complete(operation: str, results: Dict[str, Any]):
    """Log operation completion using global logger."""
    get_enhanced_logger().log_operation_complete(operation, results)


def log_error(error: str, context: Dict[str, Any] = None):
    """Log error using global logger."""
    get_enhanced_logger().log_error(error, context)


def log_warning(warning: str, context: Dict[str, Any] = None):
    """Log warning using global logger."""
    get_enhanced_logger().log_warning(warning, context)


def log_info(message: str, context: Dict[str, Any] = None):
    """Log info message using global logger."""
    get_enhanced_logger().log_info(message, context)


def log_debug(message: str, context: Dict[str, Any] = None):
    """Log debug message using global logger."""
    get_enhanced_logger().log_debug(message, context) 