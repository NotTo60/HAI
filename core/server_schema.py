from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class TunnelHop(BaseModel):
    ip: str
    user: str
    method: Literal["ssh", "smb", "custom", "ftp"]
    port: Optional[int] = 22
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
    connection_method: Literal["ssh", "smb", "custom", "ftp"]
    port: int
    active: bool
    grade: str
    tool: Optional[str]
    os: Literal["linux", "windows", "unknown"]
    tunnel_routes: List[TunnelRoute]
    file_transfer_protocol: Optional[Literal["sftp", "scp", "smb", "ftp"]] = "sftp"
    config: Optional[Dict[str, Any]] = None
