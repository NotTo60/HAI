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
    
    # Test 2: Try to access SMB shares using modern approach
    Write-Host "Testing SMB share access..."
    
    # Try to access the TestShare we created
    $testPath = "\\$TargetIP\TestShare"
    Write-Host "Attempting to access: $testPath"
    
    if (Test-Path $testPath -ErrorAction SilentlyContinue) {
        Write-Host "TestShare is accessible"
        try {
            $items = Get-ChildItem $testPath -ErrorAction Stop
            Write-Host "TestShare contents: $($items.Count) items"
        } catch {
            Write-Host "Could not list TestShare contents: $_"
        }
    } else {
        Write-Host "TestShare is not accessible, trying alternative methods..."
        
        # Try to enumerate shares using net view
        Write-Host "Trying to enumerate shares using net view..."
        $netViewOutput = net view "\\$TargetIP" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Successfully enumerated shares:"
            Write-Host $netViewOutput
        } else {
            Write-Host "Could not enumerate shares with net view"
        }
        
        # Try to access C$ share as fallback
        Write-Host "Trying to access C$ share as fallback..."
        $cSharePath = "\\$TargetIP\C$"
        if (Test-Path $cSharePath -ErrorAction SilentlyContinue) {
            Write-Host "C$ share is accessible"
        } else {
            Write-Host "C$ share is not accessible"
        }
    }
    
    Write-Host "WINDOWS SMB CONNECTIVITY OK"
    
} catch {
    Write-Host "SMB connection failed: $_"
    Write-Host "Error details: $($_.Exception.Message)"
    exit 1
} 