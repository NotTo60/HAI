# Hybrid Attack Interface (HAI)

A Python-based hybrid connection system for secure, resilient, and flexible remote access to diverse servers using SSH, SMB, Impacket, and more. Supports multi-hop tunnels, fallback logic, file transfer (with MD5 and compression), dynamic iPython magics, modular connectors, **enhanced logging**, **state management**, **threaded operations**, and **centralized constants management**.

## Features
- Modular connectors: SSH, SMB, Impacket (NTLM), and easily extensible
- Multi-hop tunnel routing and automatic fallback
- File upload/download (single/multiple, with tar.gz compression and MD5 integrity)
- Protocol selection for file transfer (`sftp`, `scp`, `smb`, `ftp`, etc.)
- **Threaded operations with progress bars and statistics tracking**
- **Enhanced logging with per-server loggers and performance tracking**
- **State management for saving/loading operation states**
- **Centralized constants management for all configuration values**
- iPython magics for interactive route management (`magics/` folder)
- Logging, validation, and modular config

## Directory Structure
- `core/` — Main logic: connection manager, file transfer, command runner, server schema, **threaded operations**
- `connectors/` — Protocol connectors: SSH, SMB, Impacket, and base class
- `magics/` — iPython magics for activating/deactivating/refreshing tunnel routes
- `utils/` — Utilities: **enhanced logging**, **state management**, **constants**, MD5
- `config/` — Configuration files (e.g., SSH/Paramiko)
- `servers/` — Server inventory/configuration (JSON)
- `tests/` — Fully mocked test suite with comprehensive coverage
- `examples/` — Example scripts including threaded operations demo
- `logs/` — **Per-server and system logs with rotation**
- `state/` — **Saved operation states for resuming work**

## Quick Start

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd hai

# Install dependencies
pip install -r requirements.txt

# Run threaded operations
python cli_threaded.py --command "whoami" --servers all
```

### Basic Usage
```python
from core.threaded_operations import run_command_on_servers
from core.server_schema import ServerEntry
import json

# Load servers
with open('servers/servers.json') as f:
    servers_data = json.load(f)
    servers = [ServerEntry(**server) for server in servers_data]

# Run command on all servers with threading
results = run_command_on_servers(
    servers=servers,
    command="whoami",
    max_workers=10,
    show_progress=True
)

print(f"Success rate: {results.success_rate:.1f}%")
```

## Configuration
### Server Inventory (`servers/servers.json`)
Example entry:
```json
{
  "hostname": "server01",
  "ip": "192.168.0.10",
  "dns": "srv01.local",
  "location": "datacenter-x",
  "user": "admin",
  "password": "pass123",
  "ssh_key": "~/.ssh/id_rsa",
  "connection_method": "ssh",
  "port": 22,
  "active": true,
  "grade": "must-win",
  "tool": "custom_backdoor_tool",
  "os": "linux",
  "tunnel_routes": [
    {
      "name": "via-gateway-A",
      "active": true,
      "hops": [
        { "ip": "10.0.0.1", "user": "jump1", "method": "ssh", "port": 22 }
      ]
    },
    {
      "name": "via-vpn-B",
      "active": false,
      "hops": [
        { "ip": "10.1.1.1", "user": "vpnuser", "method": "custom", "tool": "myvpn" }
      ]
    }
  ],
  "file_transfer_protocol": "sftp",
  "config": { "timeout": 42, "client_id": "test-sftp" }
}
```

### SSH/Paramiko Config (`config/paramiko_config.yaml`)
```yaml
ssh:
  timeout: 10                # Connection timeout in seconds
  auth_timeout: 10           # Authentication timeout in seconds
  banner_timeout: 5          # Banner timeout in seconds
  allow_agent: true          # Use SSH agent for authentication
  look_for_keys: true        # Look for SSH keys in default locations
  compress: true             # Enable SSH compression
  missing_host_key_policy: autoadd  # Policy for unknown host keys
  client_id: HAI-Client      # Custom client identifier for Paramiko
```

## Threaded Operations with Enhanced Features

HAI supports advanced threaded operations with integrated logging, state management, and progress tracking.

### Basic Threaded Operations

```python
from core.threaded_operations import (
    run_command_on_servers,
    run_commands_on_servers,
    upload_file_to_servers,
    download_file_from_servers,
    custom_operation_on_servers
)

# Single command
results = run_command_on_servers(
    servers=servers,
    command="whoami",
    max_workers=10,
    show_progress=True
)

# Multiple commands
results = run_commands_on_servers(
    servers=servers,
    commands=["whoami", "pwd", "uname -a"],
    max_workers=10,
    show_progress=True
)

