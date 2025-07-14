#!/usr/bin/env python3
"""
Test script to verify RDP fallback logic
"""

import sys
import socket
from unittest.mock import patch, MagicMock

def check_port_connectivity(host: str, port: int, timeout: int = 5) -> bool:
    """Test if a port is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error testing port {port}: {e}")
        return False

def check_rdp_connectivity(host: str) -> bool:
    """Test RDP connectivity to the target host."""
    print(f"\n=== TESTING RDP CONNECTIVITY ===")
    print(f"Testing RDP port 3389 connectivity to {host}...")
    
    # Test if RDP port is open
    if check_port_connectivity(host, 3389, 5):
        print("✅ RDP port 3389 is open and accessible")
        return True
    else:
        print("❌ RDP port 3389 is not accessible")
        return False

def check_smb_connectivity(host: str, password=None) -> bool:
    """Test SMB connectivity to the target host."""
    print(f"\n=== TESTING SMB CONNECTIVITY ===")
    
    # Test if SMB port is open
    if check_port_connectivity(host, 445, 3):
        print("✅ Port 445 is reachable")
        return True
    else:
        print("❌ Port 445 is not reachable")
        return False

def main():
    """Test the fallback logic with mock scenarios."""
    print("=== TESTING RDP FALLBACK LOGIC ===")
    
    # Test scenario 1: SMB succeeds
    print("\n--- Scenario 1: SMB succeeds ---")
    with patch('socket.socket') as mock_socket:
        mock_socket.return_value.connect_ex.return_value = 0
        mock_socket.return_value.close.return_value = None
        
        if check_smb_connectivity("192.168.1.100"):
            print("✅ SMB CONNECTIVITY SUCCESSFUL")
            print("No need to test RDP - SMB is sufficient")
            return 0
        else:
            print("❌ SMB CONNECTIVITY FAILED")
            print("Falling back to RDP connectivity test...")
            
            if check_rdp_connectivity("192.168.1.100"):
                print("⚠️  SMB FAILED but RDP SUCCESSFUL")
                return 1
            else:
                print("❌ BOTH SMB AND RDP CONNECTIVITY FAILED")
                return 1
    
    # Test scenario 2: SMB fails, RDP succeeds
    print("\n--- Scenario 2: SMB fails, RDP succeeds ---")
    with patch('socket.socket') as mock_socket:
        def mock_connect_ex(addr):
            host, port = addr
            if port == 445:  # SMB port
                return 1  # Connection failed
            elif port == 3389:  # RDP port
                return 0  # Connection succeeded
            return 1
        
        mock_socket.return_value.connect_ex.side_effect = mock_connect_ex
        mock_socket.return_value.close.return_value = None
        
        if check_smb_connectivity("192.168.1.100"):
            print("✅ SMB CONNECTIVITY SUCCESSFUL")
            return 0
        else:
            print("❌ SMB CONNECTIVITY FAILED")
            print("Falling back to RDP connectivity test...")
            
            if check_rdp_connectivity("192.168.1.100"):
                print("⚠️  SMB FAILED but RDP SUCCESSFUL")
                return 1
            else:
                print("❌ BOTH SMB AND RDP CONNECTIVITY FAILED")
                return 1
    
    # Test scenario 3: Both fail
    print("\n--- Scenario 3: Both fail ---")
    with patch('socket.socket') as mock_socket:
        mock_socket.return_value.connect_ex.return_value = 1  # All connections fail
        mock_socket.return_value.close.return_value = None
        
        if check_smb_connectivity("192.168.1.100"):
            print("✅ SMB CONNECTIVITY SUCCESSFUL")
            return 0
        else:
            print("❌ SMB CONNECTIVITY FAILED")
            print("Falling back to RDP connectivity test...")
            
            if check_rdp_connectivity("192.168.1.100"):
                print("⚠️  SMB FAILED but RDP SUCCESSFUL")
                return 1
            else:
                print("❌ BOTH SMB AND RDP CONNECTIVITY FAILED")
                return 1

if __name__ == "__main__":
    sys.exit(main()) 