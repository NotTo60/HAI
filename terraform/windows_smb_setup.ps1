# Windows SMB Setup & Diagnostics Script
# Run as Administrator

# 1. Enable SMB Firewall Rules
Write-Host "Enabling File and Printer Sharing (SMB-In) firewall rules..."
Enable-NetFirewallRule -DisplayGroup "File and Printer Sharing"

# 2. Ensure SMB Server Service is Running
Write-Host "Ensuring 'Server' service is running..."
Set-Service -Name 'LanmanServer' -StartupType Automatic
Start-Service -Name 'LanmanServer'

# 3. Enable SMB2 (and optionally SMB1 for legacy)
Write-Host "Ensuring SMB2 is enabled..."
Set-SmbServerConfiguration -EnableSMB2Protocol $true -Force
# Uncomment to enable SMB1 (not recommended)
# Set-SmbServerConfiguration -EnableSMB1Protocol $true -Force

# 4. Create TestShare with Open Permissions
$sharePath = "C:\\TestShare"
if (-Not (Test-Path $sharePath)) {
    Write-Host "Creating folder $sharePath..."
    New-Item -Path $sharePath -ItemType Directory | Out-Null
}

if (-Not (Get-SmbShare | Where-Object { $_.Name -eq "TestShare" })) {
    Write-Host "Creating SMB share 'TestShare' with Everyone:FullControl..."
    New-SmbShare -Name "TestShare" -Path $sharePath -FullAccess Everyone
}

# 5. Set Share and NTFS Permissions
Write-Host "Setting NTFS permissions for Everyone:FullControl on $sharePath..."
$acl = Get-Acl $sharePath
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone","FullControl","ContainerInherit,ObjectInherit","None","Allow")
$acl.SetAccessRule($rule)
Set-Acl $sharePath $acl

# 6. Enable Guest Access (for debugging only)
# WARNING: This is insecure! Only use for temporary testing.
$enableGuest = $true  # Set to $false to disable guest access
if ($enableGuest) {
    Write-Host "Enabling SMB guest access (for debugging)..."
    Set-SmbServerConfiguration -EnableGuestAccess $true -Force
}

# 7. Set Authentication Policy to Classic
Write-Host "Setting local security policy for classic authentication..."
secedit /export /cfg C:\\secpol.cfg
(gc C:\\secpol.cfg) -replace '^(\s*SeNetworkLogonRight\s*=).*', '$1 *S-1-5-32-544' | Set-Content C:\\secpol.cfg
secedit /configure /db C:\\Windows\\security\\local.sdb /cfg C:\\secpol.cfg /areas SECURITYPOLICY
Remove-Item C:\\secpol.cfg -Force

# 8. Output Diagnostics
Write-Host "\n=== SMB Diagnostics ==="
Get-SmbShare
Get-Service -Name *smb*
Get-SmbShareAccess -Name TestShare
Get-SmbServerConfiguration | Select EnableSMB1Protocol, EnableSMB2Protocol, EnableGuestAccess
Write-Host "\nUser accounts:"
net user
Write-Host "\nDone. SMB setup and diagnostics complete." 