# File upload with compression
results = upload_file_to_servers(
    servers=servers,
    local_path="/local/file.txt",
    remote_path="/remote/file.txt",
    compress=True,
    max_workers=10,
    show_progress=True
)

# File download with decompression
results = download_file_from_servers(
    servers=servers,
    remote_path="/remote/file.txt",
    local_path="/local/file.txt",
    decompress=True,
    max_workers=10,
    show_progress=True
)
```

### Advanced Usage with ThreadedOperations Class

```python
from core.threaded_operations import ThreadedOperations
from utils.enhanced_logger import get_enhanced_logger

# Create operations manager with enhanced logging
ops = ThreadedOperations(max_workers=20)

# Run operations with comprehensive logging and state management
results = ops.run_command_on_servers(
    servers=servers,
    command="whoami",
    show_progress=True,
    description="Checking user identity across servers",
    save_state=True,  # Save state after operation
    load_state=True,  # Load state before operation
    timeout=30
)

# Access detailed logging information
logger = get_enhanced_logger("batch_operations")
logger.log_info(f"Operation completed with {results.success_rate:.1f}% success rate")

# Chain operations with state persistence
if results.successful:
    successful_servers = results.get_successful_servers()
    
    # Continue with successful servers
    follow_up_results = ops.run_commands_on_servers(
        servers=successful_servers,
        commands=["pwd", "ls -la"],
        show_progress=True,
        description="Gathering system information",
        save_state=True
    )
```

### CLI Usage

```bash
# Run command with state management
python cli_threaded.py --command "whoami" --servers all --save-state --load-state

# Run command with custom logging
python cli_threaded.py --command "ls -la" --servers server01,server02 --workers 20 --timeout 30

# Upload file with compression and state saving
python cli_threaded.py --upload /local/file.txt /remote/file.txt --servers all --compress --save-state

# Download file with decompression and state loading
python cli_threaded.py --download /remote/file.txt /local/file.txt --servers all --decompress --load-state

# Run multiple commands
python cli_threaded.py --commands "whoami,pwd,uname -a" --servers all --workers 15
```

### Results and Statistics

All threaded operations return a `BatchResult` object with comprehensive statistics:

```python
# Access detailed statistics
print(f"Success rate: {results.success_rate:.1f}%")
print(f"Execution time: {results.execution_time:.2f} seconds")
print(f"Total servers: {results.total_servers}")
print(f"Successful: {results.total_successful}")
print(f"Failed: {results.total_failed}")

# Access individual results
for result in results.successful:
    print(f"{result.server.hostname}: {result.result['output']}")

for result in results.failed:
    print(f"{result.server.hostname}: {result.error}")

# Chain operations
successful_servers = results.get_successful_servers()
failed_servers = results.get_failed_servers()

# Run different operations on each group
if successful_servers:
    # Continue with successful servers
    pass

if failed_servers:
    # Retry or alternative approach for failed servers
    pass
```

## Enhanced Logging System

HAI features a comprehensive logging system with per-server loggers, performance tracking, and structured logging.

### Features
- **Per-server logging**: Each server gets its own log file with detailed operation tracking
- **Performance logging**: Track execution times and performance metrics
- **Structured logging**: JSON-formatted logs for easy parsing and analysis
- **Log rotation**: Automatic log rotation with configurable size limits
- **Multiple log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Usage

```python
from utils.enhanced_logger import get_enhanced_logger, get_server_logger

# System-wide logger
logger = get_enhanced_logger("my_operation")

# Per-server logger
server_logger = get_server_logger("server01", "192.168.1.10")

# Log operations
logger.log_operation_start("batch_operation", 10)
logger.log_operation_complete("batch_operation", {
    "total_servers": 10,
    "successful": 8,
    "failed": 2,
    "execution_time": 45.2
})

# Server-specific logging
server_logger.log_operation("command_execution", "success", {"command": "whoami"})
server_logger.log_command("whoami", "admin", None, 1.5)
server_logger.log_file_transfer("upload", "/local/file", "/remote/file", True, 2.0)
server_logger.log_connection("connected", "ssh", 1.0)
```

### Log Structure
```
logs/
├── hai.log                    # Main system log
├── server01_192.168.1.10.log  # Per-server log
├── server02_192.168.1.11.log  # Per-server log
└── performance.log            # Performance metrics
```

## State Management

HAI provides robust state management for saving and loading operation states, allowing you to resume work from where you left off.

### Features
- **Automatic state saving**: Save state after operations with custom descriptions
- **State loading**: Resume operations from saved states
- **Backup management**: Automatic backup of state files
- **State validation**: Verify state integrity before loading
- **Cross-machine compatibility**: Load states on different machines

### Usage

```python
from utils.state_manager import save_current_state, load_saved_state, get_state_manager

