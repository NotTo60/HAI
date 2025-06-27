import os
import tempfile
import pytest
from core.connection_manager import connect_with_fallback
from core.server_schema import ServerEntry, TunnelRoute, TunnelHop
from core.file_transfer import upload_file, download_file

# Helper to build a minimal ServerEntry for each protocol
def build_server_entry(prefix, method, os_type):
    # For Linux SSH, use SSH key instead of password
    if prefix == "LINUX" and method == "ssh":
        ssh_key_path = os.environ.get("TEST_LINUX_SSH_KEY", "terraform/id_rsa")
        password = None
        ssh_key = ssh_key_path
    else:
        password = os.environ[f"TEST_{prefix}_PASS"]
        ssh_key = None
    
    return ServerEntry(
        hostname=f"{prefix.lower()}-test",
        ip=os.environ[f"TEST_{prefix}_HOST"],
        dns=os.environ.get(f"TEST_{prefix}_DNS", ""),
        location=os.environ.get(f"TEST_{prefix}_LOCATION", "test-lab"),
        user=os.environ[f"TEST_{prefix}_USER"],
        password=password,
        ssh_key=ssh_key,
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
    "TEST_LINUX_HOST", "TEST_LINUX_USER", "TEST_LINUX_SSH_KEY",
    "TEST_WINDOWS_HOST", "TEST_WINDOWS_USER", "TEST_WINDOWS_PASS"
]

skip_if_no_env = pytest.mark.skipif(
    not all(os.environ.get(e) for e in required_envs),
    reason="Real server credentials not set in environment"
)

def _test_file_transfer(conn, tmp_content=b"test123", remote_name="hai_test_file.txt"):
    # Create a temp file to upload
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(tmp_content)
        tmp.flush()
        local_path = tmp.name
    remote_path = f"/tmp/{remote_name}"
    # Upload
    assert upload_file(conn, local_path, remote_path, compress=False)
    # Download to a new temp file
    download_path = local_path + ".downloaded"
    assert download_file(conn, remote_path, download_path, decompress=False)
    # Check content
    with open(download_path, "rb") as f:
        assert f.read() == tmp_content
    os.remove(local_path)
    os.remove(download_path)

@skip_if_no_env
def test_linux_ssh_full():
    server = build_server_entry("LINUX", "ssh", "linux")
    conn = connect_with_fallback(server)
    # Command
    out, err = conn.exec_command("whoami")
    assert server.user in out
    # File transfer
    _test_file_transfer(conn)
    conn.disconnect()

@skip_if_no_env
def test_windows_smb_full():
    server = build_server_entry("WINDOWS", "smb", "windows")
    conn = connect_with_fallback(server)
    # List shares (if implemented)
    if hasattr(conn, "list_shares"):
        shares = conn.list_shares()
        assert isinstance(shares, list)
    # File transfer
    _test_file_transfer(conn, tmp_content=b"smbtest", remote_name="hai_test_file_smb.txt")
    conn.disconnect()

@skip_if_no_env
def test_windows_wmi_full():
    server = build_server_entry("WINDOWS", "impacket", "windows")
    conn = connect_with_fallback(server)
    # Command
    out, err = conn.exec_command("whoami")
    assert server.user.lower() in out.lower()
    # File transfer
    _test_file_transfer(conn, tmp_content=b"wmismbtest", remote_name="hai_test_file_wmi.txt")
    conn.disconnect() 