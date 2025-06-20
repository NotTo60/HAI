from connectors.impacket_wrapper import ImpacketWrapper
from connectors.smb_connector import SMBConnector
from connectors.ssh_connector import SSHConnector
from utils.logger import get_logger

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
                port=server.port,
                user=server.user,
                password=server.password,
                ssh_key=server.ssh_key,
                timeout=config.get("timeout", 10),
                client_id=config.get("client_id"),
            )
        elif method == "smb":
            conn = SMBConnector(
                host=server.ip,
                user=server.user,
                password=server.password,
                timeout=config.get("timeout", 10),
                client_id=config.get("client_id"),
            )
        elif method == "custom":
            conn = ImpacketWrapper(
                host=server.ip,
                user=server.user,
                password=server.password,
                timeout=config.get("timeout", 10),
                client_id=config.get("client_id"),
            )
        elif method == "ftp":
            # Placeholder for future FTPConnector
            raise NotImplementedError("FTPConnector not implemented yet.")
        else:
            raise Exception(f"Unknown connection method: {method}")
        conn.connect()
        return conn
