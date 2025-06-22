#!/usr/bin/env python3
"""
Example script demonstrating threaded operations with HAI.

This script shows how to:
1. Run commands on multiple servers in parallel
2. Upload/download files with compression
3. Chain operations based on results
4. Handle errors and retries
"""

from pathlib import Path

from core.threaded_operations import (
    run_command_on_servers,
    run_commands_on_servers,
    upload_file_to_servers,
    download_file_from_servers,
    custom_operation_on_servers,
    ThreadedOperations
)
from core.server_schema import ServerEntry
from utils.constants import DEFAULT_MAX_WORKERS, DEFAULT_SSH_PORT

def create_sample_servers():
    """Create sample server entries for demonstration."""
    servers = [
        ServerEntry(
            hostname="server01",
            ip="192.168.1.10",
            user="admin",
            password="password123",
            connection_method="ssh",
            port=DEFAULT_SSH_PORT,
            active=True,
            grade="must-win",
            os="linux"
        ),
        ServerEntry(
            hostname="server02", 
            ip="192.168.1.11",
            user="admin",
            password="password123",
            connection_method="ssh",
            port=DEFAULT_SSH_PORT,
            active=True,
            grade="must-win",
            os="linux"
        ),
        ServerEntry(
            hostname="server03",
            ip="192.168.1.12", 
            user="admin",
            password="password123",
            connection_method="ssh",
            port=DEFAULT_SSH_PORT,
            active=True,
            grade="nice-to-have",
            os="linux"
        )
    ]
    return servers

def example_basic_command():
    """Example: Run a basic command on all servers."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Command Execution")
    print("=" * 60)
    
    servers = create_sample_servers()
    
    # Run whoami command on all servers
    results = run_command_on_servers(
        servers=servers,
        command="whoami",
        max_workers=DEFAULT_MAX_WORKERS,
        show_progress=True,
        description="Checking user identity"
    )
    
    print("\nResults:")
    print(f"  Total servers: {results.total_servers}")
    print(f"  Successful: {results.total_successful}")
    print(f"  Failed: {results.total_failed}")
    print(f"  Success rate: {results.success_rate:.1f}%")
    
    # Show individual results
    for result in results.successful:
        print(f"  ✓ {result.server.hostname}: {result.result['output'].strip()}")
    
    for result in results.failed:
        print(f"  ✗ {result.server.hostname}: {result.error}")
    
    return results

def example_multiple_commands():
    """Example: Run multiple commands on all servers."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Multiple Commands")
    print("=" * 60)
    
    servers = create_sample_servers()
    
    commands = [
        "whoami",
        "pwd", 
        "uname -a",
        "df -h"
    ]
    
    results = run_commands_on_servers(
        servers=servers,
        commands=commands,
        max_workers=DEFAULT_MAX_WORKERS,
        show_progress=True,
        description="Gathering system information"
    )
    
    print("\nResults:")
    print(f"  Total servers: {results.total_servers}")
    print(f"  Commands per server: {len(commands)}")
    print(f"  Total operations: {results.total_servers * len(commands)}")
    print(f"  Successful: {results.total_successful}")
    print(f"  Failed: {results.total_failed}")
    print(f"  Success rate: {results.success_rate:.1f}%")
    
    return results

def example_file_operations():
    """Example: File upload and download operations."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: File Operations")
    print("=" * 60)
    
    servers = create_sample_servers()
    
    # Create a test file
    test_file = Path("test_file.txt")
    test_file.write_text("This is a test file for HAI threaded operations!")
    
    try:
        # Upload file to all servers
        print("Uploading test file to all servers...")
        upload_results = upload_file_to_servers(
            servers=servers,
            local_path=str(test_file),
            remote_path="/tmp/test_file.txt",
            compress=True,
            max_workers=DEFAULT_MAX_WORKERS,
            show_progress=True,
            description="Uploading test file"
        )
        
        print(f"Upload results: {upload_results.total_successful}/{upload_results.total_servers} successful")
        
        # Download file from successful uploads
        successful_servers = upload_results.get_successful_servers()
        if successful_servers:
            print(f"\nDownloading file from {len(successful_servers)} servers...")
            download_results = download_file_from_servers(
                servers=successful_servers,
                remote_path="/tmp/test_file.txt",
                local_path="downloaded_test_file.txt",
                decompress=True,
                max_workers=DEFAULT_MAX_WORKERS,
                show_progress=True,
                description="Downloading test file"
            )
            
            print(f"Download results: {download_results.total_successful}/{download_results.total_servers} successful")
        
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()

def example_custom_operation():
    """Example: Custom operation function."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Custom Operations")
    print("=" * 60)
    
    servers = create_sample_servers()
    
    def custom_system_check(conn, check_type="basic", **kwargs):
        """Custom operation to perform system checks."""
        results = {}
        
        if check_type == "basic":
            # Basic system info
            out, err = conn.exec_command("uname -a")
            results["system_info"] = out.strip()
            
            out, err = conn.exec_command("whoami")
            results["current_user"] = out.strip()
            
        elif check_type == "detailed":
            # Detailed system check
            out, err = conn.exec_command("df -h")
            results["disk_usage"] = out.strip()
            
            out, err = conn.exec_command("free -h")
            results["memory_usage"] = out.strip()
            
            out, err = conn.exec_command("uptime")
            results["uptime"] = out.strip()
        
        return results
    
    # Run basic check
    basic_results = custom_operation_on_servers(
        servers=servers,
        operation_func=custom_system_check,
        operation_args=("basic",),
        max_workers=DEFAULT_MAX_WORKERS,
        show_progress=True,
        description="Basic system check"
    )
    
    print(f"Basic check results: {basic_results.total_successful}/{basic_results.total_servers} successful")
    
    # Run detailed check on successful basic checks
    successful_servers = basic_results.get_successful_servers()
    if successful_servers:
        detailed_results = custom_operation_on_servers(
            servers=successful_servers,
            operation_func=custom_system_check,
            operation_args=("detailed",),
            max_workers=DEFAULT_MAX_WORKERS,
            show_progress=True,
            description="Detailed system check"
        )
        
        print(f"Detailed check results: {detailed_results.total_successful}/{detailed_results.total_servers} successful")

