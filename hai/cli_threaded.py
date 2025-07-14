#!/usr/bin/env python3
"""
CLI script for running threaded operations on multiple servers.

Usage examples:
    python cli_threaded.py --command "whoami" --servers server01,server02
    python cli_threaded.py --command "ls -la" --servers all --workers 20
    python cli_threaded.py --commands "whoami,pwd,uname -a" --servers all
    python cli_threaded.py --upload /local/file.txt /remote/file.txt --servers all --compress
    python cli_threaded.py --download /remote/file.txt /local/file.txt --servers all --decompress
"""

import argparse
import json
import sys

from core.threaded_operations import (
    run_command_on_servers,
    run_commands_on_servers,
    upload_file_to_servers,
    download_file_from_servers
)
from core.server_schema import ServerEntry
from utils.constants import DEFAULT_MAX_WORKERS, DEFAULT_TIMEOUT, MAX_OUTPUT_LENGTH

def load_servers(servers_file="servers/servers.json"):
    """Load servers from JSON file."""
    try:
        with open(servers_file, 'r') as f:
            servers_data = json.load(f)
        
        servers = []
        for server_data in servers_data:
            server = ServerEntry(**server_data)
            servers.append(server)
        
        return servers
    except FileNotFoundError:
        print(f"Error: Servers file not found: {servers_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in servers file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading servers: {e}")
        sys.exit(1)

def filter_servers(servers, server_names):
    """Filter servers by name."""
    if server_names == "all":
        return servers
    
    server_names_list = [name.strip() for name in server_names.split(",")]
    filtered_servers = []
    
    for server in servers:
        if server.hostname in server_names_list:
            filtered_servers.append(server)
    
    # Check if all requested servers were found
    found_names = {server.hostname for server in filtered_servers}
    missing_names = set(server_names_list) - found_names
    
    if missing_names:
        print(f"Warning: Servers not found: {', '.join(missing_names)}")
    
    return filtered_servers

def main():
    parser = argparse.ArgumentParser(
        description="Run threaded operations on multiple servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Server selection
    parser.add_argument(
        "--servers", 
        required=True,
        help="Comma-separated list of server names or 'all' for all servers"
    )
    
    parser.add_argument(
        "--servers-file",
        default="servers/servers.json",
        help="Path to servers JSON file (default: servers/servers.json)"
    )
    
    # Operation type
    operation_group = parser.add_mutually_exclusive_group(required=True)
    operation_group.add_argument(
        "--command",
        help="Single command to run on servers"
    )
    
    operation_group.add_argument(
        "--commands",
        help="Comma-separated list of commands to run on servers"
    )
    
    operation_group.add_argument(
        "--upload",
        nargs=2,
        metavar=("LOCAL_PATH", "REMOTE_PATH"),
        help="Upload file from local path to remote path"
    )
    
    operation_group.add_argument(
        "--download",
        nargs=2,
        metavar=("REMOTE_PATH", "LOCAL_PATH"),
        help="Download file from remote path to local path"
    )
    
    # Options
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f"Maximum number of worker threads (default: {DEFAULT_MAX_WORKERS})"
    )
    
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar"
    )
    
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Enable compression for file transfers"
    )
    
    parser.add_argument(
        "--decompress",
        action="store_true",
        help="Enable decompression for file downloads"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Connection timeout in seconds (default: {DEFAULT_TIMEOUT})"
    )
    
    args = parser.parse_args()
    
    # Load servers
    print(f"Loading servers from {args.servers_file}...")
    all_servers = load_servers(args.servers_file)
    
    # Filter servers
    servers = filter_servers(all_servers, args.servers)
    
    if not servers:
        print("Error: No servers found matching the specified criteria")
        sys.exit(1)
    
    print(f"Running operation on {len(servers)} servers...")
    
    # Run operation
    try:
        if args.command:
            results = run_command_on_servers(
                servers=servers,
                command=args.command,
                max_workers=args.workers,
                show_progress=not args.no_progress,
                timeout=args.timeout
            )
            
        elif args.commands:
            commands = [cmd.strip() for cmd in args.commands.split(",")]
            results = run_commands_on_servers(
                servers=servers,
                commands=commands,
                max_workers=args.workers,
                show_progress=not args.no_progress,
                timeout=args.timeout
            )
            
        elif args.upload:
            local_path, remote_path = args.upload
            results = upload_file_to_servers(
                servers=servers,
                local_path=local_path,
                remote_path=remote_path,
                compress=args.compress,
                max_workers=args.workers,
                show_progress=not args.no_progress,
                timeout=args.timeout
            )
            
        elif args.download:
            remote_path, local_path = args.download
            results = download_file_from_servers(
                servers=servers,
                remote_path=remote_path,
                local_path=local_path,
                decompress=args.decompress,
                max_workers=args.workers,
                show_progress=not args.no_progress,
                timeout=args.timeout
            )
        
        # Display results
        print("\n" + "="*50)
        print("OPERATION RESULTS")
        print("="*50)
        print(f"Total servers: {results.total_servers}")
        print(f"Successful: {results.total_successful}")
        print(f"Failed: {results.total_failed}")
        print(f"Success rate: {results.success_rate:.1f}%")
        print(f"Execution time: {results.execution_time:.2f} seconds")
        
        if results.successful:
            print(f"\nSuccessful servers ({len(results.successful)}):")
            for result in results.successful:
                print(f"  ✓ {result.server.hostname}")
                if hasattr(result, 'result') and 'output' in result.result:
                    output = result.result['output'].strip()
                    if output:
                        print(f"    Output: {output[:MAX_OUTPUT_LENGTH]}{'...' if len(output) > MAX_OUTPUT_LENGTH else ''}")
        
        if results.failed:
            print(f"\nFailed servers ({len(results.failed)}):")
            for result in results.failed:
                print(f"  ✗ {result.server.hostname}: {result.error}")
        
        # Exit with error code if any servers failed
        if results.failed:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running operation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 