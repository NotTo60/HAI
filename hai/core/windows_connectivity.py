"""
Windows Connectivity Module for HAI

This module provides comprehensive Windows connectivity testing with RDP fallback
functionality, integrated into the HAI project structure.
"""

import socket
import subprocess
import time
from typing import Optional, Dict, Any, Tuple
from ..utils.logger import get_logger
from ..utils.constants import DEFAULT_TIMEOUT
from ..core.server_schema import ServerEntry

logger = get_logger("windows_connectivity")


class WindowsConnectivityTester:
    """Windows connectivity tester with SMB and RDP fallback."""
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.logger = get_logger("windows_connectivity_tester")
    
    def test_port_connectivity(self, host: str, port: int, timeout: Optional[int] = None) -> bool:
        """Test if a port is reachable."""
        if timeout is None:
            timeout = self.timeout
            
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            self.logger.error(f"Error testing port {port} on {host}: {e}")
            return False
    
    def test_smb_connectivity(self, server: ServerEntry) -> Dict[str, Any]:
        """Test SMB connectivity to a Windows server."""
        self.logger.info(f"Testing SMB connectivity to {server.hostname} ({server.ip})")
        
        result = {
            "success": False,
            "protocol": "smb",
            "port": 445,
            "details": {},
            "error": None
        }
        
        # Test port connectivity
        if not self.test_port_connectivity(server.ip, 445, 5):
            result["error"] = "Port 445 not reachable"
            return result
        
        result["details"]["port_open"] = True
        
        # Test SMB enumeration
        try:
            # Try anonymous access first
            cmd = ["smbclient", "-L", f"//{server.ip}/", "-U", "", "-N", "-d", "0"]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            
            if process.returncode == 0 and ("TestShare" in process.stdout or "C$" in process.stdout):
                result["success"] = True
                result["details"]["access_method"] = "anonymous"
                result["details"]["shares"] = [line.strip() for line in process.stdout.split('\n') 
                                             if "Sharename" in line or "TestShare" in line or "C$" in line]
                self.logger.info(f"SMB anonymous access successful to {server.hostname}")
                return result
            
            # Try authenticated access if credentials available
            if server.password and server.password not in ["DECRYPTION_FAILED", "NO_PASSWORD_AVAILABLE", "NO_INSTANCE_FOUND"]:
                clean_password = ''.join(c for c in server.password if c.isprintable())
                cmd = ["smbclient", "-L", f"//{server.ip}/", "-U", f"{server.user}%{clean_password}", "-d", "0"]
                process = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                
                if process.returncode == 0 and ("TestShare" in process.stdout or "C$" in process.stdout):
                    result["success"] = True
                    result["details"]["access_method"] = "authenticated"
                    result["details"]["shares"] = [line.strip() for line in process.stdout.split('\n') 
                                                 if "Sharename" in line or "TestShare" in line or "C$" in line]
                    self.logger.info(f"SMB authenticated access successful to {server.hostname}")
                    return result
            
            result["error"] = "SMB enumeration failed"
            result["details"]["stdout"] = process.stdout
            result["details"]["stderr"] = process.stderr
            
        except subprocess.TimeoutExpired:
            result["error"] = "SMB enumeration timed out"
        except FileNotFoundError:
            result["error"] = "smbclient not found"
        except Exception as e:
            result["error"] = f"SMB test failed: {e}"
        
        return result
    
    def test_rdp_connectivity(self, server: ServerEntry) -> Dict[str, Any]:
        """Test RDP connectivity to a Windows server."""
        self.logger.info(f"Testing RDP connectivity to {server.hostname} ({server.ip})")
        
        result = {
            "success": False,
            "protocol": "rdp",
            "port": 3389,
            "details": {},
            "error": None
        }
        
        # Test port connectivity
        if not self.test_port_connectivity(server.ip, 3389, 5):
            result["error"] = "Port 3389 not reachable"
            return result
        
        result["details"]["port_open"] = True
        
        # Test RDP connection attempt
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result_code = sock.connect_ex((server.ip, 3389))
            sock.close()
            
            if result_code == 0:
                result["success"] = True
                result["details"]["connection_test"] = "successful"
                self.logger.info(f"RDP connectivity successful to {server.hostname}")
            else:
                result["error"] = "RDP connection test failed"
                result["details"]["connection_test"] = "failed"
                
        except Exception as e:
            result["error"] = f"RDP test failed: {e}"
        
        return result
    
    def test_windows_connectivity(self, server: ServerEntry) -> Dict[str, Any]:
        """Test Windows connectivity with SMB first, then RDP fallback."""
        self.logger.info(f"Starting Windows connectivity test for {server.hostname} ({server.ip})")
        
        # Test SMB first
        smb_result = self.test_smb_connectivity(server)
        
        if smb_result["success"]:
            self.logger.info(f"SMB connectivity successful to {server.hostname}")
            return {
                "overall_success": True,
                "primary_protocol": "smb",
                "fallback_used": False,
                "smb_result": smb_result,
                "rdp_result": None
            }
        
        # SMB failed, test RDP as fallback
        self.logger.info(f"SMB failed for {server.hostname}, testing RDP fallback")
        rdp_result = self.test_rdp_connectivity(server)
        
        if rdp_result["success"]:
            self.logger.warning(f"SMB failed but RDP successful for {server.hostname}")
            return {
                "overall_success": True,
                "primary_protocol": "rdp",
                "fallback_used": True,
                "smb_result": smb_result,
                "rdp_result": rdp_result
            }
        
        # Both protocols failed
        self.logger.error(f"Both SMB and RDP failed for {server.hostname}")
        return {
            "overall_success": False,
            "primary_protocol": None,
            "fallback_used": True,
            "smb_result": smb_result,
            "rdp_result": rdp_result
        }


def check_windows_connectivity(server: ServerEntry, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Convenience function to test Windows connectivity."""
    tester = WindowsConnectivityTester(timeout)
    return tester.test_windows_connectivity(server)


def check_multiple_windows_servers(servers: list[ServerEntry], timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Test connectivity to multiple Windows servers."""
    tester = WindowsConnectivityTester(timeout)
    results = {
        "total_servers": len(servers),
        "successful": 0,
        "failed": 0,
        "smb_only": 0,
        "rdp_fallback": 0,
        "both_failed": 0,
        "server_results": {}
    }
    
    for server in servers:
        if server.connection_method not in ["smb"] or server.os != "windows":
            continue
            
        result = tester.test_windows_connectivity(server)
        results["server_results"][server.hostname] = result
        
        if result["overall_success"]:
            results["successful"] += 1
            if result["fallback_used"]:
                results["rdp_fallback"] += 1
            else:
                results["smb_only"] += 1
        else:
            results["failed"] += 1
            results["both_failed"] += 1
    
    return results 