#!/usr/bin/env python3
"""
Demo script showcasing all implemented features of HAI.

This script demonstrates:
- Multi-protocol connections (SSH, SMB, Impacket, FTP)
- File transfer with compression and MD5 verification
- Threaded operations with progress tracking
- State management and persistence
- Enhanced logging
- Error handling and fallback logic
"""

import json
import tempfile
import os
from pathlib import Path

# Import HAI components
from core.server_schema import ServerEntry, TunnelRoute, TunnelHop
from core.threaded_operations import (
    run_command_on_servers,
    upload_file_to_servers,
    download_file_from_servers
)
from utils.enhanced_logger import get_enhanced_logger, log_performance
from utils.state_manager import get_state_manager, save_current_state

def create_demo_servers():
    """Create demo server configurations."""
    servers = []
    
    # SSH server
    ssh_server = ServerEntry(
        hostname="demo-ssh",
        ip="192.168.1.100",
        user="admin",
        password="password123",  # pragma: allowlist secret
        connection_method="ssh",
        port=22,
        active=True,
        grade="important",
        os="linux",
        tunnel_routes=[
            TunnelRoute(
                name="direct",
                active=True,
                hops=[
                    TunnelHop(
                        ip="192.168.1.100",
                        user="admin",
                        method="ssh",
                        port=22
                    )
                ]
            )
        ],
        file_transfer_protocol="sftp"
    )
    servers.append(ssh_server)
    
    # SMB server
    smb_server = ServerEntry(
        hostname="demo-smb",
        ip="192.168.1.101",
        user="Administrator",
        password="password123",  # pragma: allowlist secret
        connection_method="smb",
        port=445,
        active=True,
        grade="important",
        os="windows",
        tunnel_routes=[
            TunnelRoute(
                name="direct",
                active=True,
                hops=[
                    TunnelHop(
                        ip="192.168.1.101",
                        user="Administrator",
                        method="smb",
                        port=445
                    )
                ]
            )
        ],
        file_transfer_protocol="smb"
    )
    servers.append(smb_server)
    
    # Impacket server
    impacket_server = ServerEntry(
        hostname="demo-impacket",
        ip="192.168.1.102",
        user="Administrator",
        password="password123",  # pragma: allowlist secret
        connection_method="custom",
        port=445,
        active=True,
        grade="important",
        os="windows",
        tunnel_routes=[
            TunnelRoute(
                name="direct",
                active=True,
                hops=[
                    TunnelHop(
                        ip="192.168.1.102",
                        user="Administrator",
                        method="custom",
                        port=445
                    )
                ]
            )
        ],
        file_transfer_protocol="smb"
    )
    servers.append(impacket_server)
    
    # FTP server
    ftp_server = ServerEntry(
        hostname="demo-ftp",
        ip="192.168.1.103",
        user="ftpuser",
        password="ftppass",  # pragma: allowlist secret
        connection_method="ftp",
        port=21,
        active=True,
        grade="important",
        os="linux",
        tunnel_routes=[
            TunnelRoute(
                name="direct",
                active=True,
                hops=[
                    TunnelHop(
                        ip="192.168.1.103",
                        user="ftpuser",
                        method="ftp",
                        port=21
                    )
                ]
            )
        ],
        file_transfer_protocol="ftp"
    )
    servers.append(ftp_server)
    
    return servers

def demo_basic_operations():
    """Demonstrate basic operations."""
    print("="*60)
    print("DEMO: Basic Operations")
    print("="*60)
    
    servers = create_demo_servers()
    logger = get_enhanced_logger("demo")
    
    # Demo 1: Run command on multiple servers
    print("\n1. Running command on multiple servers...")
    try:
        results = run_command_on_servers(
            servers=servers,
            command="whoami",
            show_progress=True,
            description="Running whoami command",
            save_state=True
        )
        
        print(f"Results: {results.total_successful}/{results.total_servers} successful")
        print(f"Success rate: {results.success_rate:.1f}%")
        
    except Exception as e:
        print(f"Command execution failed: {e}")
    
    # Demo 2: File upload with compression
    print("\n2. Uploading files with compression...")
    try:
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("This is a test file for HAI demo\n" * 10)
            test_file = f.name
        
        results = upload_file_to_servers(
            servers=servers,
            local_path=test_file,
            remote_path="/tmp/hai_demo.txt",
            compress=True,
            show_progress=True,
            description="Uploading demo file"
        )
        print(f"Upload results: {results.total_successful}/{results.total_servers} successful")
        # Show FTP result
        ftp_result = [r for r in results.results if r.server.connection_method == "ftp"]
        if ftp_result:
            print(f"FTP upload result: {ftp_result[0].success}")
        
        # Clean up
        os.unlink(test_file)
        
    except Exception as e:
        print(f"File upload failed: {e}")
    
    # Demo 3: File download
    print("\n3. Downloading files...")
    try:
        download_dir = tempfile.mkdtemp()
        
        results = download_file_from_servers(
            servers=servers,
            remote_path="/tmp/hai_demo.txt",
            local_path=os.path.join(download_dir, "downloaded.txt"),
            decompress=True,
            show_progress=True,
            description="Downloading demo file"
        )
        print(f"Download results: {results.total_successful}/{results.total_servers} successful")
        # Show FTP result
        ftp_result = [r for r in results.results if r.server.connection_method == "ftp"]
        if ftp_result:
            print(f"FTP download result: {ftp_result[0].success}")
        
        # Clean up
        import shutil
        shutil.rmtree(download_dir)
        
    except Exception as e:
        print(f"File download failed: {e}")

