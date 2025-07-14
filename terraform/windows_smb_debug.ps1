# Windows SMB Debug Setup Script
# Run as Administrator - FOR DEBUGGING ONLY

# Error handling
$ErrorActionPreference = "Stop"
$LogFile = "C:\Windows\Temp\smb_debug_setup.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage
}

try {
    Write-Log "Starting SMB debug setup and configuration..."

    # 1. Enable ALL SMB Firewall Rules (for debugging)
    Write-Log "Enabling ALL SMB firewall rules for debugging..."
    Enable-NetFirewallRule -DisplayGroup "File and Printer Sharing" -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "Allow SMB Inbound Debug" -Direction Inbound -LocalPort 445 -Protocol TCP -Action Allow -Profile Any -ErrorAction SilentlyContinue

    # 2. Ensure SMB Server Service is Running
    Write-Log "Ensuring 'Server' service is running..."
    Set-Service -Name 'LanmanServer' -StartupType Automatic
    Start-Service -Name 'LanmanServer'
    if ((Get-Service -Name 'LanmanServer').Status -ne 'Running') {
        throw "Failed to start LanmanServer service"
    }

    # 3. Configure SMB protocols (enable all for debugging)
    Write-Log "Configuring SMB protocols for debugging..."
    Set-SmbServerConfiguration -EnableSMB2Protocol $true -Force
    Set-SmbServerConfiguration -EnableSMB3Protocol $true -Force
    Set-SmbServerConfiguration -EnableSMB1Protocol $true -Force  # Enable SMB1 for debugging

    # 4. Create TestShare with OPEN permissions (for debugging)
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

    Write-Log "Creating SMB share 'TestShare' with OPEN permissions for debugging..."
    New-SmbShare -Name "TestShare" -Path $sharePath -FullAccess "Everyone" -CachingMode None

    # 5. Set NTFS permissions (OPEN for debugging)
    Write-Log "Setting NTFS permissions for debugging..."
    $acl = Get-Acl $sharePath
    # Remove existing Everyone permissions
    $acl.Access | Where-Object {$_.IdentityReference -eq "Everyone"} | ForEach-Object { $acl.RemoveAccessRule($_) }
    # Add new permissions
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone","FullControl","ContainerInherit,ObjectInherit","None","Allow")
    $acl.SetAccessRule($rule)
    Set-Acl $sharePath $acl

    # 6. Configure SMB Security Settings (PERMISSIVE for debugging)
    Write-Log "Configuring SMB security settings for debugging..."
    Set-SmbServerConfiguration -RequireSecuritySignature $false -Force
    Set-SmbServerConfiguration -EnableGuestAccess $true -Force  # Enable guest access for debugging
    Set-SmbServerConfiguration -RestrictNullSessAccess $false -Force
    Set-SmbServerConfiguration -RestrictNullSessPipes $false -Force
    Set-SmbServerConfiguration -RestrictNullSessShares $false -Force

    # 7. Configure registry settings for anonymous access (for debugging)
    Write-Log "Configuring registry settings for debugging..."
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "RestrictNullSessAccess" -Value 0 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "NullSessionShares" -Value "TestShare" -Type String -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "NullSessionPipes" -Value "spoolss" -Type String -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "AutoShareWks" -Value 1 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "AutoShareServer" -Value 1 -Type DWord -Force

    # 8. Configure Local Security Policy for anonymous access (for debugging)
    Write-Log "Configuring local security policy for debugging..."
    secedit /export /cfg C:\secpol_debug.cfg
    (Get-Content C:\secpol_debug.cfg) -replace 'RestrictAnonymousSAM = 1', 'RestrictAnonymousSAM = 0' | Set-Content C:\secpol_debug.cfg
    (Get-Content C:\secpol_debug.cfg) -replace 'RestrictAnonymous = 1', 'RestrictAnonymous = 0' | Set-Content C:\secpol_debug.cfg
    secedit /configure /db C:\Windows\Security\Local.sdb /cfg C:\secpol_debug.cfg /areas SECURITYPOLICY
    Remove-Item C:\secpol_debug.cfg -Force

    # 9. Enable Guest account for debugging
    Write-Log "Enabling Guest account for debugging..."
    Enable-LocalUser -Name "Guest" -ErrorAction SilentlyContinue
    Set-LocalUser -Name "Guest" -Password (ConvertTo-SecureString "Guest123!" -AsPlainText -Force) -ErrorAction SilentlyContinue

    # 10. Configure network access settings (for debugging)
    Write-Log "Configuring network access settings for debugging..."
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "EveryoneIncludesAnonymous" -Value 1 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "NoLMHash" -Value 0 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "LmCompatibilityLevel" -Value 1 -Type DWord -Force

    # 11. Create test file
    Write-Log "Creating test file..."
    "This is a test file for SMB connectivity - $(Get-Date)" | Out-File -FilePath "$sharePath\test.txt" -Encoding ASCII

    # 12. Restart SMB services to apply changes
    Write-Log "Restarting SMB services..."
    Restart-Service -Name "LanmanServer" -Force
    Restart-Service -Name "LanmanWorkstation" -Force
    Start-Sleep -Seconds 10

    # 13. Output Diagnostics
    Write-Log "=== SMB Debug Setup Complete ==="
    Write-Log "SMB Server Configuration:"
    Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol, EnableSMB3Protocol, RequireSecuritySignature, EnableGuestAccess, RestrictNullSessAccess | Format-Table
    Write-Log "SMB Shares:"
    Get-SmbShare | Format-Table
    Write-Log "SMB Share Permissions:"
    Get-SmbShareAccess -Name TestShare | Format-Table
    Write-Log "Test file contents:"
    Get-Content "$sharePath\test.txt"
    Write-Log "Registry settings:"
    Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" | Select-Object RestrictNullSessAccess, NullSessionShares, NullSessionPipes | Format-Table
    Write-Log "Debug setup completed successfully!"

} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    Write-Log "Stack trace: $($_.ScriptStackTrace)"
    throw
} 