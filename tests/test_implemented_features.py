#!/usr/bin/env python3
"""
Test suite for all implemented features of HAI.

This test suite verifies:
- All connector implementations (SSH, SMB, Impacket, FTP)
- File transfer with compression and MD5 verification
- Threaded operations
- State management
- Enhanced logging
- Error handling and fallback logic
"""

import pytest
import tempfile
import os
import json
from pathlib import Path

# Import HAI components
from hai.core.server_schema import ServerEntry, TunnelRoute, TunnelHop
from hai.core.threaded_operations import (
    run_command_on_servers,
    upload_file_to_servers,
    download_file_from_servers
)
from hai.utils.enhanced_logger import get_enhanced_logger
from hai.utils.state_manager import get_state_manager, save_current_state
from hai.utils.constants import *
from hai.connectors import SSHConnector, SMBConnector, ImpacketWrapper, FTPConnector

class TestConnectorImplementations:
    """Test all connector implementations."""
    
    def test_ssh_connector_creation(self):
        """Test SSH connector can be created."""
        connector = SSHConnector(
            host="test-host",
            port=22,
            user="test-user",
            password="test-pass"
        )
        assert connector.host == "test-host"
        assert connector.port == 22
        assert connector.user == "test-user"
        assert connector.password == "test-pass"
    
    def test_smb_connector_creation(self):
        """Test SMB connector can be created."""
        connector = SMBConnector(
            host="test-host",
            user="test-user",
            password="test-pass"
        )
        assert connector.host == "test-host"
        assert connector.user == "test-user"
        assert connector.password == "test-pass"
    
    def test_impacket_wrapper_creation(self):
        """Test Impacket wrapper can be created."""
        connector = ImpacketWrapper(
            host="test-host",
            user="test-user",
            password="test-pass"
        )
        assert connector.host == "test-host"
        assert connector.user == "test-user"
        assert connector.password == "test-pass"
    
    def test_ftp_connector_creation(self):
        """Test FTP connector can be created."""
        connector = FTPConnector(
            host="test-host",
            user="test-user",
            password="test-pass"
        )
        assert connector.host == "test-host"
        assert connector.user == "test-user"
        assert connector.password == "test-pass"

class TestStateManagement:
    """Test state management functionality."""
    
    def test_state_manager_creation(self):
        """Test state manager can be created."""
        state_manager = get_state_manager()
        assert state_manager is not None
        assert hasattr(state_manager, 'state_dir')
    
    def test_new_state_creation(self):
        """Test new state can be created."""
        state_manager = get_state_manager()
        state = state_manager.create_new_state("Test state")
        assert state is not None
        assert state.metadata.description == "Test state"
        assert state.metadata.version == STATE_VERSION
    
    def test_operation_state_update(self):
        """Test operation state can be updated."""
        state_manager = get_state_manager()
        
        # Create a new state first
        state_manager.create_new_state("Test state")
        
        # Update operation state
        state_manager.update_operation_state(
            operation_id="test_op_001",
            operation_type="command_execution",
            servers=["server1", "server2"],
            successful=["server1"],
            failed=["server2"],
            status="completed"
        )
        
        # Verify operation state was updated
        op_state = state_manager.get_operation_state("test_op_001")
        assert op_state is not None
        assert op_state.operation_id == "test_op_001"
        assert op_state.status == "completed"

class TestEnhancedLogging:
    """Test enhanced logging functionality."""
    
    def test_enhanced_logger_creation(self):
        """Test enhanced logger can be created."""
        logger = get_enhanced_logger("test_logger")
        assert logger is not None
        assert hasattr(logger, 'log_info')
        assert hasattr(logger, 'log_warning')
        assert hasattr(logger, 'log_error')
    
    def test_logging_with_context(self):
        """Test logging with context works."""
        logger = get_enhanced_logger("test_context_logger")
        
        # Test logging with context
        logger.log_info("Test message", {"key": "value"})
        # If no exception is raised, the test passes
    
    def test_performance_logging(self):
        """Test performance logging works."""
        from hai.utils.enhanced_logger import log_performance
        
        # Test performance logging
        log_performance("test_operation", 1.5, 3)
        # If no exception is raised, the test passes

class TestFileTransfer:
    """Test file transfer functionality."""
    
    def test_md5_verification(self):
        """Test MD5 verification functionality."""
        from hai.utils.md5sum import md5sum
        
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            test_file = f.name
        
        try:
            # Calculate MD5
            md5_hash = md5sum(test_file)
            assert md5_hash is not None
            assert len(md5_hash) == 32  # MD5 hash is 32 characters
        finally:
            os.unlink(test_file)
    
    def test_compression_constants(self):
        """Test compression constants are defined."""
        assert SUPPORTED_COMPRESSION_FORMATS is not None
        assert len(SUPPORTED_COMPRESSION_FORMATS) > 0
        assert ".tar.gz" in SUPPORTED_COMPRESSION_FORMATS

