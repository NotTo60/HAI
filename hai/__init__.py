"""
HAI (Hybrid Attack Interface) - A Python-based hybrid connection system.

This package provides secure, resilient, and flexible remote access to diverse servers
using SSH, SMB, Impacket, and more. Supports multi-hop tunnels, fallback logic,
file transfer (with MD5 and compression), dynamic iPython magics, modular connectors,
enhanced logging, state management, threaded operations, and centralized constants management.

Example usage:
    from hai import connect_with_fallback, upload_file, run_command
    from hai import ServerEntry
    
    # Create server entry
    server = ServerEntry(
        hostname="test-server",
        ip="192.168.1.100",
        user="admin",
        password="password123",  # pragma: allowlist secret
        connection_method="ssh"
    )
    
    # Connect with fallback
    conn = connect_with_fallback(server)
    
    # Run command
    output, error = run_command(conn, "whoami")
    
    # Upload file
    upload_file(conn, "local.txt", "/remote/remote.txt", compress=True)
    
    # Disconnect
    conn.disconnect()
"""

__version__ = "0.1.0"
__author__ = "HAI Team"
__description__ = "Hybrid Attack Interface - Multi-protocol remote access system"

# Import main components
from .core import (
    connect_with_fallback,
    upload_file,
    download_file,
    run_command,
    run_commands,
    ServerEntry,
    TunnelRoute,
    TunnelHop,
    filter_servers
)

from .core.threaded_operations import (
    run_command_on_servers,
    run_commands_on_servers,
    upload_file_to_servers,
    download_file_from_servers
)

from .utils import (
    get_logger,
    get_enhanced_logger
)

__all__ = [
    # Core functionality
    'connect_with_fallback',
    'upload_file',
    'download_file',
    'run_command',
    'run_commands',
    'ServerEntry',
    'TunnelRoute',
    'TunnelHop',
    'filter_servers',
    
    # Threaded operations
    'run_command_on_servers',
    'run_commands_on_servers',
    'upload_file_to_servers',
    'download_file_from_servers',
    
    # Utilities
    'get_logger',
    'get_enhanced_logger',
    
    # Version info
    '__version__',
    '__author__',
    '__description__'
] 