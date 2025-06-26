param(
    [string]$TargetIP
)

if (-not $TargetIP) {
    Write-Host "Usage: .\test_smb.ps1 -TargetIP <ip>"
    exit 1
}

try {
    $smb = New-Object -ComObject WScript.Network
    $smb.MapNetworkDrive('Z:', "\\$TargetIP\C$", $false)
    Write-Host "SMB OK"
    $smb.RemoveNetworkDrive('Z:', $true, $false)
} catch {
    Write-Host "SMB connection failed: $_"
    exit 1
} 