from IPython.core.magic import register_line_magic

from utils.logger import get_logger

logger = get_logger("route_magics")
servers_cache = {}  # Populate externally


@register_line_magic
def activate_route(line):
    host, route_name = line.split()
    srv = servers_cache.get(host)
    for route in srv.tunnel_routes:
        if route.name == route_name:
            route.active = True
            logger.info(f"Activated route '{route_name}' on '{host}'")
            return


@register_line_magic
def deactivate_route(line):
    host, route_name = line.split()
    srv = servers_cache.get(host)
    for route in srv.tunnel_routes:
        if route.name == route_name:
            route.active = False
            logger.info(f"Deactivated route '{route_name}' on '{host}'")
            return


@register_line_magic
def refresh_routes(line):
    host = line.strip()
    srv = servers_cache.get(host)
    for route in srv.tunnel_routes:
        if not route.active:
            try:
                # Implement dry-run connection check
                route.active = True
                logger.info(f"Route '{route.name}' re-activated")
            except Exception:
                logger.warning(f"Route '{route.name}' still unreachable")
