import paramiko

from .base_connector import BaseConnector
from ..utils.logger import get_logger
from ..utils.constants import DEFAULT_SSH_PORT, DEFAULT_TIMEOUT

logger = get_logger("ssh_connector")


class SSHConnector(BaseConnector):
    def __init__(
        self,
        host,
        port=DEFAULT_SSH_PORT,
        user=None,
        password=None,
        ssh_key=None,
        timeout=DEFAULT_TIMEOUT,
        client_id=None,
        **kwargs,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.ssh_key = ssh_key
        self.timeout = timeout
        self.client_id = client_id
        self.client = None
        self.extra = kwargs

    def connect(self):
        logger.info(f"Connecting to SSH {self.user}@{self.host}:{self.port}")
        if self.client_id:
            logger.info(f"Using client_id: {self.client_id}")
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.ssh_key:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    key_filename=self.ssh_key,
                    timeout=self.timeout,
                    allow_agent=True,
                    look_for_keys=True,
                )
            else:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    password=self.password,
                    timeout=self.timeout,
                    allow_agent=True,
                    look_for_keys=True,
                )
            logger.info("SSH connection established.")
        except Exception as e:
            logger.error(f"SSH connection failed: {e}")
            self.client = None
            raise

    def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("SSH connection closed.")

    def exec_command(self, command):
        if not self.client:
            raise Exception("SSH client not connected.")
        logger.info(f"Executing command: {command}")
        stdin, stdout, stderr = self.client.exec_command(command)
        out = stdout.read().decode()
        err = stderr.read().decode()
        logger.info(f"Command output: {out}")
        if err:
            logger.warning(f"Command error: {err}")
        return out, err

    def is_alive(self):
        """Check if the SSH connection is still alive and functional."""
        if not self.client:
            return False
        try:
            # Try to execute a simple command to test the connection
            self.client.exec_command("echo 'test'", timeout=5)
            return True
        except Exception as e:
            logger.warning(f"SSH connection test failed: {e}")
            return False

    @classmethod
    def connect_cls(cls, host, port=DEFAULT_SSH_PORT, user=None, password=None, ssh_key=None, timeout=DEFAULT_TIMEOUT, client_id=None, **kwargs):
        instance = cls(host, port, user, password, ssh_key, timeout, client_id, **kwargs)
        instance.connect()
        return instance