def example_chaining_operations():
    """Example: Chaining operations based on results."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Chaining Operations")
    print("=" * 60)
    
    servers = create_sample_servers()
    
    # Step 1: Check if servers are reachable
    print("Step 1: Checking server connectivity...")
    connectivity_results = run_command_on_servers(
        servers=servers,
        command="echo 'Server is reachable'",
        max_workers=DEFAULT_MAX_WORKERS,
        show_progress=True,
        description="Connectivity check"
    )
    
    reachable_servers = connectivity_results.get_successful_servers()
    unreachable_servers = connectivity_results.get_failed_servers()
    
    print(f"  Reachable: {len(reachable_servers)} servers")
    print(f"  Unreachable: {len(unreachable_servers)} servers")
    
    # Step 2: Run system commands on reachable servers
    if reachable_servers:
        print("\nStep 2: Running system commands on reachable servers...")
        system_results = run_commands_on_servers(
            servers=reachable_servers,
            commands=["whoami", "pwd", "uname -a"],
            max_workers=DEFAULT_MAX_WORKERS,
            show_progress=True,
            description="System commands"
        )
        
        successful_system_servers = system_results.get_successful_servers()
        failed_system_servers = system_results.get_failed_servers()
        
        print(f"  System commands successful: {len(successful_system_servers)} servers")
        print(f"  System commands failed: {len(failed_system_servers)} servers")
        
        # Step 3: Run additional commands on successful servers
        if successful_system_servers:
            print("\nStep 3: Running additional commands on successful servers...")
            additional_results = run_command_on_servers(
                servers=successful_system_servers,
                command="df -h",
                max_workers=DEFAULT_MAX_WORKERS,
                show_progress=True,
                description="Disk usage check"
            )
            
            print(f"  Final successful: {additional_results.total_successful} servers")
    
    # Step 4: Retry failed servers with different approach
    if unreachable_servers:
        print(f"\nStep 4: Retrying {len(unreachable_servers)} unreachable servers...")
        retry_results = run_command_on_servers(
            servers=unreachable_servers,
            command="echo 'Retry attempt'",
            max_workers=1,  # Use fewer workers for retries
            show_progress=True,
            description="Retry unreachable servers"
        )
        
        print(f"  Retry successful: {retry_results.total_successful} servers")

def example_using_threaded_operations_class():
    """Example: Using the ThreadedOperations class directly."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Using ThreadedOperations Class")
    print("=" * 60)
    
    servers = create_sample_servers()
    
    # Create operations manager
    ops = ThreadedOperations(max_workers=DEFAULT_MAX_WORKERS)
    
    # Run multiple operations with the same manager
    print("Running multiple operations with ThreadedOperations class...")
    
    # Operation 1: Check connectivity
    connectivity_results = ops.run_command_on_servers(
        servers=servers,
        command="echo 'Connected'",
        show_progress=True,
        description="Connectivity check"
    )
    
    # Operation 2: Run commands on successful servers
    if connectivity_results.successful:
        successful_servers = connectivity_results.get_successful_servers()
        
        command_results = ops.run_commands_on_servers(
            servers=successful_servers,
            commands=["whoami", "pwd"],
            show_progress=True,
            description="User and directory info"
        )
        
        print(f"  Connectivity check: {connectivity_results.total_successful}/{connectivity_results.total_servers}")
        print(f"  Command execution: {command_results.total_successful}/{command_results.total_servers}")

def main():
    """Run all examples."""
    print("HAI Threaded Operations Examples")
    print("This script demonstrates various threaded operations capabilities.")
    print("Note: These examples use simulated servers and may not connect to real systems.")
    
    try:
        # Run examples
        example_basic_command()
        example_multiple_commands()
        example_file_operations()
        example_custom_operation()
        example_chaining_operations()
        example_using_threaded_operations_class()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED")
        print("=" * 60)
        print("These examples demonstrate the key features of HAI threaded operations:")
        print("  • Parallel execution with progress bars")
        print("  • Detailed success/failure tracking")
        print("  • Operation chaining based on results")
        print("  • Custom operation functions")
        print("  • File transfer with compression")
        print("  • Error handling and retry logic")
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"Error running examples: {e}")

if __name__ == "__main__":
    main() 