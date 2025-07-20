"""
Server Schema Module for HAI

This module defines the data structures for server configuration and management.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal


@dataclass
class TunnelHop:
    ip: str
    user: str
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    port: Optional[int] = None
    os: Optional[str] = None
    tool: Optional[str] = None
    method: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


@dataclass
class TunnelRoute:
    name: str
    active: bool = True
    hops: List[TunnelHop] = field(default_factory=list)


@dataclass
class ServerEntry:
    hostname: str
    ip: str
    dns: Optional[str] = None
    location: Optional[str] = None
    user: str = ""
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    connection_method: Literal["ssh", "smb", "custom", "ftp", "impacket"] = "ssh"
    port: int = 22
    active: bool = True
    grade: Literal["critical", "must-win", "important", "nice-to-have", "low-priority"] = "important"
    tool: Optional[str] = None
    os: Literal["linux", "windows", "unknown"] = "unknown"
    tunnel_routes: List[TunnelRoute] = field(default_factory=list)
    file_transfer_protocol: Optional[Literal["sftp", "scp", "smb", "ftp"]] = "sftp"
    config: Optional[Dict[str, Any]] = None


def filter_servers(servers: list, logic: str = "and", **criteria) -> list:
    """
    Filter a list of ServerEntry objects by arbitrary attribute-value pairs.
    Supports AND (default) or OR logic, and multi-value matching.
    Ensures no duplicate servers in the result (especially for OR logic).
    Example usage:
        asia_servers = filter_servers(all_servers, location="asia")
        win_critical = filter_servers(all_servers, os="windows", grade="critical")
        asia_or_windows = filter_servers(all_servers, location="asia", os="windows", logic="or")
        multi_os = filter_servers(all_servers, os=["windows", "linux"])
    Args:
        servers: List of ServerEntry objects
        logic: 'and' (default) or 'or' (any criterion matches)
        **criteria: Arbitrary attribute-value pairs to filter on
    Returns:
        List of unique ServerEntry objects matching the criteria
    """
    filtered = []
    seen = set()
    for server in servers:
        matches = []
        for key, value in criteria.items():
            attr = server
            for part in key.split("__"):
                if hasattr(attr, part):
                    attr = getattr(attr, part)
                else:
                    attr = None
                    break
            if isinstance(value, (list, tuple, set)):
                match = attr in value
            else:
                match = attr == value
            matches.append(match)
        add = False
        if logic == "and":
            add = all(matches)
        elif logic == "or":
            add = any(matches)
        else:
            raise ValueError("logic must be 'and' or 'or'")
        # Use (hostname, ip) as a unique key
        key = (getattr(server, 'hostname', None), getattr(server, 'ip', None))
        if add and key not in seen:
            filtered.append(server)
            seen.add(key)
    return filtered
