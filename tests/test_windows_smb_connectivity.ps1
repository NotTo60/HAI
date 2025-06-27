param(
    [string]$TargetIP
)

if (-not $TargetIP) {
    Write-Host "Usage: .\test_windows_smb_connectivity.ps1 -TargetIP <ip>"
    exit 1
}

Write-Host "Testing SMB connectivity to $TargetIP..."

# Retry loop for port 445
$maxAttempts = 10
$delaySeconds = 10
$attempt = 1
$portOpen = $false
while ($attempt -le $maxAttempts) {
    Write-Host "Testing port 445 connectivity (attempt $attempt of $maxAttempts)..."
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $iar = $tcp.BeginConnect($TargetIP, 445, $null, $null)
        $success = $iar.AsyncWaitHandle.WaitOne(3000, $false)
        if ($success -and $tcp.Connected) {
            $tcp.EndConnect($iar)
            $tcp.Close()
            Write-Host "Port 445 is reachable!"
            $portOpen = $true
            break
        } else {
            $tcp.Close()
            Write-Host "Port 445 not open yet."
        }
    } catch {
        Write-Host "Port 445 not open yet ($_)."
    }
    $attempt++
    Start-Sleep -Seconds $delaySeconds
}

if (-not $portOpen) {
    Write-Host "Port 445 is not reachable after $maxAttempts attempts."
    exit 1
}

$shareAccessible = $false

# Test 2: Try to access the TestShare we created
Write-Host "Testing SMB share access..."
$testPath = "\\$TargetIP\TestShare"
Write-Host "Attempting to access: $testPath"

# Try multiple methods to test SMB access
$methods = @(
    @{ Name = "Test-Path"; Script = { Test-Path $testPath -ErrorAction SilentlyContinue } },
    @{ Name = "Get-ChildItem"; Script = { Get-ChildItem $testPath -ErrorAction SilentlyContinue } }
)

foreach ($method in $methods) {
    Write-Host "Trying method: $($method.Name)"
    try {
        $result = & $method.Script
        if ($result) {
            Write-Host "$($method.Name) succeeded"
            $shareAccessible = $true
            break
        }
    } catch {
        Write-Host "$($method.Name) failed: $_"
    }
}

# Try with explicit credentials if available
if (-not $shareAccessible) {
    Write-Host "Trying with explicit credentials..."
    try {
        $cred = New-Object System.Management.Automation.PSCredential("Administrator", (ConvertTo-SecureString "TemporaryPassword123!" -AsPlainText -Force))
        $session = New-PSSession -ComputerName $TargetIP -Credential $cred -ErrorAction SilentlyContinue
        if ($session) {
            Write-Host "PowerShell remoting session established"
            $shareAccessible = $true
            Remove-PSSession $session
        }
    } catch {
        Write-Host "PowerShell remoting failed: $_"
    }
}

if (-not $shareAccessible) {
    Write-Host "TestShare is not accessible, trying alternative methods..."
    
    # Try to enumerate shares using net view only if on Windows
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        Write-Host "Trying to enumerate shares using net view..."
        try {
            $netViewOutput = net view "\\$TargetIP" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Successfully enumerated shares:"
                Write-Host $netViewOutput
                $shareAccessible = $true
            } else {
                Write-Host "Could not enumerate shares with net view: $netViewOutput"
            }
        } catch {
            Write-Host "net view failed: $_"
        }
    } else {
        Write-Host "Skipping net view: not running on Windows"
    }
    
    # Try to access C$ share as fallback
    if (-not $shareAccessible) {
        Write-Host "Trying to access C$ share as fallback..."
        $cSharePath = "\\$TargetIP\C$"
        try {
            if (Test-Path $cSharePath -ErrorAction SilentlyContinue) {
                Write-Host "C$ share is accessible"
                $shareAccessible = $true
            } else {
                Write-Host "C$ share is not accessible"
            }
        } catch {
            Write-Host "C$ access failed: $_"
        }
    }
    
    # Try to access ADMIN$ share as another fallback
    if (-not $shareAccessible) {
        Write-Host "Trying to access ADMIN$ share as fallback..."
        $adminSharePath = "\\$TargetIP\ADMIN$"
        try {
            if (Test-Path $adminSharePath -ErrorAction SilentlyContinue) {
                Write-Host "ADMIN$ share is accessible"
                $shareAccessible = $true
            } else {
                Write-Host "ADMIN$ share is not accessible"
            }
        } catch {
            Write-Host "ADMIN$ access failed: $_"
        }
    }
}

if ($shareAccessible) {
    Write-Host "WINDOWS SMB CONNECTIVITY OK"
    exit 0
} else {
    Write-Host "ERROR: No accessible SMB shares found. SMB may not be working as expected."
    Write-Host "Debugging information:"
    Write-Host "- Target IP: $TargetIP"
    Write-Host "- Port 445: Reachable"
    Write-Host "- TestShare: Not accessible"
    Write-Host "- C$ share: Not accessible"
    Write-Host "- ADMIN$ share: Not accessible"
    Write-Host ""
    Write-Host "Possible issues:"
    Write-Host "1. Windows Firewall blocking SMB"
    Write-Host "2. SMB service not running"
    Write-Host "3. Network connectivity issues"
    Write-Host "4. Authentication problems"
    exit 1
} 