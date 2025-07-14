"""
SMB Connector for HAI

This module provides SMB connectivity functionality for the HAI project.
"""

import smbclient
from typing import List
from ..utils.logger import get_logger
from .base_connector import BaseConnector

logger = get_logger("smb_connector")

try:
    from smb.SMBConnection import SMBConnection as SMBLibConnection
    SMB_AVAILABLE = True
except ImportError:
    SMB_AVAILABLE = False
    logger.warning("smb.SMBConnection not available, using placeholder SMB functionality")


class SMBConnection:
    """SMB connection wrapper."""
    
    def __init__(self, host: str, user: str, password: str = None, 
                 domain: str = "", timeout: int = 30):
        self.host = host
        self.user = user
        self.password = password
        self.domain = domain
        self.timeout = timeout
        self.connection = None
    
    def connect(self) -> bool:
        """Establish SMB connection."""
        try:
            if SMB_AVAILABLE:
                # Use real SMB connection
                self.connection = SMBLibConnection(
                    self.user, 
                    self.password, 
                    'client', 
                    self.host, 
                    domain=self.domain,
                    use_ntlm_v2=True,
                    timeout=self.timeout
                )
                # Test connection by listing shares
                shares = self.connection.listShares()
                logger.info(f"Connected to SMB on {self.host} as {self.user}")
                logger.info(f"Available shares: {[share.name for share in shares]}")
                return True
            else:
                logger.error("smbprotocol not available: cannot establish real SMB connection. Install smbprotocol for full functionality.")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to SMB on {self.host}: {e}")
            return False
    
    def list_shares(self) -> List[str]:
        """List available SMB shares."""
        try:
            if SMB_AVAILABLE and self.connection:
                shares = self.connection.listShares()
                return [share.name for share in shares]
            else:
                logger.error("smbprotocol not available or connection not established: cannot list shares.")
                return []
        except Exception as e:
            logger.error(f"Failed to list shares: {e}")
            return []
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file via SMB."""
        try:
            if SMB_AVAILABLE and self.connection:
                # Parse remote path to get share and file path
                if remote_path.startswith('//'):
                    # Format: //host/share/path
                    parts = remote_path[2:].split('/', 2)
                    if len(parts) >= 2:
                        share_name = parts[0]
                        file_path = parts[1] if len(parts) > 1 else ''
                    else:
                        raise ValueError(f"Invalid SMB path format: {remote_path}")
                else:
                    # Assume default share and path
                    share_name = "C$"
                    file_path = remote_path.lstrip('/')
                def file_callback():
                    with open(local_path, 'rb') as f:
                        return f.read()
                self.connection.putFile(share_name, file_path, file_callback)
                logger.info(f"SMB upload completed: {local_path} -> {remote_path}")
                return True
            else:
                logger.error("SMB library not available: cannot perform real upload. Install smbprotocol for full functionality.")
                return False
        except Exception as e:
            logger.error(f"SMB upload failed: {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file via SMB."""
        try:
            if SMB_AVAILABLE and self.connection:
                # Parse remote path to get share and file path
                if remote_path.startswith('//'):
                    # Format: //host/share/path
                    parts = remote_path[2:].split('/', 2)
                    if len(parts) >= 2:
                        share_name = parts[0]
                        file_path = parts[1] if len(parts) > 1 else ''
                    else:
                        raise ValueError(f"Invalid SMB path format: {remote_path}")
                else:
                    # Assume default share and path
                    share_name = "C$"
                    file_path = remote_path.lstrip('/')
                def file_callback(data):
                    with open(local_path, 'wb') as f:
                        f.write(data)
                self.connection.getFile(share_name, file_path, file_callback)
                logger.info(f"SMB download completed: {remote_path} -> {local_path}")
                return True
            else:
                logger.error("SMB library not available: cannot perform real download. Install smbprotocol for full functionality.")
                return False
        except Exception as e:
            logger.error(f"SMB download failed: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the SMB connection is healthy."""
        try:
            if SMB_AVAILABLE and self.connection:
                # Try to list shares as a health check
                self.connection.listShares()
                return True
            else:
                logger.error("smbprotocol not available: cannot perform real health check. Install smbprotocol for full functionality.")
                return False
        except Exception as e:
            logger.error(f"SMB health check failed: {e}")
            return False
    
    def disconnect(self):
        """Close the SMB connection."""
        if self.connection:
            self.connection.close()
            self.connection = None


def connect_cls(cls, host, user, password=None, domain="", lmhash="", nthash="", aesKey="", doKerberos=False, kdcHost=None, timeout=30, client_id=None, **kwargs):
    """Connect using SMB class."""
    connection = SMBConnection(host, user, password, domain, timeout)
    if connection.connect():
        return connection
    return None


class SMBConnector(BaseConnector):
    """SMB connector for Windows file operations."""
    
    def __init__(self, host: str, user: str, password: str = None, 
                 domain: str = "", timeout: int = 30, client_id: str = None):
        self.host = host
        self.user = user
        self.password = password
        self.timeout = timeout
        self.domain = domain
        self.client_id = client_id
        self.smb_connection = None
    
    def connect(self) -> bool:
        """Establish SMB connection."""
        try:
            self.smb_connection = SMBConnection(
                self.host, self.user, self.password, 
                self.domain, self.timeout
            )
            return self.smb_connection.connect()
        except Exception as e:
            logger.error(f"Failed to establish SMB connection: {e}")
            return False
    
    def disconnect(self):
        """Close SMB connection."""
        if self.smb_connection:
            self.smb_connection.disconnect()
            self.smb_connection = None
    
    def list_shares(self) -> List[str]:
        """List available SMB shares."""
        if not self.smb_connection:
            logger.error("No SMB connection established")
            return []
        
        return self.smb_connection.list_shares()
    
    def health_check(self) -> bool:
        """Check SMB connection health."""
        if not self.smb_connection:
            return False
        
        return self.smb_connection.health_check()
    
    def exec_command(self, command: str) -> tuple:
        """Execute a command via SMB using WMI or PowerShell."""
        if not self.smb_connection:
            raise Exception("SMB connection not established.")
        logger.info(f"Executing command via SMB: {command}")
        
        try:
            # Try to use WMI for command execution
            if SMB_AVAILABLE:
                from impacket.dcerpc.v5 import wmi
                from impacket.dcerpc.v5.dtypes import NULL
                
                # Create WMI connection
                dce = self.smb_connection.get_dce_rpc()
                dce.connect()
                dce.bind(wmi.MSRPC_UUID_WMI)
                
                # Execute command via WMI
                wmi_conn = wmi.WMI(dce)
                result = wmi_conn.exec_query(f"SELECT * FROM Win32_Process WHERE Name='cmd.exe' AND CommandLine='{command}'")
                
                return str(result), ""
            else:
                logger.error("Impacket not available: cannot execute command via SMB. Install impacket for full functionality.")
                return "", "Impacket not available: install impacket for SMB command execution."
        except Exception as e:
            logger.error(f"SMB command execution failed: {e}")
            return "", str(e)
    
    def is_alive(self) -> bool:
        """Check if the SMB connection is still alive and functional."""
        return self.health_check()
