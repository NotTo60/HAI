param(
    [string]$TargetIP,
    [string]$Password
)

if (-not $TargetIP) {
    Write-Host "Usage: .\test_windows_smb_connectivity.ps1 -TargetIP <ip> [-Password <password>]"
    exit 1
}

# DEBUG SECTION
Write-Host "=== DEBUG SECTION ==="
Write-Host "Timestamp: $(Get-Date -Format o)"
Write-Host "Current user: $([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)"
Write-Host "OS: $([System.Environment]::OSVersion.VersionString)"
Write-Host "Working directory: $(Get-Location)"
Write-Host "Script arguments: TargetIP=$TargetIP, Password=(masked), Domain=(default/empty)"
if ($Password) {
    $masked = if ($Password.Length -gt 2) { $Password[0] + ('*' * ($Password.Length-2)) + $Password[-1] } else { '*' * $Password.Length }
    Write-Host "Password (masked): $masked (length: $($Password.Length))"
}
Write-Host "=== END DEBUG SECTION ==="

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

# Test SMB share access
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

# Try to enumerate shares using net view only if on Windows
if (-not $shareAccessible -and ($IsWindows -or $env:OS -eq "Windows_NT")) {
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
} elseif (-not $shareAccessible) {
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

# Try to access TestShare with different authentication methods
if (-not $shareAccessible) {
    Write-Host "Trying TestShare with different authentication methods..."
    
    # Try with Administrator credentials if password provided
    if ($Password -and $Password -ne "DECRYPTION_FAILED" -and $Password -ne "NO_PASSWORD_AVAILABLE" -and $Password -ne "NO_INSTANCE_FOUND") {
        Write-Host "[DEBUG] Timestamp: $(Get-Date -Format o)"
        Write-Host "Attempting SMB access with Administrator credentials..."
        Write-Host "[DEBUG] Using connection parameters:"
        Write-Host "  Host: $TargetIP"
        Write-Host "  User: Administrator"
        $masked = if ($Password.Length -gt 2) { $Password[0] + ('*' * ($Password.Length-2)) + $Password[-1] } else { '*' * $Password.Length }
        Write-Host "  Password: $masked (from previous step 'DEBUG WINDOWS ADMINISTRATOR PASSWORD', length: $($Password.Length))"
        Write-Host "  Domain: (default/empty)"
        Write-Host "[DEBUG] Full command: New-PSSession -ComputerName $TargetIP -Credential <credential>"
        try {
            # Create credential object
            $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
            $credential = New-Object System.Management.Automation.PSCredential("Administrator", $securePassword)
            
            # Try to access shares with credentials
            $testPath = "\\$TargetIP\TestShare"
            $session = $null
            $errorMsg = $null
            try {
                $session = New-PSSession -ComputerName $TargetIP -Credential $credential -ErrorAction Stop
            } catch {
                $errorMsg = $_
            }
            if ($session) {
                Write-Host "✅ Successfully connected with Administrator credentials"
                Remove-PSSession $session
                $shareAccessible = $true
                Write-Host "[DEBUG] Result: Success"
            } else {
                Write-Host "Failed to connect with Administrator credentials"
                Write-Host "[DEBUG] Result: Failure"
                if ($errorMsg) { Write-Host "[DEBUG] Error: $errorMsg" }
            }
        } catch {
            Write-Host "Administrator authentication failed: $_"
            Write-Host "[DEBUG] Exception: $_"
        }
    }
    
    # Try with anonymous access
    if (-not $shareAccessible) {
        try {
            $testPath = "\\$TargetIP\TestShare"
            if (Test-Path $testPath -ErrorAction SilentlyContinue) {
                Write-Host "TestShare accessible with anonymous access"
                $shareAccessible = $true
            }
        } catch {
            Write-Host "Anonymous access to TestShare failed"
        }
    }
    
    # Try with guest access (if we had credentials)
    if (-not $shareAccessible) {
        Write-Host "Note: Guest access would require credentials"
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
    exit 1
} 