# Save current state
save_current_state(description="After successful command execution")

# Load saved state
loaded_state = load_saved_state()

# Use with threaded operations
from core.threaded_operations import ThreadedOperations

ops = ThreadedOperations()
results = ops.run_command_on_servers(
    servers=servers,
    command="whoami",
    save_state=True,  # Save state after operation
    load_state=True   # Load state before operation
)
```

### State Structure
```
state/
├── hai_state_2024-01-01_12-00-00.json  # Timestamped state files
├── hai_state_2024-01-01_12-30-00.json
└── backups/                             # Automatic backups
    ├── hai_state_2024-01-01_12-00-00.json.backup
    └── hai_state_2024-01-01_12-30-00.json.backup
```

## Constants Management

All hardcoded values throughout the codebase have been replaced with centralized constants for better maintainability and consistency.

### Key Constants

```python
from utils.constants import (
    # Connection settings
    DEFAULT_SSH_PORT, DEFAULT_SMB_PORT, DEFAULT_TIMEOUT,
    
    # Threading settings
    DEFAULT_MAX_WORKERS, PROGRESS_BAR_WIDTH,
    
    # Logging settings
    LOGS_DIR, DEFAULT_LOG_LEVEL, DEFAULT_LOG_FILE,
    DEFAULT_LOG_TO_FILE, DEFAULT_LOG_TO_CONSOLE,
    DEFAULT_LOG_MAX_SIZE, DEFAULT_LOG_BACKUP_COUNT,
    
    # File transfer settings
    DEFAULT_BUFFER_SIZE, COMPRESSION_LEVEL,
    
    # Protocol strings
    PROTOCOL_SSH, PROTOCOL_SMB, PROTOCOL_IMPACKET,
    METHOD_SSH, METHOD_SMB, METHOD_IMPACKET,
    
    # OS types
    OS_LINUX, OS_WINDOWS, OS_UNKNOWN,
    
    # Server grades
    GRADE_MUST_WIN, GRADE_NICE_TO_HAVE, GRADE_OPTIONAL,
    
    # File extensions
    EXT_TAR_GZ, EXT_LOG, EXT_JSON,
    
    # Status codes
    STATUS_SUCCESS, STATUS_FAILED, STATUS_TIMEOUT
)
```

### Benefits
- **Consistency**: All components use the same values
- **Maintainability**: Change values in one place
- **Configuration**: Easy to modify behavior without code changes
- **Documentation**: Clear documentation of all configuration options

## Traditional Usage (Non-Threaded)

For single-server operations or when threading isn't needed:

```python
from core.connection_manager import connect_with_fallback
from core.file_transfer import upload_file, download_file, upload_files, download_files
from core.command_runner import run_command, run_commands
from core.server_schema import ServerEntry
import json

# Load server config
with open('servers/servers.json') as f:
    servers = json.load(f)
    # Convert dict to ServerEntry if needed

server = ... # Build ServerEntry from config
conn = connect_with_fallback(server)

# Run a command
out, err = run_command(conn, 'whoami')

# Upload a file (with compression)
upload_file(conn, 'local.txt', '/remote/remote.txt', compress=True)

# Download multiple files
download_files(conn, ['/remote/a.txt', '/remote/b.txt'], './downloads', compress=True)

