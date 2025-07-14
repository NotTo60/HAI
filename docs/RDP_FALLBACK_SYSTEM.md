# RDP Fallback System Documentation

## Overview

The HAI project includes a comprehensive RDP fallback system that provides robust Windows connectivity testing with automatic fallback from SMB to RDP when SMB connectivity fails. This system ensures maximum connectivity success rates for Windows servers.

## System Architecture

### Components

1. **Test Scripts** - Standalone scripts for quick connectivity testing
2. **Windows Connectivity Module** - Integrated Python module for programmatic use
3. **Integration Tests** - Comprehensive test suite validating all functionality
4. **Example Scripts** - Usage examples and demonstrations

### Workflow

```
SMB Test → Success? → Yes → Exit Success
         ↓ No
RDP Test → Success? → Yes → Exit with Warning
         ↓ No
         → Exit with Error
```

## Test Scripts

### 1. Bash Script (`tests/test_windows_connectivity_with_rdp_fallback.sh`)

**Features:**
- Cross-platform bash script
- SMB connectivity testing using `smbclient`
- RDP port connectivity testing
- Detailed error reporting
- Configurable timeouts and retries

**Usage:**
```bash
# Test with default settings
./tests/test_windows_connectivity_with_rdp_fallback.sh 192.168.1.100

# Test with custom credentials
./tests/test_windows_connectivity_with_rdp_fallback.sh 192.168.1.100 -u Administrator -p password

# Test with help
./tests/test_windows_connectivity_with_rdp_fallback.sh --help
```

**Exit Codes:**
- `0` - SMB connectivity successful
- `1` - SMB failed but RDP successful, or both failed

### 2. PowerShell Script (`tests/test_windows_connectivity_with_rdp_fallback.ps1`)

**Features:**
- Native Windows PowerShell script
- SMB connectivity testing using `Test-NetConnection`
- RDP port connectivity testing
- Detailed status reporting
- Error handling and logging

**Usage:**
```powershell
# Test with default settings
.\tests\test_windows_connectivity_with_rdp_fallback.ps1 -TargetIP "192.168.1.100"

# Test with custom credentials
.\tests\test_windows_connectivity_with_rdp_fallback.ps1 -TargetIP "192.168.1.100" -Username "Administrator" -Password "password"

# Test with help
.\tests\test_windows_connectivity_with_rdp_fallback.ps1 -Help
```

### 3. Python Script (`tests/test_windows_connectivity_with_rdp_fallback.py`)

**Features:**
- Cross-platform Python script
- SMB connectivity testing using `subprocess` and `smbclient`
- RDP port connectivity testing using `socket`
- Configurable timeouts and retry logic
- Detailed logging and error reporting

**Usage:**
```bash
# Test with default settings
python tests/test_windows_connectivity_with_rdp_fallback.py 192.168.1.100

# Test with custom credentials
python tests/test_windows_connectivity_with_rdp_fallback.py 192.168.1.100 --password "password"

# Test with help
python tests/test_windows_connectivity_with_rdp_fallback.py --help
```

## Windows Connectivity Module

### Core Classes

#### `WindowsConnectivityTester`

The main class for testing Windows connectivity with RDP fallback.

**Methods:**
- `test_port_connectivity(host, port, timeout)` - Test if a port is reachable
- `test_smb_connectivity(host, username, password)` - Test SMB connectivity
- `test_rdp_connectivity(host)` - Test RDP connectivity
- `test_windows_connectivity(server)` - Complete Windows connectivity test with fallback

**Example:**
```python
from hai.core.windows_connectivity import WindowsConnectivityTester
from hai.core.server_schema import ServerEntry

# Create tester
tester = WindowsConnectivityTester()

# Create server entry
server = ServerEntry(
    hostname="test-server",
    ip="192.168.1.100",
    user="Administrator",
    password="password",  # pragma: allowlist secret
    connection_method="smb",
    port=445,
    os="windows"
)

# Test connectivity
result = tester.test_windows_connectivity(server)
print(f"Success: {result['overall_success']}")
print(f"Protocol: {result['primary_protocol']}")
print(f"Fallback used: {result['fallback_used']}")
```

### Convenience Functions

#### `check_windows_connectivity(server)`

Test connectivity for a single Windows server.

**Returns:**
```python
{
    "overall_success": bool,
    "primary_protocol": str,  # "smb" or "rdp"
    "fallback_used": bool,
    "smb_result": dict,
    "rdp_result": dict or None
}
```

#### `check_multiple_windows_servers(servers)`

Test connectivity for multiple servers, filtering for Windows servers only.

**Returns:**
```python
{
    "total_servers": int,
    "successful": int,
    "failed": int,
    "smb_only": int,
    "rdp_fallback": int,
    "both_failed": int,
    "server_results": list
}
```

## Integration Tests

### Test Coverage

The integration test suite (`tests/test_rdp_fallback_integration.py`) provides comprehensive coverage:

1. **Script Availability** - Verify all test scripts exist and are executable
2. **Help Output** - Test that all scripts provide proper help information
3. **SMB Success Scenarios** - Test when SMB connectivity succeeds
4. **RDP Fallback Scenarios** - Test when SMB fails but RDP succeeds
5. **Both Fail Scenarios** - Test when both protocols fail
6. **Module Integration** - Test integration with Windows connectivity module
7. **Complete Workflows** - Test end-to-end workflows
8. **Error Handling** - Test error handling and logging
9. **Multiple Servers** - Test multiple servers workflow
10. **Documentation Consistency** - Verify documentation matches implementation
11. **Example Script Execution** - Test example script functionality

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run only integration tests
python -m pytest tests/test_rdp_fallback_integration.py -v

