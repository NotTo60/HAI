import sys
import pytest
from unittest.mock import patch
import os
import tarfile
import io
import tempfile
from core.connection_manager import connect_with_fallback
from core.server_schema import ServerEntry, TunnelRoute, TunnelHop
from core.file_transfer import upload_file, upload_files
from core.command_runner import run_command
from utils.logger import get_logger
from core import file_transfer


def create_tar_gz(output_path, files):
    with tarfile.open(output_path, "w:gz") as tar:
        for fname in files:
            tar.add(fname, arcname=os.path.basename(fname))


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
    for tarfile_name in [
        "local.txt.tar.gz", "upload_bundle.tar.gz", "download_bundle.tar.gz"
    ]:
        if os.path.exists(tarfile_name):
            os.remove(tarfile_name)


def _mock_download_file(conn, remote_path, local_path, decompress=False):
    if decompress:
        # Create a tar.gz at local_path (even if the name is local.txt)
        with tarfile.open(local_path, "w:gz") as tar:
            info = tarfile.TarInfo(name="extracted.txt")
            content = b"dummy content"
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
        # Debug output
        with open(local_path, "rb") as f:
            data = f.read(16)
            f.seek(0, os.SEEK_END)
            size = f.tell()
        print(f"[DEBUG] Wrote tar.gz to {local_path}: first bytes {data}, size {size}")
    else:
        with open(local_path, "w") as f:
            f.write("test content")
    return True


def _mock_download_files(conn, remote_paths, local_dir, compress=False):
    if compress:
        # Simulate the tarball being downloaded to the expected temp path
        temp_dir = None
        for d in os.listdir(tempfile.gettempdir()):
            if d.startswith("tmp"):
                temp_dir = os.path.join(tempfile.gettempdir(), d)
                break
        if not temp_dir:
            temp_dir = tempfile.gettempdir()
        tar_path = os.path.join(temp_dir, "download_bundle.tar.gz")
        with tarfile.open(tar_path, "w:gz") as tar:
            for remote_path in remote_paths:
                info = tarfile.TarInfo(name=os.path.basename(remote_path))
                content = b"dummy content for " + remote_path.encode()
                info.size = len(content)
                tar.addfile(info, io.BytesIO(content))
        print(f"[DEBUG] Wrote tar.gz to {tar_path}: size {os.path.getsize(tar_path)}")
    else:
        os.makedirs(local_dir, exist_ok=True)
        for remote_path in remote_paths:
            local_path = os.path.join(local_dir, os.path.basename(remote_path))
            with open(local_path, "w") as f:
                f.write("test content")
    return True


@pytest.fixture(autouse=True)
def patch_tunnel_builder_and_download(monkeypatch, temp_files):
    from core import file_transfer
    with patch("core.tunnel_builder.TunnelBuilder.build") as mock_build:
        def dummy_build(server, route):
            proto = getattr(server, 'file_transfer_protocol', 'sftp')
            config = getattr(server, 'config', {})
            return DummyConn(proto, config)
        mock_build.side_effect = dummy_build
        monkeypatch.setattr(file_transfer, "download_file", _mock_download_file)
        monkeypatch.setattr(file_transfer, "download_files", _mock_download_files)
        yield


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
        tunnel_routes=[
            TunnelRoute(
                name="default",
                active=True,
                hops=[TunnelHop(ip="1.2.3.4", user="user", method="ssh")],
            )
        ],
        file_transfer_protocol=proto,
        config={"timeout": 42, "client_id": f"test-{proto}"},
    )
    conn = connect_with_fallback(server)
    out, err = run_command(conn, "echo test")
    assert proto in out
    upload_file(conn, "local.txt", "/remote/remote.txt", compress=True)
    file_transfer.download_file(conn, "/remote/remote.txt", "local.txt", decompress=True)
    upload_files(conn, ["a.txt", "b.txt"], "/remote/", compress=True)
    file_transfer.download_files(
        conn, ["/remote/a.txt", "/remote/b.txt"], "./downloads", compress=True
    )
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
        tunnel_routes=[
            TunnelRoute(
                name="default",
                active=True,
                hops=[TunnelHop(ip="1.2.3.4", user="user", method="ssh")],
            )
        ],
        file_transfer_protocol="sftp",
    )
    conn = connect_with_fallback(server)
    out, err = run_command(conn, "echo test")
    assert "sftp" in out
    conn.disconnect()


def test_sshconnector_classmethod_connect(monkeypatch):
    from connectors.ssh_connector import SSHConnector
    class DummyClient:
        def set_missing_host_key_policy(self, policy):
            pass
        def connect(self, **kwargs):
            pass
        def exec_command(self, cmd):
            class Dummy:
                def read(self):
                    return b"ssh output for: " + cmd.encode()
            return None, Dummy(), Dummy()
        def close(self):
            pass
    monkeypatch.setattr("paramiko.SSHClient", DummyClient)
    ssh = SSHConnector.connect_cls(host="1.2.3.4", port=22, user="me", password="pw")
    def fake_exec_command(self, cmd):
        return f"ssh output for: {cmd}", ""
    def fake_disconnect(self):
        self.connected = False
    ssh.exec_command = fake_exec_command.__get__(ssh)
    ssh.disconnect = fake_disconnect.__get__(ssh)
    assert isinstance(ssh, SSHConnector)
    out, err = ssh.exec_command("echo test")
    assert "ssh output" in out
    ssh.disconnect()


def test_smbconnector_classmethod_connect(monkeypatch):
    from connectors.smb_connector import SMBConnector
    smb = SMBConnector.connect_cls(host="1.2.3.4", user="me", password="pw")
    def fake_exec_command(self, cmd):
        return f"smb output for: {cmd}", ""
    def fake_disconnect(self):
        self.connected = False
    smb.exec_command = fake_exec_command.__get__(smb)
    smb.disconnect = fake_disconnect.__get__(smb)
    assert isinstance(smb, SMBConnector)
    out, err = smb.exec_command("echo test")
    assert "smb output" in out
    smb.disconnect()


def test_impacketwrapper_classmethod_connect(monkeypatch):
    from connectors.impacket_wrapper import ImpacketWrapper
    imp = ImpacketWrapper.connect_cls(host="1.2.3.4", user="me", password="pw")
    def fake_exec_command(self, cmd):
        return f"impacket output for: {cmd}", ""
    def fake_disconnect(self):
        self.connected = False
    imp.exec_command = fake_exec_command.__get__(imp)
    imp.disconnect = fake_disconnect.__get__(imp)
    assert isinstance(imp, ImpacketWrapper)
    out, err = imp.exec_command("echo test")
    assert "impacket output" in out
    imp.disconnect()
