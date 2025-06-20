import paramiko

from connectors.base_connector import BaseConnector
from utils.logger import get_logger

logger = get_logger("ssh_connector")


class SSHConnector(BaseConnector):
    def __init__(
        self,
        host,
        port,
        user,
        password=None,
        ssh_key=None,
        timeout=10,
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