conn.disconnect()
```

## iPython Magics (`magics/`)
- `activate_route <host> <route>` — Activate a tunnel route for a host
- `deactivate_route <host> <route>` — Deactivate a tunnel route
- `refresh_routes <host>` — Try to reactivate all inactive routes for a host

## Supported File Transfer Protocols
- `sftp`, `scp` (via SSH)
- `smb` (via SMBConnector)
- `ftp` (future extension)
- Specify protocol in your server JSON:
```json
{
  ...
  "file_transfer_protocol": "sftp"
}
```

## Fallback & Multi-hop Tunnels
- Define multiple `tunnel_routes` per server
- Automatic fallback: tries each active route in order
- Each route can have multiple hops (jump hosts, VPNs, etc.)

## Testing
- **Unit tests are fully mocked**: No real network or file transfer is performed. File transfer tests create and decompress real tar.gz files using Python's tarfile module, so the compression/decompression logic is exercised.
- **Comprehensive test coverage**: Tests cover all new features including enhanced logging, state management, constants integration, and threaded operations.
- **Test runner:**
```sh
pytest
```

## Improved Organization and Maintainability

### Code Quality Improvements
- **Eliminated code duplication**: Removed duplicate logging imports and consolidated functionality
- **Centralized configuration**: All constants moved to `utils/constants.py`
- **Enhanced error handling**: Better error messages and recovery mechanisms
- **Comprehensive testing**: Full test coverage for all new features
- **Documentation**: Complete documentation for all new functionality

### File Structure Improvements
```
hai/
├── core/
│   ├── threaded_operations.py    # Enhanced with logging and state
│   ├── connection_manager.py     # Uses constants
│   ├── file_transfer.py          # Uses constants
│   ├── command_runner.py         # Uses constants
│   ├── server_schema.py          # Uses constants
│   └── tunnel_builder.py         # Uses constants
├── connectors/
│   ├── ssh_connector.py          # Uses constants
│   ├── smb_connector.py          # Uses constants
│   └── impacket_wrapper.py       # Uses constants
├── utils/
│   ├── constants.py              # All constants centralized
│   ├── enhanced_logger.py        # Advanced logging system
│   ├── state_manager.py          # State persistence
│   ├── logger.py                 # Basic logging (legacy)
│   └── md5sum.py                 # Uses constants
├── logs/                         # Per-server and system logs
├── state/                        # Saved operation states
├── tests/                        # Comprehensive test suite
│   ├── test_threaded_operations.py  # Enhanced with new features
│   └── test_hai.py                  # Enhanced with new features
└── examples/                     # Updated examples
```

### Migration Guide
If you're upgrading from an older version:

1. **Update imports**: Replace `from utils.logger import get_logger` with `from utils.enhanced_logger import get_enhanced_logger`
2. **Use constants**: Replace hardcoded values with constants from `utils.constants`
3. **Enable state management**: Add `save_state=True` and `load_state=True` to threaded operations
4. **Update logging**: Use the new logging methods for better tracking

## CLI Usage: Direct Connect

You can now connect to a server directly from the command line without using servers.json:

```
python -m hai.connect --host <hostname_or_ip> --port <port> --user <username> --password <password> --method <ssh|smb|impacket>
```

This will initiate a connection using the specified parameters.

## Connector Usage: Instance vs Class Method

Each connector (SSH, SMB, Impacket) supports two ways to connect:

### 1. Instance Method (`connect(self)`)
Create an object, then call `connect()`:
```python
from connectors.ssh_connector import SSHConnector
ssh = SSHConnector(host="1.2.3.4", port=22, user="me", password="pw")
ssh.connect()
# ... use ssh ...
ssh.disconnect()
```

### 2. Class Method (`@classmethod connect_cls`)
Call `connect_cls` directly on the class for a one-liner:
```python
from connectors.ssh_connector import SSHConnector
ssh = SSHConnector.connect_cls(host="1.2.3.4", port=22, user="me", password="pw")
# ... use ssh ...
ssh.disconnect()
```

- The class method will instantiate the connector, connect, and return the connected instance.
- The instance method gives you more control if you want to set more attributes before connecting.

This pattern works for all connectors:
- `SSHConnector.connect_cls(...)`
- `SMBConnector.connect_cls(...)`
- `ImpacketWrapper.connect_cls(...)`

## Extending
- Add new connectors in `connectors/` (subclass `BaseConnector`)
- Implement new file transfer protocols in `core/file_transfer.py`
- Add new iPython magics in `magics/`
- **Extend logging**: Add new log types in `utils/enhanced_logger.py`
- **Add constants**: Define new constants in `utils/constants.py`
- **Enhance state management**: Extend state persistence in `utils/state_manager.py`

## Dependencies

The project requires the following Python packages:

```
pydantic>=1.10          # Data validation and settings management
paramiko>=3.0           # SSH protocol implementation
impacket>=0.10          # Network protocol library
ipython>=8.0            # Interactive Python shell
pyyaml>=6.0             # YAML configuration files
tqdm>=4.64              # Progress bars for threaded operations
concurrent-futures>=3.1.1  # Threading and concurrency utilities
threading>=3.0          # Threading support
json>=2.0               # JSON serialization
datetime>=4.0           # Date and time utilities
pathlib>=1.0            # Path manipulation
logging>=0.5            # Logging framework
tarfile>=3.0            # Archive file handling
gzip>=1.0               # Compression utilities
hashlib>=3.0            # Cryptographic hashing
os>=1.0                 # Operating system interface
sys>=1.0                # System-specific parameters
time>=1.0               # Time-related functions
functools>=1.0          # Higher-order functions
typing>=3.7             # Type hints
dataclasses>=3.7        # Data classes
```

## License

MIT License 