import os
import pytest
from core.connection_manager import connect_with_fallback
from core.server_schema import ServerEntry, TunnelRoute, TunnelHop

# Helper to build a minimal ServerEntry for each protocol
def build_server_entry(prefix, method, os_type):
    return ServerEntry(
        hostname=f"{prefix.lower()}-test",
        ip=os.environ[f"TEST_{prefix}_HOST"],
        dns=os.environ.get(f"TEST_{prefix}_DNS", ""),
        location=os.environ.get(f"TEST_{prefix}_LOCATION", "test-lab"),
        user=os.environ[f"TEST_{prefix}_USER"],
        password=os.environ[f"TEST_{prefix}_PASS"],
        ssh_key=None,
        connection_method=method,
        port=int(os.environ.get(f"TEST_{prefix}_PORT", 22)),
        active=True,
        grade="must-win",
        tool=None,
        os=os_type,
        tunnel_routes=[TunnelRoute(name="direct", active=True, hops=[TunnelHop(ip=os.environ[f"TEST_{prefix}_HOST"], user=os.environ[f"TEST_{prefix}_USER"], method=method, port=int(os.environ.get(f"TEST_{prefix}_PORT", 22)))])],
        file_transfer_protocol="sftp" if method == "ssh" else "smb",
        config=None
    )

required_envs = [
    "TEST_LINUX_HOST", "TEST_LINUX_USER", "TEST_LINUX_PASS",
    "TEST_WINDOWS_HOST", "TEST_WINDOWS_USER", "TEST_WINDOWS_PASS"
]

skip_if_no_env = pytest.mark.skipif(
    not all(os.environ.get(e) for e in required_envs),
    reason="Real server credentials not set in environment"
)

@skip_if_no_env
def test_connect_linux_ssh():
    server = build_server_entry("LINUX", "ssh", "linux")
    conn = connect_with_fallback(server)
    out, err = conn.exec_command("whoami")
    assert server.user in out
    conn.disconnect()

@skip_if_no_env
def test_connect_windows_smb():
    server = build_server_entry("WINDOWS", "smb", "windows")
    conn = connect_with_fallback(server)
    # For SMB, just test connection and list shares if implemented
    if hasattr(conn, "list_shares"):
        shares = conn.list_shares()
        assert isinstance(shares, list)
    conn.disconnect()

@skip_if_no_env
def test_connect_windows_wmi():
    server = build_server_entry("WINDOWS", "impacket", "windows")
    conn = connect_with_fallback(server)
    # For WMI/Impacket, try a basic command
    out, err = conn.exec_command("whoami")
    assert server.user.lower() in out.lower()
    conn.disconnect() 