# Hybrid Attack Interface (HAI)

A Python-based hybrid connection system for secure, resilient, and flexible remote access to diverse servers using SSH, SMB, Impacket, and more. Supports multi-hop tunnels, fallback logic, file transfer (with MD5 and compression), dynamic magics, and modular connectors.

## Features
- SSH, SMB, Impacket (NTLM), and extensible connector support
- Multi-hop tunnel routing and fallback
- File upload/download (single/multiple, with tar.gz compression)
- Protocol selection for file transfer (sftp, scp, smb, ftp, etc.)
- iPython magics for interactive control
- Logging, validation, and modular config

## Setup
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration
- Edit `servers/servers.json` to define your servers, tunnels, and file transfer protocols.
- Edit `config/paramiko_config.yaml` for SSH options.

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
out, err = conn.exec_command('whoami')

# Upload a file (with compression)
upload_file(conn, 'local.txt', '/remote/remote.txt', compress=True)

# Download multiple files
download_files(conn, ['/remote/a.txt', '/remote/b.txt'], './downloads', compress=True)

conn.disconnect()
```

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

## Testing
```sh
python test_hai.py
```

## Extending
- Add new connectors in `connectors/`
- Implement new file transfer protocols in `core/file_transfer.py`

---
MIT License 