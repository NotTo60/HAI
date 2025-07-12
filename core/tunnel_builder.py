from connectors.impacket_wrapper import ImpacketWrapper
from connectors.smb_connector import SMBConnector
from connectors.ssh_connector import SSHConnector
from utils.logger import get_logger
from utils.constants import (
    DEFAULT_SSH_PORT, DEFAULT_TIMEOUT
)

logger = get_logger("tunnel_builder")


class TunnelBuilder:
    @staticmethod
    def build(server, route):
        logger.info(f"Building tunnel to {server.hostname} via {route.name}")
        method = server.connection_method
        config = server.config or {}
        if method == "ssh":
            conn = SSHConnector(
                host=server.ip,
                port=server.port or DEFAULT_SSH_PORT,
                user=server.user,
                password=server.password,
                ssh_key=server.ssh_key,
                timeout=config.get("timeout", DEFAULT_TIMEOUT),
                client_id=config.get("client_id"),
            )
        elif method == "smb":
            conn = SMBConnector(
                host=server.ip,
                user=server.user,
                password=server.password,
                timeout=config.get("timeout", DEFAULT_TIMEOUT),
                client_id=config.get("client_id"),
            )
        elif method == "custom":
            conn = ImpacketWrapper(
                host=server.ip,
                user=server.user,
                password=server.password,
                timeout=config.get("timeout", DEFAULT_TIMEOUT),
                client_id=config.get("client_id"),
            )
        elif method == "ftp":
            from connectors.ftp_connector import FTPConnector
            conn = FTPConnector(
                host=server.ip,
                user=server.user,
                password=server.password,
                timeout=config.get("timeout", DEFAULT_TIMEOUT),
                client_id=config.get("client_id"),
            )
        else:
            raise Exception(f"Unknown connection method: {method}")
        conn.connect()
        return conn
