#!/usr/bin/env python3
"""
Simple demonstration of HAI threading functionality.

This script creates a few sample servers and demonstrates:
1. Running commands in parallel
2. Progress bars
3. Statistics tracking
4. Chaining operations
"""

from core.server_schema import ServerEntry, TunnelHop, TunnelRoute
from core.threaded_operations import ThreadedOperations, run_command_on_servers
from utils.constants import DEFAULT_MAX_WORKERS, DEFAULT_SSH_PORT


def create_demo_servers():
    """Create sample servers for demonstration"""
    # Create tunnel hops
    hop1 = TunnelHop(ip="10.0.0.1", user="jump1", method="ssh", port=DEFAULT_SSH_PORT)
    hop2 = TunnelHop(ip="10.1.1.1", user="jump2", method="ssh", port=DEFAULT_SSH_PORT)
    
    # Create tunnel routes
    route1 = TunnelRoute(name="via-gateway-A", active=True, hops=[hop1])
    route2 = TunnelRoute(name="via-gateway-B", active=True, hops=[hop2])
    
    # Create servers
    servers = [
        ServerEntry(
            hostname="web-server-01",
            ip="192.168.1.10",
            dns="web01.local",
            location="datacenter-east",
            user="admin",
            password="demo123",
            connection_method="ssh",
            port=DEFAULT_SSH_PORT,
            active=True,
            grade="critical",
            os="linux",
            tunnel_routes=[route1],
            file_transfer_protocol="sftp"
        ),
        ServerEntry(
            hostname="db-server-01",
            ip="192.168.1.11",
            dns="db01.local",
            location="datacenter-west",
            user="admin",
            password="demo123",
            connection_method="ssh",
            port=DEFAULT_SSH_PORT,
            active=True,
            grade="critical",
            os="linux",
            tunnel_routes=[route2],
            file_transfer_protocol="sftp"
        ),
        ServerEntry(
            hostname="app-server-01",
            ip="192.168.1.12",
            dns="app01.local",
            location="datacenter-north",
            user="admin",
            password="demo123",
            connection_method="ssh",
            port=DEFAULT_SSH_PORT,
            active=True,
            grade="important",
            os="linux",
            tunnel_routes=[route1, route2],
            file_transfer_protocol="sftp"
        ),
        ServerEntry(
            hostname="backup-server-01",
            ip="192.168.1.13",
            dns="backup01.local",
            location="datacenter-south",
            user="admin",
            password="demo123",
            connection_method="ssh",
            port=DEFAULT_SSH_PORT,
            active=True,
            grade="nice-to-have",
            os="linux",
            tunnel_routes=[route1],
            file_transfer_protocol="sftp"
        )
    ]
    
    return servers


def print_summary(results, operation_name):
    """Print a summary of operation results"""
    print(f"\n📊 {operation_name} Summary:")
    print(f"   Total servers: {results.total_servers}")
    print(f"   Successful: {results.total_successful}")
    print(f"   Failed: {results.total_failed}")
    print(f"   Success rate: {results.success_rate:.1f}%")
    print(f"   Execution time: {results.execution_time:.2f} seconds")
    
    if results.successful:
        print(f"   ✅ Successful servers: {[s.hostname for s in results.get_successful_servers()]}")
    
    if results.failed:
        print(f"   ❌ Failed servers: {[s.hostname for s in results.get_failed_servers()]}")


def main():
    """Main demonstration function"""
    print("🚀 HAI Threading Demo")
    print("=" * 50)
    
    # Create demo servers
    servers = create_demo_servers()
    print(f"Created {len(servers)} demo servers:")
    for server in servers:
        print(f"  • {server.hostname} ({server.ip}) - {server.grade}")
    
    print("\nStarting threaded operations...")
    
    # Demo 1: Basic command execution
    print("\n1️⃣ Running 'whoami' on all servers...")
    results1 = run_command_on_servers(
        servers=servers,
        command="whoami",
        max_workers=DEFAULT_MAX_WORKERS,
        show_progress=True
    )
    print_summary(results1, "whoami command")
    
    # Demo 2: System information gathering
    print("\n2️⃣ Gathering system information...")
    results2 = run_command_on_servers(
        servers=servers,
        command="uname -a && df -h",
        max_workers=DEFAULT_MAX_WORKERS,
        show_progress=True
    )
    print_summary(results2, "system info")
    
    # Demo 3: Chaining operations - retry failed servers
    if results1.failed:
        print("\n3️⃣ Retrying failed servers with alternative command...")
        failed_servers = results1.get_failed_servers()
        retry_results = run_command_on_servers(
            servers=failed_servers,
            command="echo 'Alternative approach'",
            max_workers=2,
            show_progress=True
        )
        print_summary(retry_results, "retry operation")
    else:
        print("\n3️⃣ All servers succeeded - no retry needed!")
    
    # Demo 4: Using ThreadedOperations class for more control
    print("\n4️⃣ Using ThreadedOperations class for custom operations...")
    ops = ThreadedOperations(max_workers=3)
    
    # Run multiple commands on successful servers
    successful_servers = results1.get_successful_servers()
    if successful_servers:
        print(f"Running follow-up commands on {len(successful_servers)} successful servers...")
        follow_up_results = ops.run_commands_on_servers(
            servers=successful_servers,
            commands=["pwd", "ls -la /tmp"],
            show_progress=True,
            description="Follow-up commands"
        )
        print_summary(follow_up_results, "follow-up commands")
    
    print("\n🎉 Demo completed!")
    print("💡 Key features demonstrated:")
    print("   • Parallel execution with progress bars")
    print("   • Detailed statistics and success tracking")
    print("   • Easy access to successful/failed server lists")
    print("   • Chaining operations based on results")
    print("   • Configurable worker threads")


if __name__ == "__main__":
    main() 