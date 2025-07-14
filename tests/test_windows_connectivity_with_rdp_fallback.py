#!/usr/bin/env python3
"""
Enhanced Windows Connectivity Test with RDP Fallback

This script tests SMB connectivity first, then falls back to RDP testing if SMB fails.
It exits with an error if both protocols fail, as requested.

Usage:
    python test_windows_connectivity_with_rdp_fallback.py <target_ip> [password]
"""

import sys
import socket
import subprocess
import time
import argparse
from typing import Optional, Tuple
import os

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
    print("\n=== TESTING RDP CONNECTIVITY ===")
    print(f"Testing RDP port 3389 connectivity to {host}...")
    
    # Test if RDP port is open
    if check_port_connectivity(host, 3389, 5):
        print("✅ RDP port 3389 is open and accessible")
        
        # Test RDP connection attempt (without actually connecting)
        print("Testing RDP connection attempt...")
        try:
            # Try to establish a TCP connection to RDP port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, 3389))
            sock.close()
            
            if result == 0:
                print("✅ RDP connection test successful")
                print("RDP connectivity is working")
                return True
            else:
                print("❌ RDP connection test failed")
                return False
        except Exception as e:
            print(f"❌ RDP connection test failed: {e}")
            return False
    else:
        print("❌ RDP port 3389 is not accessible")
        return False

def check_smb_connectivity(host: str, password: Optional[str] = None) -> bool:
    """Test SMB connectivity to the target host."""
    print("\n=== TESTING SMB CONNECTIVITY ===")
    
    # Retry loop for port 445
    max_attempts = 5
    delay_seconds = 5
    
    for attempt in range(1, max_attempts + 1):
        print(f"Testing port 445 connectivity (attempt {attempt} of {max_attempts})...")
        if check_port_connectivity(host, 445, 3):
            print("✅ Port 445 is reachable")
            break
        else:
            print("Port 445 not open yet.")
            if attempt < max_attempts:
                time.sleep(delay_seconds)
    else:
        print(f"❌ Port 445 is not reachable after {max_attempts} attempts.")
        return False

    print("Testing SMB connectivity with smbclient...")
    
    # Check if smbclient is available
    try:
        subprocess.run(["smbclient", "-V"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ smbclient not found. Please install samba-client.")
        return False

    # Try anonymous access first
    print("Testing anonymous SMB enumeration...")
    try:
        result = subprocess.run(
            ["smbclient", "-L", f"//{host}/", "-U", "", "-N", "-d", "0"],
            capture_output=True,
            text=True,
            timeout=20
        )
        
        if result.returncode == 0 and ("TestShare" in result.stdout or "C$" in result.stdout):
            print("✅ Anonymous SMB access successful")
            # Print found shares
            for line in result.stdout.split('\n'):
                if "Sharename" in line or "TestShare" in line or "C$" in line:
                    print(f"   {line.strip()}")
            return True
        else:
            print("❌ Anonymous SMB enumeration failed")
            print(f"   Error: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("❌ Anonymous SMB enumeration timed out")
    except Exception as e:
        print(f"❌ Anonymous SMB enumeration failed: {e}")

    # Try with credentials if available
    if password and password not in ["DECRYPTION_FAILED", "NO_PASSWORD_AVAILABLE", "NO_INSTANCE_FOUND"]:
        print("Testing authenticated SMB access...")
        try:
            # Clean the password
            clean_password = ''.join(c for c in password if c.isprintable())
            
            result = subprocess.run(
                ["smbclient", "-L", f"//{host}/", "-U", f"Administrator%{clean_password}", "-d", "0"],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if result.returncode == 0 and ("TestShare" in result.stdout or "C$" in result.stdout):
                print("✅ Authenticated SMB access successful")
                # Print found shares
                for line in result.stdout.split('\n'):
                    if "Sharename" in line or "TestShare" in line or "C$" in line:
                        print(f"   {line.strip()}")
                return True
            else:
                print("❌ Authenticated SMB access failed")
                print(f"   Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("❌ Authenticated SMB enumeration timed out")
        except Exception as e:
            print(f"❌ Authenticated SMB enumeration failed: {e}")

    print("❌ All SMB authentication methods failed")
    return False

def main():
    """Main function to run the connectivity tests."""
    parser = argparse.ArgumentParser(description="Enhanced Windows Connectivity Test with RDP Fallback")
    parser.add_argument("target_ip", help="Target Windows IP address")
    parser.add_argument("password", nargs="?", help="Windows Administrator password")
    
    args = parser.parse_args()
    
    print("=== ENHANCED WINDOWS CONNECTIVITY TEST WITH RDP FALLBACK ===")
    print(f"Target IP: {args.target_ip}")
    print(f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}")
    
    # Test SMB first
    if check_smb_connectivity(args.target_ip, args.password):
        print("\n=== FINAL RESULT ===")
        print("✅ SMB CONNECTIVITY SUCCESSFUL")
        print("Windows SMB connectivity is working properly")
        print("No need to test RDP - SMB is sufficient")
        sys.exit(0)
    else:
        print("\n❌ SMB CONNECTIVITY FAILED")
        print("Falling back to RDP connectivity test...")
        
        # Test RDP as fallback
        if check_rdp_connectivity(args.target_ip):
            print("\n=== FINAL RESULT ===")
            print("⚠️  SMB FAILED but RDP SUCCESSFUL")
            print("SMB connectivity failed, but RDP connectivity is working")
            print("Windows instance is reachable via RDP (port 3389)")
            print()
            print("RDP connection command (for manual testing):")
            print(f"xfreerdp /v:{args.target_ip} /u:Administrator /p:\"<password>\" /cert:ignore")
            print()
            print("Troubleshooting SMB issues:")
            print("- Check Windows Firewall rules for SMB (port 445)")
            print("- Verify SMB service is running on Windows")
            print("- Ensure TestShare is created with proper permissions")
            print("- Check Administrator password and account status")
            print("- Verify SMB protocol versions are enabled")
            sys.exit(1)  # Exit with error as requested
        else:
            print("\n=== FINAL RESULT ===")
            print("❌ BOTH SMB AND RDP CONNECTIVITY FAILED")
            print("Windows instance is not reachable via either protocol")
            print()
            print("Debugging information:")
            print(f"- Target IP: {args.target_ip}")
            print("- SMB port 445: Not accessible")
            print("- RDP port 3389: Not accessible")
            print()
            print("Possible issues:")
            print("- Windows instance may not be running")
            print("- Network connectivity issues")
            print("- Firewall blocking both ports")
            print("- Instance security groups not configured properly")
            print("- Windows services not started")
            sys.exit(1)

if __name__ == "__main__":
    main() 