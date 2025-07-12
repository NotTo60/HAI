"""
FTP connector for file operations.

This module provides FTP connectivity for file operations,
enabling upload, download, and directory listing.
"""

from typing import Optional, Dict, Any, List
from connectors.base_connector import BaseConnector
from utils.logger import get_logger
from utils.constants import DEFAULT_TIMEOUT

logger = get_logger("ftp_connector")

try:
    from ftplib import FTP
    FTP_AVAILABLE = True
except ImportError:
    FTP_AVAILABLE = False
    logger.warning("ftplib not available, using placeholder FTP functionality")


class FTPConnection:
    """FTP connection wrapper."""
    
    def __init__(self, host: str, user: str, password: str = None, 
                 timeout: int = DEFAULT_TIMEOUT):
        self.host = host
        self.user = user
        self.password = password
        self.timeout = timeout
        self.connection = None
    
    def connect(self) -> bool:
        """Establish FTP connection."""
        try:
            if FTP_AVAILABLE:
                # Use real FTP connection
                self.connection = FTP()
                self.connection.connect(self.host, timeout=self.timeout)
                if self.user:
                    self.connection.login(self.user, self.password or '')
                else:
                    self.connection.login()
                logger.info(f"Connected to FTP on {self.host} as {self.user}")
                return True
            else:
                logger.error("ftplib not available: cannot establish real FTP connection. Install ftplib for full functionality.")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to FTP on {self.host}: {e}")
            return False
    
    def list_files(self, directory: str = "/") -> List[str]:
        """List files in a directory."""
        try:
            if FTP_AVAILABLE and self.connection:
                files = []
                self.connection.retrlines(f'LIST {directory}', files.append)
                return files
            else:
                logger.error("ftplib not available or connection not established: cannot list files.")
                return []
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file via FTP."""
        try:
            if FTP_AVAILABLE and self.connection:
                with open(local_path, 'rb') as f:
                    self.connection.storbinary(f'STOR {remote_path}', f)
                logger.info(f"FTP upload completed: {local_path} -> {remote_path}")
                return True
            else:
                logger.error("ftplib not available or connection not established: cannot upload file.")
                return False
        except Exception as e:
            logger.error(f"FTP upload failed: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file via FTP."""
        try:
            if FTP_AVAILABLE and self.connection:
                with open(local_path, 'wb') as f:
                    self.connection.retrbinary(f'RETR {remote_path}', f.write)
                logger.info(f"FTP download completed: {remote_path} -> {local_path}")
                return True
            else:
                logger.error("ftplib not available or connection not established: cannot download file.")
                return False
        except Exception as e:
            logger.error(f"FTP download failed: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the FTP connection is healthy."""
        try:
            if FTP_AVAILABLE and self.connection:
                # Try to get current directory as a health check
                self.connection.pwd()
                return True
            else:
                logger.error("ftplib not available or connection not established: cannot perform health check.")
                return False
        except Exception as e:
            logger.error(f"FTP health check failed: {e}")
            return False
    
    def disconnect(self):
        """Close the FTP connection."""
        if self.connection:
            self.connection.quit()
            self.connection = None


class FTPConnector(BaseConnector):
    """FTP connector for file operations."""
    
    def __init__(self, host: str, user: str, password: str = None, 
                 timeout: int = DEFAULT_TIMEOUT, client_id: str = None):
        self.host = host
        self.user = user
        self.password = password
        self.timeout = timeout
        self.client_id = client_id
        self.ftp_connection = None
    
    def connect(self) -> bool:
        """Establish FTP connection."""
        try:
            self.ftp_connection = FTPConnection(
                self.host, self.user, self.password, self.timeout
            )
            return self.ftp_connection.connect()
        except Exception as e:
            logger.error(f"Failed to establish FTP connection: {e}")
            return False
    
    def disconnect(self):
        """Close FTP connection."""
        if self.ftp_connection:
            self.ftp_connection.disconnect()
            self.ftp_connection = None
    
    def list_files(self, directory: str = "/") -> List[str]:
        """List files in a directory."""
        if not self.ftp_connection:
            logger.error("No FTP connection established")
            return []
        
        return self.ftp_connection.list_files(directory)
    
    def health_check(self) -> bool:
        """Check FTP connection health."""
        if not self.ftp_connection:
            return False
        
        return self.ftp_connection.health_check()
    
    def exec_command(self, command: str) -> tuple:
        """Execute a command via FTP using SITE command or similar."""
        if not self.ftp_connection:
            raise Exception("FTP connection not established.")
        logger.info(f"Executing command via FTP: {command}")
        
        try:
            if FTP_AVAILABLE and self.ftp_connection.connection:
                # Try to execute command via FTP SITE command
                try:
                    # Some FTP servers support SITE commands
                    response = self.ftp_connection.connection.sendcmd(f"SITE {command}")
                    logger.info(f"FTP command response: {response}")
                    return response, ""
                except Exception as e:
                    logger.warning(f"SITE command failed: {e}")
                
                # Try to execute via system command if available
                try:
                    response = self.ftp_connection.connection.sendcmd(f"SYST")
                    logger.info(f"System info: {response}")
                    return f"System: {response}", ""
                except Exception as e:
                    logger.warning(f"SYST command failed: {e}")
                
                # Fallback to error when no command execution method works
                logger.error("No FTP command execution method available.")
                return "", "No FTP command execution method available."
            else:
                logger.error("ftplib not available: cannot execute command via FTP. Install ftplib for full functionality.")
                return "", "ftplib not available: install ftplib for FTP command execution."
        except Exception as e:
            logger.error(f"FTP command execution failed: {e}")
            return "", str(e)
    
    def is_alive(self) -> bool:
        """Check if the FTP connection is still alive and functional."""
        return self.health_check()
    
    @classmethod
    def connect_cls(cls, host, user, password=None, timeout=DEFAULT_TIMEOUT, client_id=None, **kwargs):
        """Connect using FTP class."""
        instance = cls(host, user, password, timeout, client_id, **kwargs)
        if instance.connect():
            return instance
        return None 