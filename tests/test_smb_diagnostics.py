#!/usr/bin/env python3
"""
SMB Configuration Validation and Diagnostics Script

This script validates Windows SMB share configurations and provides
comprehensive diagnostics for troubleshooting SMB connectivity issues.
"""

import subprocess
import sys
import os
import socket
import time
from pathlib import Path

def run_command(cmd, timeout=30):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -1, "", str(e)

def check_port_connectivity(host, port, timeout=5):
    """Check if a port is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_smb_connectivity(host, username=None, password=None):
    """Test SMB connectivity using smbclient."""
    print(f"\n=== Testing SMB Connectivity to {host} ===")
    
    # Check port 445
    print(f"1. Checking port 445 connectivity...")
    if check_port_connectivity(host, 445):
        print("   ✅ Port 445 is reachable")
    else:
        print("   ❌ Port 445 is not reachable")
        return False
    
    # Test anonymous access
    print(f"2. Testing anonymous SMB enumeration...")
    cmd = f"smbclient -L //{host}/ -U \"\" -N -d 0"
    rc, stdout, stderr = run_command(cmd)
    
    if rc == 0 and ("TestShare" in stdout or "C$" in stdout):
        print("   ✅ Anonymous access successful")
        print(f"   Shares found: {stdout}")
        return True
    else:
        print("   ❌ Anonymous access failed")
        print(f"   Error: {stderr}")
    
    # Test with credentials if provided
    if username and password:
        print(f"3. Testing authenticated access as {username}...")
        cmd = f"smbclient -L //{host}/ -U \"{username}%{password}\" -d 0"
        rc, stdout, stderr = run_command(cmd)
        
        if rc == 0 and ("TestShare" in stdout or "C$" in stdout):
            print("   ✅ Authenticated access successful")
            print(f"   Shares found: {stdout}")
            return True
        else:
            print("   ❌ Authenticated access failed")
            print(f"   Error: {stderr}")
    
    return False

def validate_smb_configuration():
    """Validate SMB configuration on the local system."""
    print("\n=== SMB Configuration Validation ===")
    
    # Check if smbclient is available
    rc, stdout, stderr = run_command("which smbclient")
    if rc != 0:
        print("❌ smbclient not found. Please install samba-client.")
        return False
    
    print("✅ smbclient is available")
    
    # Check smbclient version
    rc, stdout, stderr = run_command("smbclient -V")
    if rc == 0:
        print(f"✅ smbclient version: {stdout.strip()}")
    
    return True

def generate_smb_test_report(host, username=None, password=None):
    """Generate a comprehensive SMB test report."""
    print("\n" + "="*60)
    print("SMB CONNECTIVITY TEST REPORT")
    print("="*60)
    
    # Validate local configuration
    if not validate_smb_configuration():
        print("❌ Local SMB configuration validation failed")
        return False
    
    # Test connectivity
    success = check_smb_connectivity(host, username, password)
    
    # Generate recommendations
    print("\n=== RECOMMENDATIONS ===")
    if success:
        print("✅ SMB connectivity is working correctly!")
        print("   - The Windows SMB share is accessible")
        print("   - Authentication is working properly")
    else:
        print("❌ SMB connectivity issues detected:")
        print("   - Check Windows Firewall settings")
        print("   - Verify SMB service is running on Windows")
        print("   - Ensure TestShare is created with proper permissions")
        print("   - Check network connectivity between systems")
        print("   - Verify credentials are correct")
        print("   - Check SMB protocol version compatibility")
    
    return success

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python test_smb_diagnostics.py <target_host> [username] [password]")
        print("Example: python test_smb_diagnostics.py 192.168.1.100 Administrator mypassword")
        sys.exit(1)
    
    host = sys.argv[1]
    username = sys.argv[2] if len(sys.argv) > 2 else None
    password = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"Target host: {host}")
    if username:
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password) if password else 'None'}")
    
    success = generate_smb_test_report(host, username, password)
    
    if success:
        print("\n🎉 SMB connectivity test PASSED")
        sys.exit(0)
    else:
        print("\n💥 SMB connectivity test FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main() 