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

# Ensure directories exist
for directory in [LOGS_DIR, STATE_DIR]:
    directory.mkdir(exist_ok=True)

# File paths
SERVERS_JSON_PATH = SERVERS_DIR / "servers.json"
DEFAULT_STATE_FILE = STATE_DIR / "hai_state.json"

# Logging constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default logging configuration
DEFAULT_LOG_LEVEL = "INFO"

# Threading constants
DEFAULT_MAX_WORKERS = 10
DEFAULT_TIMEOUT = 30  # seconds

# Progress bar constants
PROGRESS_BAR_WIDTH = 100

# File transfer constants
DEFAULT_COMPRESSION = True
DEFAULT_CHUNK_SIZE = 8192  # bytes
SUPPORTED_COMPRESSION_FORMATS = [".tar.gz", ".tar.bz2", ".zip"]

# Connection constants
DEFAULT_SSH_PORT = 22
DEFAULT_SMB_PORT = 445

# Supported protocols
SUPPORTED_CONNECTION_METHODS = ["ssh", "smb", "custom", "ftp", "impacket"]
SUPPORTED_FILE_TRANSFER_PROTOCOLS = ["sftp", "scp", "smb", "ftp"]
SUPPORTED_OS_TYPES = ["linux", "windows", "unknown"]

# Server grades
SERVER_GRADES = ["critical", "must-win", "important", "nice-to-have", "low-priority"]

# State persistence constants
STATE_VERSION = "1.0"
STATE_BACKUP_COUNT = 3

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

# Backup and recovery constants
BACKUP_RETENTION_DAYS = 30

# Time formats
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# Enhanced logging constants
ENHANCED_LOG_BUFFER_SIZE = 1000  # Number of log entries to buffer before flushing
MAX_OUTPUT_LENGTH = 4096  # Maximum length for output truncation
MAX_RESULT_LENGTH = 4096  # Maximum length for result truncation

# State management constants
STATE_FILE_EXTENSION = '.json'  # Default extension for state files
STATE_COMPRESSION_ENABLED = True  # Enable compression for state files
STATE_ENCRYPTION_ENABLED = True  # Enable encryption for state files

# File transfer constants
MAX_FILE_SIZE = 1024 * 1024 * 100  # 100MB max file size
CHUNK_SIZE = 8192  # Default chunk size for file transfers
RETRY_ATTEMPTS = 3  # Number of retry attempts for failed operations

# Connection constants
CONNECTION_TIMEOUT = 30  # Default connection timeout
COMMAND_TIMEOUT = 60  # Default command execution timeout
FILE_TRANSFER_TIMEOUT = 300  # Default file transfer timeout

# Security constants
ENCRYPTION_KEY_LENGTH = 32  # Length of encryption keys
HASH_ALGORITHM = "sha256"  # Default hash algorithm 