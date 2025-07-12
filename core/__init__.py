"""
Core module for HAI (Hybrid Attack Interface).

This module provides the main functionality:
- Connection management: Multi-protocol connections
- File transfer: Upload/download with compression
- Command execution: Remote command execution
- Threaded operations: Parallel operations on multiple servers
- Server schema: Data models for server configuration
- Tunnel building: Multi-hop tunnel support
"""

from .connection_manager import connect_with_fallback
from .file_transfer import upload_file, download_file, upload_files, download_files
from .command_runner import run_command, run_commands
from .threaded_operations import (
    run_command_on_servers,
    run_commands_on_servers,
    upload_file_to_servers,
    download_file_from_servers,
    custom_operation_on_servers
)
from .server_schema import ServerEntry, TunnelRoute, TunnelHop
from .tunnel_builder import TunnelBuilder

__all__ = [
    'connect_with_fallback',
    'upload_file',
    'download_file', 
    'upload_files',
    'download_files',
    'run_command',
    'run_commands',
    'run_command_on_servers',
    'run_commands_on_servers',
    'upload_file_to_servers',
    'download_file_from_servers',
    'custom_operation_on_servers',
    'ServerEntry',
    'TunnelRoute',
    'TunnelHop',
    'TunnelBuilder'
] 