from IPython.core.magic import line_magic, Magics, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from utils.logger import get_logger

logger = get_logger("route_magics")
servers_cache = {}  # Populate externally


@magics_class
class RouteMagics(Magics):
    """iPython magics for managing tunnel routes."""
    
    def __init__(self, shell):
        super().__init__(shell)
        self.routes = {}
    
    @line_magic
    @magic_arguments()
    @argument('host', help='Hostname or IP address')
    @argument('route', help='Route name to activate')
    def activate_route(self, line):
        """Activate a tunnel route for a host."""
        args = parse_argstring(self.activate_route, line)
        
        host = args.host
        route = args.route
        
        logger.info(f"Activating route '{route}' for host '{host}'")
        
        srv = servers_cache.get(host)
        for route_obj in srv.tunnel_routes:
            if route_obj.name == route:
                route_obj.active = True
                logger.info(f"Activated route '{route}' on '{host}'")
                return f"Route '{route}' activated for host '{host}'"

    @line_magic
    @magic_arguments()
    @argument('host', help='Hostname or IP address')
    @argument('route', help='Route name to deactivate')
    def deactivate_route(self, line):
        """Deactivate a tunnel route for a host."""
        args = parse_argstring(self.deactivate_route, line)
        
        host = args.host
        route = args.route
        
        logger.info(f"Deactivating route '{route}' for host '{host}'")
        
        srv = servers_cache.get(host)
        for route_obj in srv.tunnel_routes:
            if route_obj.name == route:
                route_obj.active = False
                logger.info(f"Deactivated route '{route}' on '{host}'")
                return f"Route '{route}' deactivated for host '{host}'"

    @line_magic
    @magic_arguments()
    @argument('host', help='Hostname or IP address')
    def refresh_routes(self, line):
        """Try to reactivate all inactive routes for a host."""
        args = parse_argstring(self.refresh_routes, line)
        
        host = args.host
        
        logger.info(f"Refreshing routes for host '{host}'")
        
        srv = servers_cache.get(host)
        for route in srv.tunnel_routes:
            if not route.active:
                try:
                    # Implement dry-run connection check
                    from core.connection_manager import connect_with_fallback
                    from core.tunnel_builder import TunnelBuilder
                    
                    # Create a test connection to check if route is reachable
                    test_conn = TunnelBuilder.build(srv, route)
                    if test_conn and test_conn.is_alive():
                        route.active = True
                        logger.info(f"Route '{route.name}' re-activated")
                        test_conn.disconnect()
                    else:
                        logger.warning(f"Route '{route.name}' still unreachable")
                except Exception as e:
                    logger.warning(f"Route '{route.name}' still unreachable: {e}")
        
        logger.info(f"Routes refreshed for host '{host}'")
        return f"Routes refreshed for host '{host}'"

    @line_magic
    @magic_arguments()
    @argument('host', help='Hostname or IP address')
    def list_routes(self, line):
        """List all routes for a host."""
        args = parse_argstring(self.list_routes, line)
        
        host = args.host
        
        logger.info(f"Listing routes for host '{host}'")
        
        # Get server from cache and list its routes
        srv = servers_cache.get(host)
        if not srv:
            logger.warning(f"Host '{host}' not found in cache")
            return []
        
        routes_info = []
        for route in srv.tunnel_routes:
            routes_info.append({
                "name": route.name,
                "active": route.active,
                "hops": len(route.hops) if hasattr(route, 'hops') else 0
            })
        
        logger.info(f"Found {len(routes_info)} routes for host '{host}'")
        return routes_info

def load_ipython_extension(ipython):
    """Load the extension into IPython."""
    ipython.register_magics(RouteMagics)
