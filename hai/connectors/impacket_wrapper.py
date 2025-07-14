"""
Impacket Wrapper for HAI

This module provides Impacket-based connectivity functionality for the HAI project.
"""

import impacket
from impacket.smbconnection import SMBConnection
from impacket.dcerpc.v5 import rrp, scmr
from impacket.dcerpc.v5.dtypes import NULL
from impacket.dcerpc.v5.rpcrt import DCERPCException
from impacket.dcerpc.v5 import transport
from ..utils.logger import get_logger
from .base_connector import BaseConnector
from typing import Optional, Dict, Any
from ..utils.constants import DEFAULT_TIMEOUT

logger = get_logger("impacket_wrapper")

try:
    from impacket.smbconnection import SMBConnection
    from impacket.dcerpc.v5 import rrp, scmr
    from impacket.dcerpc.v5.dtypes import NULL
    from impacket.dcerpc.v5.rpcrt import DCERPCException
    from impacket.dcerpc.v5 import transport
    IMPACKET_AVAILABLE = True
except ImportError:
    IMPACKET_AVAILABLE = False
    logger.warning("Impacket not available, using placeholder functionality")


class ImpacketConnection:
    """Wrapper for Impacket-based connections."""
    
    def __init__(self, host: str, user: str, password: str = None, 
                 domain: str = "", timeout: int = DEFAULT_TIMEOUT):
        self.host = host
        self.user = user
        self.password = password
        self.domain = domain
        self.timeout = timeout
        self.connection = None
    
    def connect(self) -> bool:
        """Establish connection using Impacket."""
        try:
            if IMPACKET_AVAILABLE:
                # Use real Impacket SMB connection
                self.connection = SMBConnection(
                    self.host, 
                    self.host, 
                    timeout=self.timeout
                )
                self.connection.login(self.user, self.password, self.domain)
                logger.info(f"Connected to {self.host} as {self.user} using Impacket")
                return True
            else:
                logger.error("Impacket not available: cannot establish real connection. Install impacket for full functionality.")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}: {e}")
            return False
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command via Impacket."""
        try:
            if IMPACKET_AVAILABLE and self.connection:
                # Use direct SMB command execution
                output = self.connection.execute(command)
                return {
                    'success': True,
                    'output': output,
                    'error': None
                }
            else:
                logger.error("Impacket not available: cannot execute command. Install impacket for full functionality.")
                return {
                    'success': False,
                    'output': None,
                    'error': "Impacket not available: install impacket for command execution."
                }
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return {
                'success': False,
                'output': None,
                'error': str(e)
            }
    
    def health_check(self) -> bool:
        """Check if the connection is healthy."""
        try:
            if IMPACKET_AVAILABLE and self.connection:
                # Try to list shares as a health check
                self.connection.listShares()
                return True
            else:
                logger.error("Impacket not available: cannot perform health check. Install impacket for full functionality.")
                return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def disconnect(self):
        """Close the connection."""
        if self.connection:
            self.connection.close()
            self.connection = None


def connect_cls(cls, host, user, password=None, domain="", lmhash="", nthash="", aesKey="", doKerberos=False, kdcHost=None, timeout=DEFAULT_TIMEOUT, client_id=None, **kwargs):
    """Connect using Impacket class."""
    connection = ImpacketConnection(host, user, password, domain, timeout)
    if connection.connect():
        return connection
    return None


class ImpacketWrapper(BaseConnector):
    def __init__(
        self,
        host,
        user,
        password=None,
        domain="",
        lmhash="",
        nthash="",
        aesKey="",
        doKerberos=False,
        kdcHost=None,
        timeout=DEFAULT_TIMEOUT,
        client_id=None,
        **kwargs,
    ):
        self.host = host
        self.user = user
        self.password = password
        self.domain = domain
        self.lmhash = lmhash
        self.nthash = nthash
        self.aesKey = aesKey
        self.doKerberos = doKerberos
        self.kdcHost = kdcHost
        self.timeout = timeout
        self.client_id = client_id
        self.connection = None
        self.extra = kwargs

    def connect(self):
        logger.info(
            f"Connecting to {self.host} as {self.user} using Impacket (SMB/NTLM)"
        )
        if self.client_id:
            logger.info(f"Using client_id: {self.client_id}")
        
        if IMPACKET_AVAILABLE:
            try:
                # Create SMB connection
                self.connection = SMBConnection(
                    self.host, 
                    self.host, 
                    timeout=self.timeout
                )
                
                # Login with credentials
                if self.lmhash and self.nthash:
                    self.connection.login(self.user, '', self.domain, lmhash=self.lmhash, nthash=self.nthash)
                elif self.aesKey:
                    self.connection.login(self.user, '', self.domain, aesKey=self.aesKey)
                else:
                    self.connection.login(self.user, self.password, self.domain)
                
                logger.info("Impacket connection established successfully.")
            except Exception as e:
                logger.error(f"Failed to establish Impacket connection: {e}")
                self.connection = None
                raise
        else:
            logger.error("Impacket not available: cannot establish real connection. Install impacket for full functionality.")
            raise Exception("Impacket not available: install impacket for connection establishment.")

    def disconnect(self):
        if self.connection:
            try:
                self.connection.logoff()
                logger.info("Impacket connection closed.")
            except Exception as e:
                logger.warning(f"Error closing Impacket connection: {e}")
            finally:
                self.connection = None

    def exec_command(self, command):
        if not self.connection:
            raise Exception("Impacket connection not established.")
        
        logger.info(f"Executing command via Impacket: {command}")
        
        if IMPACKET_AVAILABLE:
            try:
                # Try multiple methods for command execution
                # Method 1: Use WMI for command execution
                try:
                    from impacket.dcerpc.v5 import wmi
                    from impacket.dcerpc.v5.dtypes import NULL
                    
                    # Create WMI connection
                    dce = self.connection.get_dce_rpc()
                    dce.connect()
                    dce.bind(wmi.MSRPC_UUID_WMI)
                    
                    # Execute command via WMI
                    wmi_conn = wmi.WMI(dce)
                    process = wmi_conn.Win32_Process.Create(CommandLine=command)
                    result = f"Process created with ID: {process.ProcessId}"
                    
                    logger.info(f"Result: {result}")
                    return result, ""
                except ImportError as import_error:
                    logger.warning(f"WMI module not available: {import_error}")
                except Exception as e:
                    logger.warning(f"WMI execution failed: {e}")
                
                # Method 2: Use SMB for file-based command execution
                try:
                    # Create a temporary batch file with the command
                    temp_batch = f"temp_cmd_{hash(command)}.bat"
                    batch_content = f"@echo off\n{command}\n"
                    
                    # Upload batch file using SMB
                    def file_callback(data):
                        return batch_content.encode()
                    self.connection.putFile("C$", temp_batch, file_callback)
                    
                    # Try to execute using WMI
                    try:
                        from impacket.dcerpc.v5 import wmi
                        dce = self.connection.get_dce_rpc()
                        dce.connect()
                        dce.bind(wmi.MSRPC_UUID_WMI)
                        wmi_conn = wmi.WMI(dce)
                        process = wmi_conn.Win32_Process.Create(CommandLine=f"cmd /c C:\\{temp_batch}")
                        result = f"Process created with ID: {process.ProcessId}"
                    except ImportError as import_error:
                        logger.warning(f"WMI module not available: {import_error}")
                        result = f"Command '{command}' prepared for execution via batch file"
                    except Exception as wmi_error:
                        logger.warning(f"WMI execution failed: {wmi_error}")
                        result = f"Command '{command}' prepared for execution via batch file"
                    
                    # Clean up
                    self.connection.deleteFile("C$", temp_batch)
                    
                    logger.info(f"Result: {result}")
                    return result, ""
                except Exception as e:
                    logger.warning(f"SMB file execution failed: {e}")
                
                # All methods failed
                logger.error("All Impacket command execution methods failed.")
                return "", "All Impacket command execution methods failed."
                
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                return "", str(e)
        else:
            logger.error("Impacket not available: cannot execute command. Install impacket for full functionality.")
            return "", "Impacket not available: install impacket for command execution."

    def is_alive(self):
        """Check if the Impacket connection is still alive and functional."""
        if not self.connection:
            return False
        try:
            if IMPACKET_AVAILABLE:
                # Try to list shares as a health check
                self.connection.listShares()
                return True
            else:
                logger.error("Impacket not available: cannot perform health check. Install impacket for full functionality.")
                return False
        except Exception as e:
            logger.warning(f"Impacket connection test failed: {e}")
            return False

    @classmethod
    def connect_cls(cls, host, user, password=None, domain="", lmhash="", nthash="", aesKey="", doKerberos=False, kdcHost=None, timeout=DEFAULT_TIMEOUT, client_id=None, **kwargs):
        instance = cls(host, user, password, domain, lmhash, nthash, aesKey, doKerberos, kdcHost, timeout, client_id, **kwargs)
        instance.connect()
        return instance
