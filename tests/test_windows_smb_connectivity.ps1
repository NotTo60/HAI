param(
    [string]$TargetIP
)

if (-not $TargetIP) {
    Write-Host "Usage: .\test_windows_smb_connectivity.ps1 -TargetIP <ip>"
    exit 1
}

Write-Host "Testing SMB connectivity to $TargetIP..."

try {
    # Test 1: Check if port 445 is reachable
    Write-Host "Testing port 445 connectivity..."
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ConnectAsync($TargetIP, 445).Wait(5000) | Out-Null
    
    if ($tcpClient.Connected) {
        Write-Host "Port 445 is reachable"
        $tcpClient.Close()
    } else {
        Write-Host "Port 445 is not reachable"
        exit 1
    }
    
    # Test 2: Try to list SMB shares
    Write-Host "Testing SMB share enumeration..."
    $shares = Get-WmiObject -Class Win32_Share -ComputerName $TargetIP -ErrorAction Stop
    Write-Host "Successfully enumerated shares:"
    foreach ($share in $shares) {
        Write-Host "  - $($share.Name) ($($share.Path))"
    }
    
    # Test 3: Try to access the TestShare we created
    Write-Host "Testing access to TestShare..."
    $testPath = "\\$TargetIP\TestShare"
    if (Test-Path $testPath) {
        Write-Host "TestShare is accessible"
        $items = Get-ChildItem $testPath -ErrorAction Stop
        Write-Host "TestShare contents: $($items.Count) items"
    } else {
        Write-Host "TestShare is not accessible"
    }
    
    Write-Host "WINDOWS SMB CONNECTIVITY OK"
    
} catch {
    Write-Host "SMB connection failed: $_"
    Write-Host "Error details: $($_.Exception.Message)"
    exit 1
} 