# Run with coverage
python -m pytest tests/ --cov=hai --cov-report=html
```

## Example Usage

### Basic Usage

```python
from hai.core.windows_connectivity import check_windows_connectivity
from hai.core.server_schema import ServerEntry

# Create a server entry
server = ServerEntry(
    hostname="windows-server",
    ip="192.168.1.100",
    user="Administrator",
    password="password",  # pragma: allowlist secret
    connection_method="smb",
    port=445,
    os="windows"
)

# Test connectivity
result = check_windows_connectivity(server)

if result["overall_success"]:
    print(f"✅ Connectivity successful via {result['primary_protocol']}")
    if result["fallback_used"]:
        print("⚠️  RDP fallback was used")
else:
    print("❌ Connectivity failed")
```

### Multiple Servers

```python
from hai.core.windows_connectivity import check_multiple_windows_servers

# Test multiple servers
servers = [
    ServerEntry(hostname="server1", ip="192.168.1.100", os="windows", ...),
    ServerEntry(hostname="server2", ip="192.168.1.101", os="windows", ...),
    ServerEntry(hostname="linux-server", ip="192.168.1.102", os="linux", ...)
]

results = check_multiple_windows_servers(servers)

print(f"Total servers: {results['total_servers']}")
print(f"Successful: {results['successful']}")
print(f"SMB only: {results['smb_only']}")
print(f"RDP fallback: {results['rdp_fallback']}")
```

### Detailed Testing

```python
from hai.core.windows_connectivity import WindowsConnectivityTester

tester = WindowsConnectivityTester()

# Test individual components
port_result = tester.test_port_connectivity("192.168.1.100", 445)
smb_result = tester.test_smb_connectivity("192.168.1.100", "Administrator", "password")
rdp_result = tester.test_rdp_connectivity("192.168.1.100")

print(f"Port 445: {'✅' if port_result else '❌'}")
print(f"SMB: {'✅' if smb_result['success'] else '❌'}")
print(f"RDP: {'✅' if rdp_result['success'] else '❌'}")
```

## Configuration

### Environment Variables

The system respects the following environment variables:

- `SMB_TIMEOUT` - SMB connection timeout (default: 10 seconds)
- `RDP_TIMEOUT` - RDP connection timeout (default: 5 seconds)
- `PORT_TIMEOUT` - Port connectivity timeout (default: 5 seconds)
- `SMB_RETRIES` - Number of SMB connection retries (default: 3)

### Logging

The system uses the HAI logging framework:

```python
from hai.utils.logger import get_logger

logger = get_logger("windows_connectivity")
logger.info("Testing Windows connectivity")
logger.error("Connectivity test failed")
```

## Error Handling

### Common Error Scenarios

1. **SMB Authentication Failure**
   - Error: `NT_STATUS_LOGON_FAILURE`
   - Solution: Verify credentials and user permissions

2. **Port Connectivity Failure**
   - Error: Connection timeout
   - Solution: Check firewall settings and network connectivity

3. **RDP Port Closed**
   - Error: Connection refused
   - Solution: Enable RDP on the target server

4. **Network Timeout**
   - Error: Connection timeout
   - Solution: Check network connectivity and increase timeouts

### Troubleshooting

1. **Enable Debug Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Test Individual Components**
   ```python
   # Test port connectivity first
   tester = WindowsConnectivityTester()
   if tester.test_port_connectivity("192.168.1.100", 445):
       print("Port 445 is reachable")
   ```

3. **Check Network Connectivity**
   ```bash
   # Test basic connectivity
   ping 192.168.1.100
   telnet 192.168.1.100 445
   telnet 192.168.1.100 3389
   ```

## Security Considerations

1. **Credential Handling**
   - Passwords are handled securely and not logged
   - Use environment variables for sensitive data
   - Consider using SSH keys where possible

2. **Network Security**
   - SMB connections use authentication when possible
   - RDP fallback only tests port connectivity
   - No actual RDP connections are established

3. **Error Information**
   - Error messages are sanitized to avoid information disclosure
   - Debug logging can be enabled for troubleshooting

## Performance

### Optimization Tips

1. **Parallel Testing**
   - Use `check_multiple_windows_servers()` for multiple servers
   - Consider threading for large server lists

2. **Timeout Configuration**
   - Adjust timeouts based on network conditions
   - Use shorter timeouts for local networks

3. **Caching**
   - Results are not cached by default
   - Implement caching if testing the same servers repeatedly

## Future Enhancements

1. **Additional Protocols**
   - Support for WMI connectivity testing
   - HTTP/HTTPS connectivity testing
   - Custom protocol support

2. **Advanced Features**
   - Connection pooling
   - Automatic retry with exponential backoff
   - Health check integration

3. **Monitoring Integration**
   - Prometheus metrics
   - Grafana dashboards
   - Alert integration

## Support

For issues and questions:

1. Check the test logs for detailed error information
2. Run the integration tests to verify system functionality
3. Review the example scripts for usage patterns
4. Check the troubleshooting section for common solutions

## Contributing

When contributing to the RDP fallback system:

1. Add tests for new functionality
2. Update documentation for API changes
3. Follow the existing code style and patterns
4. Test with multiple Windows server configurations
5. Update integration tests for new features 