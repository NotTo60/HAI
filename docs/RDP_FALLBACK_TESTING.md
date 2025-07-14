# RDP Fallback Testing Documentation

This document describes the enhanced Windows connectivity testing functionality that includes RDP fallback when SMB fails.

## Overview

The HAI project now includes enhanced Windows connectivity testing that:
1. **Tests SMB connectivity first** (port 445)
2. **Falls back to RDP testing** if SMB fails (port 3389)
3. **Exits with an error** if both protocols fail (as requested)

This provides comprehensive connectivity validation for Windows instances in various network configurations.

## Test Scripts

### 1. Bash Script (`tests/test_windows_connectivity_with_rdp_fallback.sh`)

**Usage:**
```bash
./test_windows_connectivity_with_rdp_fallback.sh <target_ip> [password]
```

**Features:**
- Cross-platform compatibility (Linux, macOS)
- Automatic smbclient installation
- Comprehensive SMB protocol testing
- RDP port connectivity validation
- Detailed error reporting and troubleshooting

**Example:**
```bash
# Test with anonymous access
./test_windows_connectivity_with_rdp_fallback.sh 192.168.1.100

# Test with credentials
./test_windows_connectivity_with_rdp_fallback.sh 192.168.1.100 mypassword
```

### 2. PowerShell Script (`tests/test_windows_connectivity_with_rdp_fallback.ps1`)

**Usage:**
```powershell
.\test_windows_connectivity_with_rdp_fallback.ps1 -TargetIP <ip> [-Password <password>]
```

**Features:**
- Native Windows PowerShell implementation
- Integrated with Windows networking APIs
- Automatic credential handling
- Detailed SMB share enumeration

**Example:**
```powershell
# Test with anonymous access
.\test_windows_connectivity_with_rdp_fallback.ps1 -TargetIP 192.168.1.100

# Test with credentials
.\test_windows_connectivity_with_rdp_fallback.ps1 -TargetIP 192.168.1.100 -Password mypassword
```

### 3. Python Script (`tests/test_windows_connectivity_with_rdp_fallback.py`)

**Usage:**
```bash
python test_windows_connectivity_with_rdp_fallback.py <target_ip> [password]
```

**Features:**
- Integration with HAI project
- Cross-platform compatibility
- Structured error handling
- Extensible for automation

**Example:**
```bash
# Test with anonymous access
python test_windows_connectivity_with_rdp_fallback.py 192.168.1.100

# Test with credentials
python test_windows_connectivity_with_rdp_fallback.py 192.168.1.100 mypassword
```

## Test Flow

### Phase 1: SMB Testing
1. **Port Connectivity Check**: Tests if port 445 is reachable
2. **Anonymous Access**: Attempts SMB enumeration without credentials
3. **Authenticated Access**: Tests with Administrator credentials (if provided)
4. **Share Validation**: Verifies TestShare or C$ share accessibility

### Phase 2: RDP Fallback (if SMB fails)
1. **Port Connectivity Check**: Tests if port 3389 is reachable
2. **Connection Validation**: Attempts TCP connection to RDP port
3. **Service Verification**: Confirms RDP service is responding

### Phase 3: Result Reporting
- **Success**: SMB working (exit 0)
- **Partial Success**: SMB failed, RDP working (exit 1)
- **Failure**: Both protocols failed (exit 1)

## Expected Results

### Scenario 1: SMB Success
```
=== FINAL RESULT ===
✅ SMB CONNECTIVITY SUCCESSFUL
Windows SMB connectivity is working properly
No need to test RDP - SMB is sufficient
```
**Exit Code:** 0

### Scenario 2: SMB Failure, RDP Success
```
=== FINAL RESULT ===
⚠️  SMB FAILED but RDP SUCCESSFUL
SMB connectivity failed, but RDP connectivity is working
Windows instance is reachable via RDP (port 3389)

RDP connection command (for manual testing):
xfreerdp /v:192.168.1.100 /u:Administrator /p:"<password>" /cert:ignore

Troubleshooting SMB issues:
- Check Windows Firewall rules for SMB (port 445)
- Verify SMB service is running on Windows
- Ensure TestShare is created with proper permissions
- Check Administrator password and account status
- Verify SMB protocol versions are enabled
```
**Exit Code:** 1 (as requested)

