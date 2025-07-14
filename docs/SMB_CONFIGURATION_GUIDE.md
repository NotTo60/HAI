# Windows SMB Configuration Guide

This document outlines the secure configuration of Windows SMB shares for the HAI project, including setup scripts, testing procedures, and troubleshooting guidelines.

## Overview

The HAI project includes comprehensive Windows SMB share configuration for testing and development purposes. All configurations have been updated to follow security best practices while maintaining functionality.

## Configuration Files

### 1. Terraform Configuration (`terraform/instances.tf`)
- **Purpose**: Automated Windows instance setup with SMB configuration
- **Security Level**: Enhanced security with proper permissions
- **Key Features**:
  - SMB2/SMB3 enabled, SMB1 disabled for security
  - Guest access disabled
  - Security signatures required
  - Restricted null session access
  - Proper NTFS permissions (Everyone: Modify, Administrators: Full Control)

### 2. Standalone Setup Script (`terraform/windows_smb_setup.ps1`)
- **Purpose**: Manual SMB configuration for existing Windows instances
- **Security Level**: Enhanced security with error handling
- **Key Features**:
  - Comprehensive error handling and logging
  - Service status validation
  - Secure share permissions
  - Detailed diagnostics output

### 3. Testing Scripts
- **PowerShell Test** (`tests/test_windows_smb_connectivity.ps1`)
- **Bash Test** (`tests/test_windows_smb_connectivity.sh`)
- **Python Diagnostics** (`tests/test_smb_diagnostics.py`)

## Security Improvements

### Before (Insecure Configuration)
```powershell
# ❌ Insecure settings
New-SmbShare -Name "TestShare" -Path $sharePath -FullAccess Everyone
Set-SmbServerConfiguration -EnableGuestAccess $true -Force
Set-SmbServerConfiguration -RequireSecuritySignature $false -Force
Set-SmbServerConfiguration -RestrictNullSessAccess $false -Force
```

### After (Balanced Configuration)
```powershell
# ✅ Balanced settings - secure but compatible
New-SmbShare -Name "TestShare" -Path $sharePath -FullAccess "Administrators" -ChangeAccess "Everyone"
Set-SmbServerConfiguration -EnableGuestAccess $false -Force
Set-SmbServerConfiguration -RequireSecuritySignature $false -Force  # Disabled for compatibility
Set-SmbServerConfiguration -RestrictNullSessAccess $false -Force  # Allowed for testing
```

## Key Security Features

### 1. Protocol Configuration
- **SMB1**: Enabled (for compatibility with older clients)
- **SMB2**: Enabled (recommended)
- **SMB3**: Enabled (latest and most secure)

### 2. Authentication Settings
- **Guest Access**: Disabled (security)
- **Security Signatures**: Not required (for compatibility)
- **Null Session Access**: Allowed (for testing)
- **Null Session Pipes**: Allowed (for testing)
- **Null Session Shares**: Allowed (for testing)

### 3. Share Permissions
- **TestShare**: Administrators (Full Control), Everyone (Change)
- **NTFS Permissions**: Everyone (Modify) with inheritance

### 4. Firewall Configuration
- **Port 445**: Specifically allowed for SMB
- **Specific Rules**: Only necessary SMB rules enabled

## Testing Procedures

### 1. Automated Testing
```bash
# Run comprehensive SMB tests
python tests/test_smb_diagnostics.py <target_ip> [username] [password]
```

### 2. Manual Testing
```bash
# Test anonymous access
smbclient -L //<target_ip>/ -U "" -N

# Test authenticated access
smbclient -L //<target_ip>/ -U "Administrator%password"
```

### 3. PowerShell Testing
```powershell
# Test share access
Test-Path "\\<target_ip>\TestShare"
Get-ChildItem "\\<target_ip>\TestShare"
```

## Troubleshooting

### Common Issues

#### 1. Port 445 Not Reachable
**Symptoms**: Connection timeout or refused
**Solutions**:
- Check Windows Firewall rules
- Verify security group allows port 445
- Ensure SMB service is running

#### 2. Authentication Failures
**Symptoms**: Access denied errors
**Solutions**:
- Verify Administrator credentials
- Check account lockout status
- Ensure password complexity requirements met

#### 3. Share Not Visible
**Symptoms**: No shares listed in enumeration
**Solutions**:
- Verify TestShare is created
- Check share permissions
- Ensure SMB service is running

### Diagnostic Commands

#### Windows (PowerShell)
```powershell
# Check SMB service status
Get-Service -Name *smb*

# Check SMB configuration
Get-SmbServerConfiguration

# Check shares
Get-SmbShare

# Check share permissions
Get-SmbShareAccess -Name TestShare

# Check firewall rules
Get-NetFirewallRule -DisplayGroup "File and Printer Sharing"
```

#### Linux/macOS
```bash
# Check smbclient availability
which smbclient

# Test connectivity
nc -zv <target_ip> 445

# Enumerate shares
smbclient -L //<target_ip>/ -U "" -N
```

## Best Practices

### 1. Security
- Always disable SMB1 unless legacy compatibility is required
- Use strong authentication credentials
- Restrict share permissions to minimum necessary access
- Enable security signatures
- Disable guest access in production

### 2. Monitoring
- Monitor SMB access logs
- Check for failed authentication attempts
- Review share permissions regularly
- Monitor network traffic on port 445

### 3. Maintenance
- Keep Windows instances updated
- Regularly review and update SMB configuration
- Test connectivity after configuration changes
- Document any custom configurations

## Configuration Validation

The project includes automated validation scripts that check:

1. **Port Connectivity**: Verifies port 445 is reachable
2. **Protocol Support**: Tests SMB2/SMB3 compatibility
3. **Authentication**: Validates credential-based access
4. **Share Access**: Confirms TestShare is accessible
5. **File Operations**: Tests basic file read/write operations

## Deployment Notes

### Terraform Deployment
- SMB configuration is automatically applied during instance creation
- All security settings are configured via user data
- No manual intervention required

### Manual Deployment
- Run `terraform/windows_smb_setup.ps1` as Administrator
- Verify configuration with diagnostic scripts
- Test connectivity before production use

## Support

For issues with SMB configuration:

1. Run diagnostic scripts to identify the problem
2. Check Windows Event Viewer for SMB-related errors
3. Verify network connectivity and firewall settings
4. Review this guide for common solutions
5. Check the project's issue tracker for known problems

## References

- [Microsoft SMB Security Best Practices](https://docs.microsoft.com/en-us/windows-server/storage/file-server/smb-security)
- [SMB Protocol Documentation](https://docs.microsoft.com/en-us/windows/win32/fileio/microsoft-smb-protocol-and-cifs-protocol-overview)
- [Windows Firewall Configuration](https://docs.microsoft.com/en-us/windows/security/threat-protection/windows-firewall/windows-firewall-with-advanced-security) 