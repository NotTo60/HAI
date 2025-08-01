import os
import tempfile
import pytest

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from hai.core.connection_manager import connect_with_fallback
from hai.core.server_schema import ServerEntry, TunnelRoute, TunnelHop
from hai.core.file_transfer import upload_file, download_file

# Helper to build a minimal ServerEntry for each protocol
def build_server_entry(prefix, method, os_type):
    # For Linux SSH, use SSH key instead of password
    if prefix == "LINUX" and method == "ssh":
        ssh_key_path = os.environ.get("TEST_LINUX_SSH_KEY", "terraform/id_rsa")
        password = None
        ssh_key = ssh_key_path
    else:
        # For Windows, use the known password set by Terraform
        if prefix == "WINDOWS":
            password = "TemporaryPassword123!"  # Password set by Terraform user_data
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
    "TEST_LINUX_USER", "TEST_LINUX_SSH_KEY",  # IP comes from CI workflow, not secrets
    # TEST_WINDOWS_PASS no longer needed - password is set by Terraform to "TemporaryPassword123!"
]

ftp_envs = ["TEST_FTP_HOST", "TEST_FTP_USER", "TEST_FTP_PASS"]
skip_if_no_ftp = pytest.mark.skipif(
    not all(os.environ.get(e) for e in ftp_envs),
    reason="FTP server credentials not set in environment"
)

skip_if_no_env = pytest.mark.skipif(
    not all(os.environ.get(e) for e in required_envs),
    reason="Real server credentials not set in environment"
)

def _test_file_transfer(conn, tmp_content=b"test123", remote_name="hai_test_file.txt", use_scp=False):
    # Create a temp file to upload
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(tmp_content)
        tmp.flush()
        local_path = tmp.name
    remote_path = f"/tmp/{remote_name}"
    # Upload
    assert upload_file(conn, local_path, remote_path, compress=False, use_scp=use_scp)
    # Download to a new temp file
    download_path = local_path + ".downloaded"
    assert download_file(conn, remote_path, download_path, decompress=False, use_scp=use_scp)
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
    # File transfer (SFTP)
    _test_file_transfer(conn)
    conn.disconnect()

@skip_if_no_env
def test_linux_ssh_scp():
    server = build_server_entry("LINUX", "ssh", "linux")
    conn = connect_with_fallback(server)
    # Command
    out, err = conn.exec_command("whoami")
    assert server.user in out
    # File transfer (SCP)
    _test_file_transfer(conn, use_scp=True)
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
    server = build_server_entry("WINDOWS", "custom", "windows")
    conn = connect_with_fallback(server)
    # Command
    out, err = conn.exec_command("whoami")
    assert server.user.lower() in out.lower()
    # File transfer
    _test_file_transfer(conn, tmp_content=b"wmismbtest", remote_name="hai_test_file_wmi.txt")
    conn.disconnect() 

@skip_if_no_ftp
def test_ftp_full():
    server = ServerEntry(
        hostname="ftp-test",
        ip=os.environ["TEST_FTP_HOST"],
        dns="",
        location="test-lab",
        user=os.environ["TEST_FTP_USER"],
        password=os.environ["TEST_FTP_PASS"],
        ssh_key=None,
        connection_method="ftp",
        port=int(os.environ.get("TEST_FTP_PORT", 21)),
        active=True,
        grade="must-win",
        tool=None,
        os="linux",
        tunnel_routes=[TunnelRoute(name="direct", active=True, hops=[TunnelHop(ip=os.environ["TEST_FTP_HOST"], user=os.environ["TEST_FTP_USER"], method="ftp", port=int(os.environ.get("TEST_FTP_PORT", 21)))])],
        file_transfer_protocol="ftp",
        config=None
    )
    conn = connect_with_fallback(server)
    _test_file_transfer(conn, tmp_content=b"ftptest", remote_name="hai_test_file_ftp.txt")
    conn.disconnect() 