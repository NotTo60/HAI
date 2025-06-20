import sys
import pytest
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

@pytest.fixture(autouse=True)
def patch_tunnel_builder(monkeypatch):
    import core.tunnel_builder
    orig_tb = core.tunnel_builder.TunnelBuilder
    class ProtocolTunnelBuilder:
        @staticmethod
        def build(server, route):
            proto = getattr(server, 'file_transfer_protocol', 'sftp')
            config = getattr(server, 'config', {})
            return DummyConn(proto, config)
    monkeypatch.setattr(core.tunnel_builder, 'TunnelBuilder', ProtocolTunnelBuilder)
    yield
    monkeypatch.setattr(core.tunnel_builder, 'TunnelBuilder', orig_tb)

@pytest.mark.parametrize("proto", ["sftp", "scp", "smb", "ftp"])
def test_protocol_and_config(proto):
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
