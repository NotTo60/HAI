"""
Tests for the Windows Connectivity Module

This module tests the Windows connectivity functionality with RDP fallback.
"""

import pytest
from unittest.mock import patch, MagicMock
from hai.core.windows_connectivity import (
    WindowsConnectivityTester,
    check_windows_connectivity,
    check_multiple_windows_servers
)
from hai.core.server_schema import ServerEntry
from hai.utils.constants import DEFAULT_TIMEOUT
import subprocess


class TestWindowsConnectivityTester:
    """Test the WindowsConnectivityTester class."""
    
    def test_init(self):
        """Test WindowsConnectivityTester initialization."""
        tester = WindowsConnectivityTester()
        assert tester.timeout == DEFAULT_TIMEOUT
        assert tester.logger is not None
        
        custom_tester = WindowsConnectivityTester(timeout=60)
        assert custom_tester.timeout == 60
    
    @patch('socket.socket')
    def test_test_port_connectivity_success(self, mock_socket):
        """Test successful port connectivity."""
        mock_socket.return_value.connect_ex.return_value = 0
        mock_socket.return_value.close.return_value = None
        
        tester = WindowsConnectivityTester()
        result = tester.test_port_connectivity("192.168.1.100", 445)
        
        assert result is True
        mock_socket.return_value.connect_ex.assert_called_once_with(("192.168.1.100", 445))
    
    @patch('socket.socket')
    def test_test_port_connectivity_failure(self, mock_socket):
        """Test failed port connectivity."""
        mock_socket.return_value.connect_ex.return_value = 1
        mock_socket.return_value.close.return_value = None
        
        tester = WindowsConnectivityTester()
        result = tester.test_port_connectivity("192.168.1.100", 445)
        
        assert result is False
    
    @patch('socket.socket')
    def test_test_port_connectivity_exception(self, mock_socket):
        """Test port connectivity with exception."""
        mock_socket.side_effect = Exception("Connection error")
        
        tester = WindowsConnectivityTester()
        result = tester.test_port_connectivity("192.168.1.100", 445)
        
        assert result is False
    
    @patch('subprocess.run')
    @patch.object(WindowsConnectivityTester, 'test_port_connectivity')
    def test_test_smb_connectivity_success_anonymous(self, mock_port_test, mock_run):
        """Test successful SMB connectivity with anonymous access."""
        mock_port_test.return_value = True
        
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Sharename      Type      Comment\nTestShare      Disk      Test Share\nC$             Disk      Default share"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test.local",
            location="test",
            user="Administrator",
            password="testpass",
            ssh_key=None,
            connection_method="smb",
            port=445,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        )
        
        tester = WindowsConnectivityTester()
        result = tester.test_smb_connectivity(server)
        
        assert result["success"] is True
        assert result["protocol"] == "smb"
        assert result["port"] == 445
        assert result["details"]["access_method"] == "anonymous"
        assert any("TestShare" in share for share in result["details"]["shares"])
    
    @patch('subprocess.run')
    @patch.object(WindowsConnectivityTester, 'test_port_connectivity')
    def test_test_smb_connectivity_success_authenticated(self, mock_port_test, mock_run):
        """Test successful SMB connectivity with authenticated access."""
        mock_port_test.return_value = True

        # Multiple calls for different protocols, last one succeeds (authenticated)
        mock_process_fail = MagicMock()
        mock_process_fail.returncode = 1
        mock_process_fail.stdout = ""
        mock_process_fail.stderr = "Access denied"

        mock_process_success = MagicMock()
        mock_process_success.returncode = 0
        mock_process_success.stdout = "Sharename      Type      Comment\nC$             Disk      Default share"
        mock_process_success.stderr = ""

        # Multiple failed attempts for anonymous/guest, then successful authenticated
        mock_run.side_effect = [mock_process_fail] * 6 + [mock_process_success]

        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test.local",
            location="test",
            user="Administrator",
            password="testpass",
            ssh_key=None,
            connection_method="smb",
            port=445,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        )

        tester = WindowsConnectivityTester()
        result = tester.test_smb_connectivity(server)

        assert result["success"] is True
        assert result["details"]["access_method"] == "authenticated"
    
    @patch.object(WindowsConnectivityTester, 'test_port_connectivity')
    def test_test_smb_connectivity_port_failure(self, mock_port_test):
        """Test SMB connectivity with port failure."""
        mock_port_test.return_value = False
        
        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test.local",
            location="test",
            user="Administrator",
            password="testpass",
            ssh_key=None,
            connection_method="smb",
            port=445,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        )
        
        tester = WindowsConnectivityTester()
        result = tester.test_smb_connectivity(server)
        
        assert result["success"] is False
        assert result["error"] == "Port 445 not reachable"
    
    @patch('subprocess.run')
    @patch.object(WindowsConnectivityTester, 'test_port_connectivity')
    def test_test_smb_connectivity_timeout(self, mock_port_test, mock_run):
        """Test SMB connectivity with timeout."""
        mock_port_test.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("smbclient", 15)

        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test.local",
            location="test",
            user="Administrator",
            password="testpass",
            ssh_key=None,
            connection_method="smb",
            port=445,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        )

        tester = WindowsConnectivityTester()
        result = tester.test_smb_connectivity(server)

        assert result["success"] is False
        assert result["error"] == "All SMB authentication methods failed"
    
    @patch('socket.socket')
    @patch.object(WindowsConnectivityTester, 'test_port_connectivity')
    def test_test_rdp_connectivity_success(self, mock_port_test, mock_socket):
        """Test successful RDP connectivity."""
        mock_port_test.return_value = True
        
        mock_socket.return_value.connect_ex.return_value = 0
        mock_socket.return_value.close.return_value = None
        
        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test.local",
            location="test",
            user="Administrator",
            password="testpass",
            ssh_key=None,
            connection_method="smb",
            port=3389,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        )
        
        tester = WindowsConnectivityTester()
        result = tester.test_rdp_connectivity(server)
        
        assert result["success"] is True
        assert result["protocol"] == "rdp"
        assert result["port"] == 3389
        assert result["details"]["connection_test"] == "successful"
    
    @patch.object(WindowsConnectivityTester, 'test_port_connectivity')
    def test_test_rdp_connectivity_port_failure(self, mock_port_test):
        """Test RDP connectivity with port failure."""
        mock_port_test.return_value = False
        
        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test.local",
            location="test",
            user="Administrator",
            password="testpass",
            ssh_key=None,
            connection_method="smb",
            port=3389,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        )
        
        tester = WindowsConnectivityTester()
        result = tester.test_rdp_connectivity(server)
        
        assert result["success"] is False
        assert result["error"] == "Port 3389 not reachable"
    
    @patch.object(WindowsConnectivityTester, 'test_rdp_connectivity')
    @patch.object(WindowsConnectivityTester, 'test_smb_connectivity')
    def test_test_windows_connectivity_rdp_success(self, mock_smb, mock_rdp):
        """Test Windows connectivity with RDP success."""
        mock_rdp.return_value = {
            "success": True,
            "protocol": "rdp",
            "port": 3389,
            "details": {"connection_test": "successful"},
            "error": None
        }
        
        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test.local",
            location="test",
            user="Administrator",
            password="testpass",
            ssh_key=None,
            connection_method="smb",
            port=445,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        )
        
        tester = WindowsConnectivityTester()
        result = tester.test_windows_connectivity(server)
        
        assert result["overall_success"] is True
        assert result["primary_protocol"] == "rdp"
        assert result["fallback_used"] is False
        assert result["rdp_result"]["success"] is True
        assert result["smb_result"] is None
        
        # SMB should not be called
        mock_smb.assert_not_called()
    
    @patch.object(WindowsConnectivityTester, 'test_rdp_connectivity')
    @patch.object(WindowsConnectivityTester, 'test_smb_connectivity')
    def test_test_windows_connectivity_smb_fallback(self, mock_smb, mock_rdp):
        """Test Windows connectivity with SMB fallback."""
        mock_rdp.return_value = {
            "success": False,
            "protocol": "rdp",
            "port": 3389,
            "details": {},
            "error": "RDP connection test failed"
        }
        
        mock_smb.return_value = {
            "success": True,
            "protocol": "smb",
            "port": 445,
            "details": {"access_method": "anonymous"},
            "error": None
        }
        
        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test.local",
            location="test",
            user="Administrator",
            password="testpass",
            ssh_key=None,
            connection_method="smb",
            port=445,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        )
        
        tester = WindowsConnectivityTester()
        result = tester.test_windows_connectivity(server)
        
        assert result["overall_success"] is True
        assert result["primary_protocol"] == "smb"
        assert result["fallback_used"] is True
        assert result["rdp_result"]["success"] is False
        assert result["smb_result"]["success"] is True
        
        # Both should be called
        mock_rdp.assert_called_once()
        mock_smb.assert_called_once()
    
    @patch.object(WindowsConnectivityTester, 'test_rdp_connectivity')
    @patch.object(WindowsConnectivityTester, 'test_smb_connectivity')
    def test_test_windows_connectivity_both_fail(self, mock_smb, mock_rdp):
        """Test Windows connectivity with both protocols failing."""
        mock_smb.return_value = {
            "success": False,
            "protocol": "smb",
            "port": 445,
            "details": {},
            "error": "SMB enumeration failed"
        }
        
        mock_rdp.return_value = {
            "success": False,
            "protocol": "rdp",
            "port": 3389,
            "details": {},
            "error": "RDP connection test failed"
        }
        
        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test.local",
            location="test",
            user="Administrator",
            password="testpass",
            ssh_key=None,
            connection_method="smb",
            port=445,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        )
        
        tester = WindowsConnectivityTester()
        result = tester.test_windows_connectivity(server)
        
        assert result["overall_success"] is False
        assert result["primary_protocol"] is None
        assert result["fallback_used"] is True
        assert result["smb_result"]["success"] is False
        assert result["rdp_result"]["success"] is False


