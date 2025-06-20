from core.tunnel_builder import TunnelBuilder
from utils.logger import get_logger

logger = get_logger("connection_manager")

def connect_with_fallback(server):
    for route in server.tunnel_routes:
        if not route.active:
            logger.info(f"Skipping inactive route: {route.name}")
            continue
        try:
            logger.info(f"Trying tunnel route: {route.name}")
            conn = TunnelBuilder.build(server, route)
            if conn and conn.is_alive():
                logger.info(f"Success via: {route.name}")
                return conn
        except Exception as e:
            logger.warning(f"Tunnel failed: {route.name} — {e}")
            route.active = False
    raise Exception(f"All tunnel routes failed for server {server.hostname}") 