def demo_state_management():
    """Demonstrate state management features."""
    print("\n" + "="*60)
    print("DEMO: State Management")
    print("="*60)
    
    state_manager = get_state_manager()
    
    # Create a new state
    print("\n1. Creating new system state...")
    state = state_manager.create_new_state("Demo state for HAI features")
    print(f"Created state with ID: {state.metadata.created_at}")
    
    # Update operation state
    print("\n2. Updating operation state...")
    state_manager.update_operation_state(
        operation_id="demo_op_001",
        operation_type="command_execution",
        servers=["demo-ssh", "demo-smb"],
        successful=["demo-ssh"],
        failed=["demo-smb"],
        status="completed"
    )
    print("Operation state updated")
    
    # Save state
    print("\n3. Saving state...")
    save_current_state("Demo state saved successfully")
    print("State saved")
    
    # Load state
    print("\n4. Loading state...")
    try:
        loaded_state = state_manager.load_state("hai_state")
        print(f"Loaded state with {len(loaded_state)} entries")
    except Exception as e:
        print(f"State loading failed: {e}")

def demo_enhanced_logging():
    """Demonstrate enhanced logging features."""
    print("\n" + "="*60)
    print("DEMO: Enhanced Logging")
    print("="*60)
    
    logger = get_enhanced_logger("demo_logging")
    
    # Log different types of messages
    print("\n1. Logging different message types...")
    logger.log_info("This is an info message")
    logger.log_warning("This is a warning message")
    logger.log_error("This is an error message")
    
    # Log with context
    print("\n2. Logging with context...")
    logger.log_info("Operation completed", {"servers": 3, "success_rate": 85.5})
    
    # Log performance metrics
    print("\n3. Logging performance metrics...")
    log_performance("demo_operation", 2.5, 3)
    
    # Log server-specific operations
    print("\n4. Logging server-specific operations...")
    from utils.enhanced_logger import log_server_operation
    log_server_operation("demo-server", "file_upload", "success", "File uploaded successfully")
    log_server_operation("demo-server", "command_execution", "failed", "Connection timeout")

def demo_error_handling():
    """Demonstrate error handling and fallback logic."""
    print("\n" + "="*60)
    print("DEMO: Error Handling & Fallback Logic")
    print("="*60)
    
    # Create a server with invalid configuration
    invalid_server = ServerEntry(
        hostname="invalid-server",
        ip="999.999.999.999",  # Invalid IP
        user="admin",
        password="password123",  # pragma: allowlist secret
        connection_method="ssh",
        active=True,
        grade="low-priority"
    )
    
    print("\n1. Testing connection to invalid server...")
    try:
        from core.connection_manager import connect_with_fallback
        conn = connect_with_fallback(invalid_server)
        print("Connection successful (unexpected)")
    except Exception as e:
        print(f"Connection failed as expected: {e}")
    
    # Test with multiple routes (some invalid)
    print("\n2. Testing fallback logic...")
    servers_with_fallback = create_demo_servers()
    for server in servers_with_fallback:
        # Add an invalid route
        invalid_route = TunnelRoute(
            name="invalid",
            active=True,
            hops=[
                TunnelHop(
                    ip="999.999.999.999",
                    user="admin",
                    method="ssh",
                    port=22
                )
            ]
        )
        server.tunnel_routes.append(invalid_route)
    
    try:
        results = run_command_on_servers(
            servers=servers_with_fallback,
            command="echo 'test'",
            show_progress=True,
            description="Testing fallback logic"
        )
        print(f"Fallback test results: {results.total_successful}/{results.total_servers} successful")
    except Exception as e:
        print(f"Fallback test failed: {e}")

def main():
    """Run all demos."""
    print("HAI (Hybrid Attack Interface) - Feature Demo")
    print("="*60)
    
    # Run all demos
    demo_basic_operations()
    demo_state_management()
    demo_enhanced_logging()
    demo_error_handling()
    
    print("\n" + "="*60)
    print("Demo completed successfully!")
    print("All implemented features have been demonstrated.")
    print("="*60)

if __name__ == "__main__":
    main() 
#
# ---
#
# Example: Using iPython Magics for Route Management
#
# In an iPython or Jupyter session, after loading your server configs:
#
# %load_ext magics.route_magics
# %list_routes demo-ssh
# %activate_route demo-ssh direct
# %deactivate_route demo-ssh direct
# %refresh_routes demo-ssh
#
# These magics allow you to interactively manage tunnel routes for any server. 