### Scenario 3: Both Protocols Fail
```
=== FINAL RESULT ===
❌ BOTH SMB AND RDP CONNECTIVITY FAILED
Windows instance is not reachable via either protocol

Debugging information:
- Target IP: 192.168.1.100
- SMB port 445: Not accessible
- RDP port 3389: Not accessible

Possible issues:
- Windows instance may not be running
- Network connectivity issues
- Firewall blocking both ports
- Instance security groups not configured properly
- Windows services not started
```
**Exit Code:** 1

## Integration with CI/CD

### GitHub Actions Integration
The scripts can be integrated into CI/CD pipelines:

```yaml
- name: Test Windows Connectivity with RDP Fallback
  run: |
    if [[ "$RUNNER_OS" == "Windows" ]]; then
      pwsh tests/test_windows_connectivity_with_rdp_fallback.ps1 -TargetIP ${{ inputs.windows_ip }}
    else
      bash tests/test_windows_connectivity_with_rdp_fallback.sh ${{ inputs.windows_ip }}
    fi
```

### Terraform Integration
Use with Terraform outputs for automated testing:

```bash
# Get Windows IP from Terraform
WINDOWS_IP=$(terraform output -raw windows_instance_ip)

# Test connectivity
python tests/test_windows_connectivity_with_rdp_fallback.py "$WINDOWS_IP"
```

## Troubleshooting

### Common SMB Issues
1. **Port 445 not reachable**
   - Check Windows Firewall settings
   - Verify security group rules
   - Ensure SMB service is running

2. **Authentication failures**
   - Verify Administrator password
   - Check account status and permissions
   - Test with different domain/workgroup settings

3. **Share not accessible**
   - Ensure TestShare is created
   - Check share permissions
   - Verify SMB protocol versions

### Common RDP Issues
1. **Port 3389 not reachable**
   - Check Windows Firewall rules
   - Verify security group configuration
   - Ensure RDP service is enabled

2. **Connection timeouts**
   - Check network connectivity
   - Verify instance is running
   - Test with different RDP clients

## Security Considerations

### SMB Security
- **Anonymous access**: Disabled by default in production
- **Guest access**: Disabled for security
- **Protocol versions**: SMB2/SMB3 preferred over SMB1
- **Authentication**: Strong passwords required

### RDP Security
- **Network Level Authentication**: Enabled by default
- **Certificate validation**: Required for production
- **Firewall rules**: Restrict access to authorized IPs
- **User permissions**: Limit RDP access to necessary users

## Best Practices

### Testing Strategy
1. **Start with SMB**: Primary protocol for file operations
2. **Fallback to RDP**: Secondary protocol for remote access
3. **Comprehensive logging**: Document all test results
4. **Error handling**: Provide actionable troubleshooting steps

### Automation
1. **Use Python script**: For CI/CD integration
2. **Parameterize credentials**: Use environment variables
3. **Handle timeouts**: Set appropriate timeout values
4. **Log results**: Store test results for analysis

### Monitoring
1. **Regular testing**: Schedule connectivity tests
2. **Alert on failures**: Notify on connectivity issues
3. **Track trends**: Monitor success/failure rates
4. **Document changes**: Log configuration modifications

## Future Enhancements

### Planned Features
1. **Additional protocols**: Support for other Windows protocols
2. **Performance metrics**: Connection speed and latency testing
3. **Automated remediation**: Self-healing connectivity issues
4. **Integration APIs**: REST API for remote testing

### Extensibility
1. **Plugin architecture**: Support for custom protocols
2. **Configuration management**: Centralized test configuration
3. **Reporting dashboard**: Web-based test results
4. **Alert integration**: Connect to monitoring systems

## Support

For issues or questions regarding the RDP fallback testing:

1. **Check logs**: Review detailed error messages
2. **Verify configuration**: Ensure proper setup
3. **Test manually**: Use provided connection commands
4. **Review documentation**: Check troubleshooting guides
5. **Submit issues**: Report problems with detailed information 