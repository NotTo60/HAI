# Windows SMB Setup & Diagnostics Script
# Run as Administrator

# Error handling
$ErrorActionPreference = "Stop"
$LogFile = "C:\Windows\Temp\smb_setup.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage
}

try {
    Write-Log "Starting SMB setup and configuration..."

    # 1. Enable Specific SMB Firewall Rules (more secure)
    Write-Log "Enabling specific SMB firewall rules..."
    Enable-NetFirewallRule -DisplayName "File and Printer Sharing (SMB-In)" -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "Allow SMB Inbound" -Direction Inbound -LocalPort 445 -Protocol TCP -Action Allow -Profile Any -ErrorAction SilentlyContinue

    # 2. Ensure SMB Server Service is Running
    Write-Log "Ensuring 'Server' service is running..."
    Set-Service -Name 'LanmanServer' -StartupType Automatic
    Start-Service -Name 'LanmanServer'
    if ((Get-Service -Name 'LanmanServer').Status -ne 'Running') {
        throw "Failed to start LanmanServer service"
    }

    # 3. Enable SMB2 and SMB3 (disable SMB1 for security)
    Write-Log "Configuring SMB protocols..."
    Set-SmbServerConfiguration -EnableSMB2Protocol $true -Force
    Set-SmbServerConfiguration -EnableSMB3Protocol $true -Force
    Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force  # Disable SMB1 for security

    # 4. Create TestShare with Better Security
    $sharePath = "C:\TestShare"
    if (-Not (Test-Path $sharePath)) {
        Write-Log "Creating folder $sharePath..."
        New-Item -Path $sharePath -ItemType Directory | Out-Null
    }

    # Remove existing share if it exists
    $existingShare = Get-SmbShare -Name "TestShare" -ErrorAction SilentlyContinue
    if ($existingShare) {
        Write-Log "Removing existing TestShare..."
        Remove-SmbShare -Name "TestShare" -Force
    }

    Write-Log "Creating SMB share 'TestShare' with restricted permissions..."
    New-SmbShare -Name "TestShare" -Path $sharePath -FullAccess "Administrators" -ChangeAccess "Everyone" -CachingMode None

    # 5. Set NTFS Permissions (more secure)
    Write-Log "Setting NTFS permissions..."
    $acl = Get-Acl $sharePath
    # Remove existing Everyone permissions
    $acl.Access | Where-Object {$_.IdentityReference -eq "Everyone"} | ForEach-Object { $acl.RemoveAccessRule($_) }
    # Add new permissions
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone","Modify","ContainerInherit,ObjectInherit","None","Allow")
    $acl.SetAccessRule($rule)
    Set-Acl $sharePath $acl

    # 6. Configure SMB Security Settings (more secure)
    Write-Log "Configuring SMB security settings..."
    Set-SmbServerConfiguration -RequireSecuritySignature $true -Force
    Set-SmbServerConfiguration -EnableGuestAccess $false -Force  # Disable guest access for security
    Set-SmbServerConfiguration -RestrictNullSessAccess $true -Force
    Set-SmbServerConfiguration -RestrictNullSessPipes $true -Force
    Set-SmbServerConfiguration -RestrictNullSessShares $true -Force

    # 7. Create test file
    Write-Log "Creating test file..."
    "This is a test file for SMB connectivity - $(Get-Date)" | Out-File -FilePath "$sharePath\test.txt" -Encoding ASCII

    # 8. Restart SMB services to apply changes
    Write-Log "Restarting SMB services..."
    Restart-Service -Name "LanmanServer" -Force
    Start-Sleep -Seconds 5

    # 9. Output Diagnostics
    Write-Log "=== SMB Setup Complete ==="
    Write-Log "SMB Server Configuration:"
    Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol, EnableSMB3Protocol, RequireSecuritySignature, EnableGuestAccess, RestrictNullSessAccess | Format-Table
    Write-Log "SMB Shares:"
    Get-SmbShare | Format-Table
    Write-Log "SMB Share Permissions:"
    Get-SmbShareAccess -Name TestShare | Format-Table
    Write-Log "Test file contents:"
    Get-Content "$sharePath\test.txt"
    Write-Log "Setup completed successfully!"

} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    Write-Log "Stack trace: $($_.ScriptStackTrace)"
    throw
} 