class TestWindowsConnectivityFunctions:
    """Test the convenience functions."""
    
    @patch('hai.core.windows_connectivity.WindowsConnectivityTester')
    def test_check_windows_connectivity_function(self, mock_tester_class):
        """Test the check_windows_connectivity convenience function."""
        mock_tester = MagicMock()
        mock_tester_class.return_value = mock_tester
        
        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test.local",
            location="test",
            user="Administrator",
            password="testpass",
            ssh_key=None,
            connection_method="smb",
            port=445,
            active=True,
            grade="important",
            tool="test",
            os="windows",
            tunnel_routes=[]
        )
        
        expected_result = {"overall_success": True, "primary_protocol": "smb"}
        mock_tester.test_windows_connectivity.return_value = expected_result
        
        result = check_windows_connectivity(server, timeout=60)
        
        assert result == expected_result
        mock_tester_class.assert_called_once_with(60)
        mock_tester.test_windows_connectivity.assert_called_once_with(server)
    
    @patch('hai.core.windows_connectivity.WindowsConnectivityTester')
    def test_check_multiple_windows_servers(self, mock_tester_class):
        """Test the check_multiple_windows_servers function."""
        mock_tester = MagicMock()
        mock_tester_class.return_value = mock_tester
        
        servers = [
            ServerEntry(
                hostname="server1",
                ip="192.168.1.100",
                dns="server1.local",
                location="test",
                user="Administrator",
                password="testpass",
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
                hostname="server2",
                ip="192.168.1.101",
                dns="server2.local",
                location="test",
                user="Administrator",
                password="testpass",
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
                hostname="server3",
                ip="192.168.1.102",
                dns="server3.local",
                location="test",
                user="Administrator",
                password="testpass",
                ssh_key=None,
                connection_method="ssh",  # Should be skipped
                port=22,
                active=True,
                grade="important",
                tool="test",
                os="linux",
                tunnel_routes=[]
            )
        ]
        
        # Mock results: server1 (SMB success), server2 (RDP fallback), server3 (skipped)
        mock_tester.test_windows_connectivity.side_effect = [
            {
                "overall_success": True,
                "primary_protocol": "smb",
                "fallback_used": False
            },
            {
                "overall_success": True,
                "primary_protocol": "rdp",
                "fallback_used": True
            }
        ]
        
        result = check_multiple_windows_servers(servers, timeout=60)
        
        assert result["total_servers"] == 3
        assert result["successful"] == 2
        assert result["failed"] == 0
        assert result["smb_only"] == 1
        assert result["rdp_fallback"] == 1
        assert result["both_failed"] == 0
        assert len(result["server_results"]) == 2  # Only Windows servers
        
        # Should only be called for Windows servers
        assert mock_tester.test_windows_connectivity.call_count == 2 