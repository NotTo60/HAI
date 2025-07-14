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
