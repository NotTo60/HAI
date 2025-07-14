#!/usr/bin/env python3
"""
Windows Connectivity Example

This example demonstrates how to use the Windows connectivity module
with RDP fallback functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hai.core.windows_connectivity import (
    WindowsConnectivityTester,
    check_windows_connectivity,
    check_multiple_windows_servers
)
from hai.core.server_schema import ServerEntry
from hai.utils.logger import get_logger

logger = get_logger("windows_connectivity_example")


def create_test_servers():
    """Create test server entries for demonstration."""
    return [
        ServerEntry(
            hostname="windows-server-1",
            ip="192.168.1.100",
            dns="server1.local",
            location="test",
            user="Administrator",
            password="testpass123",  # pragma: allowlist secret
            ssh_key=None,
            connection_method="smb",
            port=445,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        ),
        ServerEntry(
            hostname="windows-server-2",
            ip="192.168.1.101",
            dns="server2.local",
            location="test",
            user="Administrator",
            password="testpass456",  # pragma: allowlist secret
            ssh_key=None,
            connection_method="smb",
            port=445,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        ),
        ServerEntry(
            hostname="linux-server",
            ip="192.168.1.102",
            dns="server3.local",
            location="test",
            user="admin",
            password="testpass789",  # pragma: allowlist secret
            ssh_key=None,
            connection_method="ssh",
            port=22,
            active=True,
            grade="important",
            tool="test",
            os="linux",
            tunnel_routes=[]
        )
    ]


def example_single_server_test():
    """Example of testing connectivity to a single Windows server."""
    print("=== Single Server Connectivity Test ===")
    
    # Create a test server
    server = ServerEntry(
        hostname="test-windows-server",
        ip="192.168.1.100",
        dns="test.local",
        location="test",
        user="Administrator",
        password="testpass",  # pragma: allowlist secret
        ssh_key=None,
        connection_method="smb",
        port=445,
        active=True,
        grade="important",
        tool="test",
        os="windows",
        tunnel_routes=[]
    )
    
    # Test connectivity
    result = check_windows_connectivity(server, timeout=30)
    
    print(f"Server: {server.hostname} ({server.ip})")
    print(f"Overall Success: {result['overall_success']}")
    print(f"Primary Protocol: {result['primary_protocol']}")
    print(f"Fallback Used: {result['fallback_used']}")
    
    if result['smb_result']:
        print(f"SMB Success: {result['smb_result']['success']}")
        if result['smb_result']['error']:
            print(f"SMB Error: {result['smb_result']['error']}")
    
    if result['rdp_result']:
        print(f"RDP Success: {result['rdp_result']['success']}")
        if result['rdp_result']['error']:
            print(f"RDP Error: {result['rdp_result']['error']}")
    
    print()


def example_multiple_servers_test():
    """Example of testing connectivity to multiple Windows servers."""
    print("=== Multiple Servers Connectivity Test ===")
    
    # Create test servers
    servers = create_test_servers()
    
    # Test connectivity to all servers
    results = check_multiple_windows_servers(servers, timeout=30)
    
    print(f"Total Servers: {results['total_servers']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"SMB Only: {results['smb_only']}")
    print(f"RDP Fallback: {results['rdp_fallback']}")
    print(f"Both Failed: {results['both_failed']}")
    print()
    
    # Print detailed results for each server
    for hostname, result in results['server_results'].items():
        print(f"Server: {hostname}")
        print(f"  Success: {result['overall_success']}")
        print(f"  Protocol: {result['primary_protocol']}")
        print(f"  Fallback: {result['fallback_used']}")
        print()


def example_detailed_testing():
    """Example of detailed testing with the WindowsConnectivityTester class."""
    print("=== Detailed Testing Example ===")
    
    # Create a test server
    server = ServerEntry(
        hostname="detailed-test-server",
        ip="192.168.1.100",
        dns="test.local",
        location="test",
        user="Administrator",
        password="testpass",  # pragma: allowlist secret
        ssh_key=None,
        connection_method="smb",
        port=445,
        active=True,
        grade="important",
        tool="test",
        os="windows",
        tunnel_routes=[]
    )
    
    # Create tester instance
    tester = WindowsConnectivityTester(timeout=30)
    
    # Test SMB connectivity
    print("Testing SMB connectivity...")
    smb_result = tester.test_smb_connectivity(server)
    print(f"SMB Success: {smb_result['success']}")
    if smb_result['success']:
        print(f"Access Method: {smb_result['details']['access_method']}")
        if 'shares' in smb_result['details']:
            print(f"Available Shares: {smb_result['details']['shares']}")
    else:
        print(f"SMB Error: {smb_result['error']}")
    
    # Test RDP connectivity
    print("\nTesting RDP connectivity...")
    rdp_result = tester.test_rdp_connectivity(server)
    print(f"RDP Success: {rdp_result['success']}")
    if rdp_result['success']:
        print(f"Connection Test: {rdp_result['details']['connection_test']}")
    else:
        print(f"RDP Error: {rdp_result['error']}")
    
    # Test overall connectivity
    print("\nTesting overall connectivity...")
    overall_result = tester.test_windows_connectivity(server)
    print(f"Overall Success: {overall_result['overall_success']}")
    print(f"Primary Protocol: {overall_result['primary_protocol']}")
    print(f"Fallback Used: {overall_result['fallback_used']}")
    print()


def example_error_handling():
    """Example of error handling and troubleshooting."""
    print("=== Error Handling Example ===")
    
    # Create a server with invalid IP
    server = ServerEntry(
        hostname="invalid-server",
        ip="999.999.999.999",
        dns="invalid.local",
        location="test",
        user="Administrator",
        password="testpass",  # pragma: allowlist secret
        ssh_key=None,
        connection_method="smb",
        port=445,
        active=True,
        grade="important",
        tool="test",
        os="windows",
        tunnel_routes=[]
    )
    
    # Test connectivity
    result = check_windows_connectivity(server, timeout=5)
    
    print(f"Server: {server.hostname} ({server.ip})")
    print(f"Overall Success: {result['overall_success']}")
    
    if not result['overall_success']:
        print("Troubleshooting Information:")
        
        if result['smb_result'] and result['smb_result']['error']:
            print(f"  SMB Error: {result['smb_result']['error']}")
            if "Port 445 not reachable" in result['smb_result']['error']:
                print("  - Check if the server is running")
                print("  - Verify network connectivity")
                print("  - Check firewall settings")
        
        if result['rdp_result'] and result['rdp_result']['error']:
            print(f"  RDP Error: {result['rdp_result']['error']}")
            if "Port 3389 not reachable" in result['rdp_result']['error']:
                print("  - Check if RDP service is enabled")
                print("  - Verify security group rules")
                print("  - Check Windows Firewall settings")
    
    print()


def main():
    """Main function to run all examples."""
    print("Windows Connectivity Module Examples")
    print("=" * 50)
    print()
    
    try:
        # Run examples
        example_single_server_test()
        example_multiple_servers_test()
        example_detailed_testing()
        example_error_handling()
        
        print("All examples completed successfully!")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print(f"Error running examples: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 