from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel
from utils.constants import (
    SUPPORTED_CONNECTION_METHODS, SUPPORTED_FILE_TRANSFER_PROTOCOLS, SUPPORTED_OS_TYPES, SERVER_GRADES
)


class TunnelHop(BaseModel):
    ip: str
    user: str
    method: Literal[
        tuple(SUPPORTED_CONNECTION_METHODS)
    ]
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
    connection_method: Literal[
        tuple(SUPPORTED_CONNECTION_METHODS)
    ]
    port: int
    active: bool
    grade: Literal[
        tuple(SERVER_GRADES)
    ]
    tool: Optional[str]
    os: Literal[
        tuple(SUPPORTED_OS_TYPES)
    ]
    tunnel_routes: List[TunnelRoute]
    file_transfer_protocol: Optional[
        Literal[tuple(SUPPORTED_FILE_TRANSFER_PROTOCOLS)]
    ] = SUPPORTED_FILE_TRANSFER_PROTOCOLS[0]
    config: Optional[Dict[str, Any]] = None
