"""
IPython magics module for HAI (Hybrid Attack Interface).

This module provides IPython magic commands for:
- Route management: Activate/deactivate tunnel routes
- Server operations: Interactive server management
- Connection testing: Test connectivity to servers
"""

from .route_magics import RouteMagics, load_ipython_extension

__all__ = [
    'RouteMagics',
    'load_ipython_extension'
] 