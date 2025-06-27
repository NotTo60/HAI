"""
Constants for the HAI (Hybrid Attack Interface) system.

This module contains all configuration constants, file paths, 
logging settings, and other system-wide constants.
"""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
SERVERS_DIR = BASE_DIR / "servers"
LOGS_DIR = BASE_DIR / "logs"
STATE_DIR = BASE_DIR / "state"
EXAMPLES_DIR = BASE_DIR / "examples"
TESTS_DIR = BASE_DIR / "tests"

# Ensure directories exist
for directory in [LOGS_DIR, STATE_DIR]:
    directory.mkdir(exist_ok=True)

# File paths
SERVERS_JSON_PATH = SERVERS_DIR / "servers.json"
PARAMIKO_CONFIG_PATH = CONFIG_DIR / "paramiko_config.yaml"
DEFAULT_STATE_FILE = STATE_DIR / "hai_state.json"
DEFAULT_LOG_FILE = LOGS_DIR / "hai.log"

# Logging constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

# Default logging configuration
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_TO_FILE = True
DEFAULT_LOG_TO_CONSOLE = True
DEFAULT_LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_LOG_BACKUP_COUNT = 5

# Threading constants
DEFAULT_MAX_WORKERS = 10
MIN_WORKERS = 1
MAX_WORKERS = 100
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_CONNECTION_TIMEOUT = 10  # seconds

# Progress bar constants
PROGRESS_BAR_WIDTH = 100
PROGRESS_BAR_UNIT = "server"
DEFAULT_PROGRESS_DESCRIPTION = "Running operation"

# File transfer constants
DEFAULT_COMPRESSION = True
DEFAULT_CHUNK_SIZE = 8192  # bytes
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
SUPPORTED_COMPRESSION_FORMATS = [".tar.gz", ".tar.bz2", ".zip"]

# Connection constants
DEFAULT_SSH_PORT = 22
DEFAULT_SMB_PORT = 445
DEFAULT_FTP_PORT = 21
DEFAULT_HTTP_PORT = 80
DEFAULT_HTTPS_PORT = 443

# Supported protocols
SUPPORTED_CONNECTION_METHODS = ["ssh", "smb", "custom", "ftp", "impacket"]
SUPPORTED_FILE_TRANSFER_PROTOCOLS = ["sftp", "scp", "smb", "ftp"]
SUPPORTED_OS_TYPES = ["linux", "windows", "unknown"]

# Server grades
SERVER_GRADES = ["critical", "must-win", "important", "nice-to-have", "low-priority"]

# State persistence constants
STATE_VERSION = "1.0"
STATE_ENCRYPTION_KEY = "HAI_STATE_KEY"  # In production, use environment variable
STATE_COMPRESSION = True
STATE_BACKUP_COUNT = 3

# Session constants
SESSION_TIMEOUT = 3600  # 1 hour
MAX_SESSION_SIZE = 100 * 1024 * 1024  # 100MB
SESSION_CLEANUP_INTERVAL = 300  # 5 minutes

# Error codes
ERROR_CODES = {
    "CONNECTION_FAILED": 1001,
    "AUTHENTICATION_FAILED": 1002,
    "COMMAND_FAILED": 1003,
    "FILE_TRANSFER_FAILED": 1004,
    "TIMEOUT": 1005,
    "INVALID_CONFIG": 1006,
    "PERMISSION_DENIED": 1007,
    "FILE_NOT_FOUND": 1008,
    "NETWORK_ERROR": 1009,
    "UNKNOWN_ERROR": 9999
}

# Status codes
STATUS_CODES = {
    "SUCCESS": 0,
    "PARTIAL_SUCCESS": 1,
    "FAILED": 2,
    "TIMEOUT": 3,
    "CANCELLED": 4
}

# CLI constants
CLI_DEFAULT_WORKERS = 10
CLI_DEFAULT_TIMEOUT = 30
CLI_MAX_WORKERS = 50

# Validation constants
MAX_HOSTNAME_LENGTH = 255
MAX_USERNAME_LENGTH = 32
MAX_PASSWORD_LENGTH = 128
MAX_COMMAND_LENGTH = 4096
MAX_FILE_PATH_LENGTH = 4096

# Security constants
MIN_PASSWORD_LENGTH = 8
REQUIRED_PASSWORD_CHARS = ["uppercase", "lowercase", "digit", "special"]
DEFAULT_SSH_KEY_PERMISSIONS = 0o600

# Performance constants
CONNECTION_POOL_SIZE = 20
COMMAND_CACHE_SIZE = 100
FILE_CACHE_SIZE = 50
MAX_CONCURRENT_DOWNLOADS = 5
MAX_CONCURRENT_UPLOADS = 5

# Monitoring constants
HEALTH_CHECK_INTERVAL = 300  # 5 minutes
PERFORMANCE_METRICS_INTERVAL = 60  # 1 minute
ALERT_THRESHOLD_SUCCESS_RATE = 80.0  # 80%
ALERT_THRESHOLD_RESPONSE_TIME = 30.0  # 30 seconds

# Backup and recovery constants
AUTO_BACKUP_INTERVAL = 3600  # 1 hour
MAX_BACKUP_FILES = 10
BACKUP_RETENTION_DAYS = 30

# Development and testing constants
TEST_TIMEOUT = 10
MOCK_SERVER_COUNT = 5
TEST_LOG_LEVEL = "DEBUG"
COVERAGE_THRESHOLD = 80.0

# Environment variables
ENV_LOG_LEVEL = "HAI_LOG_LEVEL"
ENV_LOG_FILE = "HAI_LOG_FILE"
ENV_STATE_FILE = "HAI_STATE_FILE"
ENV_MAX_WORKERS = "HAI_MAX_WORKERS"
ENV_TIMEOUT = "HAI_TIMEOUT"
ENV_ENCRYPTION_KEY = "HAI_ENCRYPTION_KEY"

# File extensions
LOG_EXTENSIONS = [".log", ".txt"]
STATE_EXTENSIONS = [".json", ".pickle", ".yaml"]
CONFIG_EXTENSIONS = [".yaml", ".yml", ".json", ".ini"]

# Time formats
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Color codes for console output (ANSI)
COLORS = {
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",
    "BRIGHT_RED": "\033[91m",
    "BRIGHT_GREEN": "\033[92m",
    "BRIGHT_YELLOW": "\033[93m",
    "BRIGHT_BLUE": "\033[94m",
    "BRIGHT_MAGENTA": "\033[95m",
    "BRIGHT_CYAN": "\033[96m"
}

# Emoji constants for better UX
EMOJIS = {
    "SUCCESS": "✅",
    "FAILURE": "❌",
    "WARNING": "⚠️",
    "INFO": "ℹ️",
    "PROGRESS": "🔄",
    "COMPLETE": "🎉",
    "ERROR": "💥",
    "WAITING": "⏳",
    "DOWNLOAD": "⬇️",
    "UPLOAD": "⬆️",
    "COMMAND": "💻",
    "SERVER": "🖥️",
    "NETWORK": "🌐",
    "SECURITY": "🔒",
    "SETTINGS": "⚙️"
}

ENHANCED_LOG_BUFFER_SIZE = 1000  # Number of log entries to buffer before flushing
MAX_OUTPUT_LENGTH = 4096  # Maximum length for output truncation
MAX_RESULT_LENGTH = 4096  # Maximum length for result truncation

STATE_FILE_EXTENSION = '.json'  # Default extension for state files 