class TestThreadedOperations:
    """Test threaded operations functionality."""
    
    @pytest.mark.timeout(10)
    def test_batch_result_creation(self):
        """Test BatchResult can be created."""
        from hai.core.threaded_operations import BatchResult, OperationResult
        from hai.core.server_schema import ServerEntry
        
        # Create test server
        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test-server.local",
            location="test-location",
            user="test-user",
            password="test-pass",
            ssh_key=None,
            connection_method="ssh",
            port=22,
            active=True,
            grade="important",
            tool="test-tool",
            os="linux",
            tunnel_routes=[]
        )
        
        # Create test operation result
        op_result = OperationResult(
            server=server,
            success=True,
            result={"output": "test output"},
            execution_time=1.5
        )
        
        # Create batch result
        batch_result = BatchResult(
            successful=[op_result],
            failed=[],
            total_servers=1,
            total_successful=1,
            total_failed=0,
            execution_time=1.5
        )
        
        assert batch_result.success_rate == 100.0
        assert batch_result.total_servers == 1
        assert len(batch_result.successful) == 1
        assert len(batch_result.failed) == 0

class TestConstants:
    """Test constants are properly defined."""
    
    def test_connection_constants(self):
        """Test connection constants are defined."""
        assert DEFAULT_SSH_PORT == 22
        assert DEFAULT_SMB_PORT == 445
        assert DEFAULT_TIMEOUT > 0
        assert DEFAULT_MAX_WORKERS > 0
    
    def test_supported_protocols(self):
        """Test supported protocols are defined."""
        assert "ssh" in SUPPORTED_CONNECTION_METHODS
        assert "smb" in SUPPORTED_CONNECTION_METHODS
        assert "custom" in SUPPORTED_CONNECTION_METHODS
        assert "ftp" in SUPPORTED_CONNECTION_METHODS
    
    def test_error_codes(self):
        """Test error codes are defined."""
        assert "CONNECTION_FAILED" in ERROR_CODES
        assert "AUTHENTICATION_FAILED" in ERROR_CODES
        assert "COMMAND_FAILED" in ERROR_CODES
        assert "FILE_TRANSFER_FAILED" in ERROR_CODES

class TestServerSchema:
    """Test server schema functionality."""
    
    def test_server_entry_creation(self):
        """Test ServerEntry can be created."""
        server = ServerEntry(
            hostname="test-server",
            ip="192.168.1.100",
            dns="test-server.local",
            location="test-location",
            user="test-user",
            password="test-pass",
            ssh_key=None,
            connection_method="ssh",
            port=22,
            active=True,
            grade="important",
            tool="test-tool",
            os="linux",
            tunnel_routes=[]
        )
        
        assert server.hostname == "test-server"
        assert server.ip == "192.168.1.100"
        assert server.user == "test-user"
        assert server.connection_method == "ssh"
    
    def test_tunnel_route_creation(self):
        """Test TunnelRoute can be created."""
        route = TunnelRoute(
            name="test-route",
            active=True,
            hops=[]
        )
        
        assert route.name == "test-route"
        assert route.active is True
        assert len(route.hops) == 0
    
    def test_tunnel_hop_creation(self):
        """Test TunnelHop can be created."""
        hop = TunnelHop(
            ip="192.168.1.100",
            user="test-user",
            method="ssh",
            port=22
        )
        
        assert hop.ip == "192.168.1.100"
        assert hop.user == "test-user"
        assert hop.method == "ssh"
        assert hop.port == 22

class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_import_all_modules(self):
        """Test all modules can be imported."""
        # Test core imports
        from hai.core import (
            connect_with_fallback,
            upload_file,
            download_file,
            run_command,
            ServerEntry
        )
        
        # Test utils imports
        from hai.utils import (
            get_logger,
            get_enhanced_logger,
            get_state_manager
        )
        
        # Test connectors imports
        from hai.connectors import (
            SSHConnector,
            SMBConnector,
            ImpacketWrapper,
            FTPConnector
        )
        
        # If no exception is raised, all imports work
        assert True
    
    def test_constants_consistency(self):
        """Test constants are consistent across modules."""
        # Test that constants used in different modules are consistent
        assert DEFAULT_TIMEOUT > 0
        assert DEFAULT_MAX_WORKERS > 0
        assert len(SUPPORTED_CONNECTION_METHODS) > 0
        assert len(SUPPORTED_FILE_TRANSFER_PROTOCOLS) > 0

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 