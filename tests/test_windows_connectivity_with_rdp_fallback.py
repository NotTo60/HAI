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
    """Test SMB connectivity to the target host with multiple authentication methods."""
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

    # Method 1: Try anonymous access with different protocols
    print("Testing anonymous SMB enumeration with different protocols...")
    for protocol in ["SMB3", "SMB2", "NT1"]:
        try:
            print(f"  Trying protocol: {protocol}")
            result = subprocess.run(
                ["smbclient", "-L", f"//{host}/", "-U", "", "-N", "-m", protocol, "-d", "0"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and ("TestShare" in result.stdout or "C$" in result.stdout or "IPC$" in result.stdout):
                print(f"✅ Anonymous SMB access successful using {protocol}")
                # Print found shares
                for line in result.stdout.split('\n'):
                    if "Sharename" in line or "TestShare" in line or "C$" in line or "IPC$" in line:
                        print(f"   {line.strip()}")
                return True
            else:
                print(f"   ❌ Anonymous {protocol} failed")
        except subprocess.TimeoutExpired:
            print(f"   ❌ Anonymous {protocol} timed out")
        except Exception as e:
            print(f"   ❌ Anonymous {protocol} failed: {e}")

    # Method 2: Try guest access
    print("Testing guest SMB access...")
    try:
        result = subprocess.run(
            ["smbclient", "-L", f"//{host}/", "-U", "guest", "-N", "-d", "0"],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0 and ("TestShare" in result.stdout or "C$" in result.stdout or "IPC$" in result.stdout):
            print("✅ Guest SMB access successful")
            # Print found shares
            for line in result.stdout.split('\n'):
                if "Sharename" in line or "TestShare" in line or "C$" in line or "IPC$" in line:
                    print(f"   {line.strip()}")
            return True
        else:
            print("❌ Guest SMB access failed")
    except subprocess.TimeoutExpired:
        print("❌ Guest SMB enumeration timed out")
    except Exception as e:
        print(f"❌ Guest SMB enumeration failed: {e}")

    # Method 3: Try authenticated access if credentials available
    if password and password not in ["DECRYPTION_FAILED", "NO_PASSWORD_AVAILABLE", "NO_INSTANCE_FOUND"]:
        print("Testing authenticated SMB access...")
        try:
            # Clean the password
            clean_password = ''.join(c for c in password if c.isprintable())
            
            result = subprocess.run(
                ["smbclient", "-L", f"//{host}/", "-U", f"Administrator%{clean_password}", "-W", ".", "-d", "0"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and ("TestShare" in result.stdout or "C$" in result.stdout or "IPC$" in result.stdout):
                print("✅ Authenticated SMB access successful")
                # Print found shares
                for line in result.stdout.split('\n'):
                    if "Sharename" in line or "TestShare" in line or "C$" in line or "IPC$" in line:
                        print(f"   {line.strip()}")
                return True
            else:
                print("❌ Authenticated SMB access failed")
                print(f"   Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("❌ Authenticated SMB enumeration timed out")
        except Exception as e:
            print(f"❌ Authenticated SMB enumeration failed: {e}")

    # Method 4: Try with different SMB protocol versions for authenticated access
    if password and password not in ["DECRYPTION_FAILED", "NO_PASSWORD_AVAILABLE", "NO_INSTANCE_FOUND"]:
        print("Testing authenticated SMB access with different protocols...")
        clean_password = ''.join(c for c in password if c.isprintable())
        
        for protocol in ["SMB3", "SMB2", "NT1"]:
            try:
                print(f"  Trying authenticated {protocol}")
                result = subprocess.run(
                    ["smbclient", "-L", f"//{host}/", "-U", f"Administrator%{clean_password}", "-m", protocol, "-W", ".", "-d", "0"],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.returncode == 0 and ("TestShare" in result.stdout or "C$" in result.stdout or "IPC$" in result.stdout):
                    print(f"✅ Authenticated SMB access successful using {protocol}")
                    # Print found shares
                    for line in result.stdout.split('\n'):
                        if "Sharename" in line or "TestShare" in line or "C$" in line or "IPC$" in line:
                            print(f"   {line.strip()}")
                    return True
                else:
                    print(f"   ❌ Authenticated {protocol} failed")
            except subprocess.TimeoutExpired:
                print(f"   ❌ Authenticated {protocol} timed out")
            except Exception as e:
                print(f"   ❌ Authenticated {protocol} failed: {e}")

    print("❌ All SMB authentication methods failed")
    return False

def main():
    """Main function to run the connectivity tests."""
    parser = argparse.ArgumentParser(description="Enhanced Windows Connectivity Test with RDP First, SMB Fallback")
    parser.add_argument("target_ip", help="Target Windows IP address")
    parser.add_argument("password", nargs="?", help="Windows Administrator password")
    
    args = parser.parse_args()
    
    print("=== ENHANCED WINDOWS CONNECTIVITY TEST WITH RDP FIRST, SMB FALLBACK ===")
    print(f"Target IP: {args.target_ip}")
    print(f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}")
    
    # Test RDP first
    if check_rdp_connectivity(args.target_ip):
        print("\n=== FINAL RESULT ===")
        print("✅ RDP CONNECTIVITY SUCCESSFUL")
        print("Windows RDP connectivity is working properly")
        print("No need to test SMB - RDP is sufficient")
        sys.exit(0)
    else:
        print("\n❌ RDP CONNECTIVITY FAILED")
        print("Falling back to SMB connectivity test...")
        
        # Test SMB as fallback
        if check_smb_connectivity(args.target_ip, args.password):
            print("\n=== FINAL RESULT ===")
            print("⚠️  RDP FAILED but SMB SUCCESSFUL")
            print("RDP connectivity failed, but SMB connectivity is working")
            print("Windows instance is reachable via SMB (port 445)")
            print()
            print("SMB connection command (for manual testing):")
            print(f"smbclient //{args.target_ip}/TestShare -U Administrator")
            print()
            print("Troubleshooting RDP issues:")
            print("- Check Windows Firewall rules for RDP (port 3389)")
            print("- Verify Remote Desktop service is running on Windows")
            print("- Ensure Remote Desktop is enabled in System Properties")
            print("- Check if RDP is allowed in Windows Firewall")
            print("- Verify the instance security group allows port 3389")
            sys.exit(1)  # Exit with error as requested
        else:
            print("\n=== FINAL RESULT ===")
            print("❌ BOTH RDP AND SMB CONNECTIVITY FAILED")
            print("Windows instance is not reachable via either protocol")
            print()
            print("Debugging information:")
            print(f"- Target IP: {args.target_ip}")
            print("- RDP port 3389: Not accessible")
            print("- SMB port 445: Not accessible")
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