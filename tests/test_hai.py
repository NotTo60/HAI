import sys
import pytest
from unittest.mock import patch
import os
import tarfile


def create_tar_gz(output_path, files):
    with tarfile.open(output_path, "w:gz") as tar:
        for fname in files:
            tar.add(fname, arcname=os.path.basename(fname))


from core.connection_manager import connect_with_fallback
from core.server_schema import ServerEntry, TunnelRoute, TunnelHop
from core.file_transfer import upload_file, download_file, upload_files, download_files
from core.command_runner import run_command
from utils.logger import get_logger


logger = get_logger("connection_manager")
for handler in logger.handlers:
    handler.stream = sys.stdout


class DummyConn:
    def __init__(self, protocol, config=None):
        self.protocol = protocol
        self.config = config or {}
        self.connected = False

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.connected = False

    def exec_command(self, cmd):
        return f"{self.protocol} output for: {cmd} (config: {self.config})", ""

    def is_alive(self):
        return True


@pytest.fixture
def temp_files():
    files = []
    for fname in ["local.txt", "a.txt", "b.txt"]:
        with open(fname, "w") as f:
            f.write("test content")
        files.append(fname)
    yield files
    for fname in files:
        if os.path.exists(fname):
            os.remove(fname)
    # Also clean up any tar.gz files created
    for tarfile_name in ["local.txt.tar.gz", "upload_bundle.tar.gz", "download_bundle.tar.gz"]:
        if os.path.exists(tarfile_name):
            os.remove(tarfile_name)


@pytest.fixture(autouse=True)
def patch_tunnel_builder_and_download(monkeypatch, temp_files):
    from core import file_transfer
    with patch("core.tunnel_builder.TunnelBuilder.build") as mock_build:

        def dummy_build(server, route):
            proto = getattr(server, 'file_transfer_protocol', 'sftp')
            config = getattr(server, 'config', {})
            return DummyConn(proto, config)

        mock_build.side_effect = dummy_build

        # Patch download_file to create a valid tar.gz file if decompress=True
        orig_download_file = file_transfer.download_file

        def mock_download_file(conn, remote_path, local_path, decompress=False):
            # Simulate download by copying or creating a tar.gz if decompress is requested
            if decompress:
                # Create a tar.gz containing local.txt
                tar_path = local_path
                create_tar_gz(tar_path, ["local.txt"])
            else:
                # Just create a plain file
                with open(local_path, "w") as f:
                    f.write("test content")
            return True

        monkeypatch.setattr(file_transfer, "download_file", mock_download_file)
        yield
        # Restore if needed (pytest monkeypatch handles this)


@pytest.mark.parametrize("proto", ["sftp", "scp", "smb", "ftp"])
def test_protocol_and_config(proto, temp_files):
    server = ServerEntry(
        hostname=f"proto-{proto}",
        ip="1.2.3.4",
        dns=f"proto-{proto}.local",
        location="testlab",
        user="user",
        password="pw",
        ssh_key=None,
        connection_method="ssh" if proto in ["sftp", "scp"] else proto,
        port=22,
        active=True,
        grade="test",
        tool=None,
        os="linux",
        tunnel_routes=[TunnelRoute(name="default", active=True, hops=[TunnelHop(ip="1.2.3.4", user="user", method="ssh")])],
        file_transfer_protocol=proto,
        config={"timeout": 42, "client_id": f"test-{proto}"}
    )
    conn = connect_with_fallback(server)
    out, err = run_command(conn, "echo test")
    assert proto in out
    upload_file(conn, "local.txt", "/remote/remote.txt", compress=True)
    download_file(conn, "/remote/remote.txt", "local.txt", decompress=True)
    upload_files(conn, ["a.txt", "b.txt"], "/remote/", compress=True)
    download_files(conn, ["/remote/a.txt", "/remote/b.txt"], "./downloads", compress=True)
    conn.disconnect()


def test_missing_config():
    server = ServerEntry(
        hostname="no-config",
        ip="1.2.3.4",
        dns="no-config.local",
        location="testlab",
        user="user",
        password="pw",
        ssh_key=None,
        connection_method="ssh",
        port=22,
        active=True,
        grade="test",
        tool=None,
        os="linux",
        tunnel_routes=[TunnelRoute(name="default", active=True, hops=[TunnelHop(ip="1.2.3.4", user="user", method="ssh")])],
        file_transfer_protocol="sftp"
    )
    conn = connect_with_fallback(server)
    out, err = run_command(conn, "echo test")
    assert "sftp" in out
    conn.disconnect()
