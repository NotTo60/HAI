# Hybrid Attack Interface (HAI)

A Python-based hybrid connection system for secure, resilient, and flexible remote access to diverse servers using SSH, SMB, Impacket, and more. Supports multi-hop tunnels, fallback logic, file transfer (with MD5 and compression), dynamic iPython magics, and modular connectors.

## Features
- Modular connectors: SSH, SMB, Impacket (NTLM), and easily extensible
- Multi-hop tunnel routing and automatic fallback
- File upload/download (single/multiple, with tar.gz compression and MD5 integrity)
- Protocol selection for file transfer (`sftp`, `scp`, `smb`, `ftp`, etc.)
- iPython magics for interactive route management (`magics/` folder)
- Logging, validation, and modular config

## Directory Structure
- `core/` — Main logic: connection manager, file transfer, command runner, server schema
- `connectors/` — Protocol connectors: SSH, SMB, Impacket, and base class
- `magics/` — iPython magics for activating/deactivating/refreshing tunnel routes
- `utils/` — Utilities: logging, MD5
- `config/` — Configuration files (e.g., SSH/Paramiko)
- `servers/` — Server inventory/configuration (JSON)
- `tests/` — Fully mocked test suite

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

## Usage Example
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
- **Test runner:**
```sh
pytest
```

## Extending
- Add new connectors in `connectors/` (subclass `BaseConnector`)
- Implement new file transfer protocols in `core/file_transfer.py`
- Add new iPython magics in `magics/`

---
MIT License 