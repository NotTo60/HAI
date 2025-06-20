import logging
import sys

from core.command_runner import run_command, run_commands
from core.connection_manager import connect_with_fallback
from core.file_transfer import (download_file, download_files, upload_file,
                                upload_files)
from core.server_schema import ServerEntry, TunnelHop, TunnelRoute
from utils.logger import get_logger

# Setup logger to print to stdout for test visibility
logger = get_logger("connection_manager")
for handler in logger.handlers:
    handler.stream = sys.stdout

# Edge case 1: All routes inactive
server_all_inactive = ServerEntry(
    hostname="inactive01",
    ip="10.0.0.2",
    dns="inactive01.local",
    location="nowhere",
    user="user",
    password=None,
    ssh_key=None,
    connection_method="ssh",
    port=22,
    active=True,
    grade="test",
    tool=None,
    os="linux",
    tunnel_routes=[
        TunnelRoute(
            name="route1",
            active=False,
            hops=[TunnelHop(ip="1.1.1.1", user="a", method="ssh")],
        ),
        TunnelRoute(
            name="route2",
            active=False,
            hops=[TunnelHop(ip="2.2.2.2", user="b", method="ssh")],
        ),
    ],
)


# Edge case 2: All routes fail (simulate by raising in TunnelBuilder)
class FailingTunnelBuilder:
    @staticmethod
    def build(server, route):
        raise Exception("Simulated tunnel failure")


# Patch TunnelBuilder for this test
import core.tunnel_builder

orig_tb = core.tunnel_builder.TunnelBuilder
core.tunnel_builder.TunnelBuilder = FailingTunnelBuilder

server_all_fail = ServerEntry(
    hostname="fail01",
    ip="10.0.0.3",
    dns="fail01.local",
    location="nowhere",
    user="user",
    password=None,
    ssh_key=None,
    connection_method="ssh",
    port=22,
    active=True,
    grade="test",
    tool=None,
    os="linux",
    tunnel_routes=[
        TunnelRoute(
            name="route1",
            active=True,
            hops=[TunnelHop(ip="1.1.1.1", user="a", method="ssh")],
        ),
        TunnelRoute(
            name="route2",
            active=True,
            hops=[TunnelHop(ip="2.2.2.2", user="b", method="ssh")],
        ),
    ],
)


# Edge case 3: Mixed active/inactive, first active route fails, second succeeds
class MixedTunnelBuilder:
    call_count = 0

    @staticmethod
    def build(server, route):
        MixedTunnelBuilder.call_count += 1
        if MixedTunnelBuilder.call_count == 1:
            raise Exception("First route fails")

        class DummyConn:
            def is_alive(self):
                return True

        return DummyConn()


core.tunnel_builder.TunnelBuilder = MixedTunnelBuilder

server_mixed = ServerEntry(
    hostname="mixed01",
    ip="10.0.0.4",
    dns="mixed01.local",
    location="nowhere",
    user="user",
    password=None,
    ssh_key=None,
    connection_method="ssh",
    port=22,
    active=True,
    grade="test",
    tool=None,
    os="linux",
    tunnel_routes=[
        TunnelRoute(
            name="route1",
            active=True,
            hops=[TunnelHop(ip="1.1.1.1", user="a", method="ssh")],
        ),
        TunnelRoute(
            name="route2",
            active=True,
            hops=[TunnelHop(ip="2.2.2.2", user="b", method="ssh")],
        ),
    ],
)


# Edge case 4: Success on first route
class SuccessTunnelBuilder:
    @staticmethod
    def build(server, route):
        class DummyConn:
            def is_alive(self):
                return True

        return DummyConn()


core.tunnel_builder.TunnelBuilder = SuccessTunnelBuilder

server_success = ServerEntry(
    hostname="success01",
    ip="10.0.0.5",
    dns="success01.local",
    location="nowhere",
    user="user",
    password=None,
    ssh_key=None,
    connection_method="ssh",
    port=22,
    active=True,
    grade="test",
    tool=None,
    os="linux",
    tunnel_routes=[
        TunnelRoute(
            name="route1",
            active=True,
            hops=[TunnelHop(ip="1.1.1.1", user="a", method="ssh")],
        ),
        TunnelRoute(
            name="route2",
            active=True,
            hops=[TunnelHop(ip="2.2.2.2", user="b", method="ssh")],
        ),
    ],
)

print("\n--- Edge Case 1: All routes inactive ---")
try:
    connect_with_fallback(server_all_inactive)
except Exception as e:
    print(f"Expected exception: {e}")

print("\n--- Edge Case 2: All routes fail ---")
try:
    connect_with_fallback(server_all_fail)
except Exception as e:
    print(f"Expected exception: {e}")

print("\n--- Edge Case 3: Mixed active/inactive, first fails, second succeeds ---")
try:
    connect_with_fallback(server_mixed)
except Exception as e:
    print(f"Unexpected exception: {e}")

print("\n--- Edge Case 4: Success on first route ---")
try:
    connect_with_fallback(server_success)
except Exception as e:
    print(f"Unexpected exception: {e}")

# Restore original TunnelBuilder
core.tunnel_builder.TunnelBuilder = orig_tb


# DummyConn for protocol/config tests
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


# Patch TunnelBuilder for protocol/config test
import core.tunnel_builder

orig_tb = core.tunnel_builder.TunnelBuilder


class ProtocolTunnelBuilder:
    @staticmethod
    def build(server, route):
        proto = getattr(server, "file_transfer_protocol", "sftp")
        config = getattr(server, "config", {})
        return DummyConn(proto, config)


core.tunnel_builder.TunnelBuilder = ProtocolTunnelBuilder

# Test protocol selection and config passing
for proto in ["sftp", "scp", "smb", "ftp"]:
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
    print(f"\n--- Protocol: {proto} with config ---")
    conn = connect_with_fallback(server)
    out, err = run_command(conn, "echo test")
    print(f"Command output: {out}")
    upload_file(conn, "local.txt", "/remote/remote.txt", compress=True)
    download_file(conn, "/remote/remote.txt", "local.txt", decompress=True)
    upload_files(conn, ["a.txt", "b.txt"], "/remote/", compress=True)
    download_files(
        conn, ["/remote/a.txt", "/remote/b.txt"], "./downloads", compress=True
    )
    conn.disconnect()

# Test missing config
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
print(f"\n--- Protocol: sftp with missing config ---")
conn = connect_with_fallback(server)
out, err = run_command(conn, "echo test")
print(f"Command output: {out}")
conn.disconnect()

# Restore original TunnelBuilder
core.tunnel_builder.TunnelBuilder = orig_tb
