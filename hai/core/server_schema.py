from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel
from ..utils.constants import (
    SUPPORTED_CONNECTION_METHODS, SUPPORTED_FILE_TRANSFER_PROTOCOLS, SUPPORTED_OS_TYPES, SERVER_GRADES
)


class TunnelHop(BaseModel):
    ip: str
    user: str
    method: Literal["ssh", "smb", "custom", "ftp", "impacket"]
    port: Optional[int] = None
    tool: Optional[str] = None


class TunnelRoute(BaseModel):
    name: str
    active: bool = True
    hops: List[TunnelHop]


class ServerEntry(BaseModel):
    hostname: str
    ip: str
    dns: str
    location: str
    user: str
    password: Optional[str]
    ssh_key: Optional[str]
    connection_method: Literal["ssh", "smb", "custom", "ftp", "impacket"]
    port: int
    active: bool
    grade: Literal["critical", "must-win", "important", "nice-to-have", "low-priority"]
    tool: Optional[str]
    os: Literal["linux", "windows", "unknown"]
    tunnel_routes: List[TunnelRoute]
    file_transfer_protocol: Optional[
        Literal["sftp", "scp", "smb", "ftp"]
    ] = "sftp"
    config: Optional[Dict[str, Any]] = None
