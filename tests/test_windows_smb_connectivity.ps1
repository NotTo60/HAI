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
if ($env:USERNAME) {
    Write-Host "Current user: $($env:USERNAME)"
} elseif ($env:USER) {
    Write-Host "Current user: $($env:USER)"
} else {
    Write-Host "Current user: (unknown)"
}
Write-Host "OS: $([System.Environment]::OSVersion.VersionString)"
Write-Host "Working directory: $(Get-Location)"
Write-Host "Script arguments: TargetIP=$TargetIP, Password=(masked), Domain=(default/empty)"
if ($Password) {
    # Clean the password by removing null bytes and other non-printable characters
    $cleanPassword = $Password -replace "`0", "" -replace "[^\x20-\x7E]", ""
    Write-Host "Password (clear): $cleanPassword (length: $($cleanPassword.Length)) [CI DEBUG: DO NOT USE IN PRODUCTION]"
    $Password = $cleanPassword
}
Write-Host "=== END DEBUG SECTION ==="

# Platform check: skip on non-Windows
if ($env:OS -ne "Windows_NT") {
    Write-Host "[INFO] Not running on Windows. Skipping PowerShell SMB test. Use Bash fallback for SMB testing."
    exit 0
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
        Write-Host "  Password: $Password  (from previous step 'DEBUG WINDOWS ADMINISTRATOR PASSWORD', length: $($Password.Length)) [CI DEBUG: DO NOT USE IN PRODUCTION]"
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

# Try with explicit domain/workgroup
$usersToTry = @('Administrator', '.\\Administrator', 'WORKGROUP\\Administrator')
$shareResults = @{}
foreach ($user in $usersToTry) {
    Write-Host "[DEBUG] Attempting SMB access as $user (no password)"
    try {
        $cred = New-Object System.Management.Automation.PSCredential($user, (ConvertTo-SecureString '' -AsPlainText -Force))
        $testPath = "\\$TargetIP\C$"
        $result = Test-Path $testPath -Credential $cred -ErrorAction SilentlyContinue
        $shareResults["$user (no password)"] = $result
        Write-Host "[DEBUG] $user (no password): $result"
    } catch {
        $shareResults["$user (no password)"] = $false
        Write-Host "[DEBUG] $user (no password) exception: $_"
    }
}

if ($Password) {
    foreach ($user in $usersToTry) {
        Write-Host "[DEBUG] Attempting SMB access as $user (with password)"
        try {
            $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
            $cred = New-Object System.Management.Automation.PSCredential($user, $securePassword)
            $testPath = "\\$TargetIP\C$"
            $result = Test-Path $testPath -Credential $cred -ErrorAction SilentlyContinue
            $shareResults["$user (with password)"] = $result
            Write-Host "[DEBUG] $user (with password): $result"
            # Try file upload/download if access works
            if ($result) {
                $localFile = "$env:TEMP\smb_testfile.txt"
                $remoteFile = "\\$TargetIP\C$\smb_testfile.txt"
                Set-Content -Path $localFile -Value "Test file from SMB test"
                try {
                    Copy-Item -Path $localFile -Destination $remoteFile -Credential $cred -ErrorAction Stop
                    Write-Host "[DEBUG] File upload succeeded."
                    $downloaded = "$env:TEMP\smb_testfile_downloaded.txt"
                    Copy-Item -Path $remoteFile -Destination $downloaded -Credential $cred -ErrorAction Stop
                    Write-Host "[DEBUG] File download succeeded."
                    if ((Get-Content $localFile) -eq (Get-Content $downloaded)) {
                        Write-Host "[DEBUG] File contents match."
                    } else {
                        Write-Host "[DEBUG] File contents do not match."
                    }
                    Remove-Item $localFile, $downloaded, $remoteFile -ErrorAction SilentlyContinue
                } catch {
                    Write-Host "[DEBUG] File upload/download failed: $_"
                }
            }
        } catch {
            $shareResults["$user (with password)"] = $false
            Write-Host "[DEBUG] $user (with password) exception: $_"
        }
    }
}

# Try specific shares
$sharesToTry = @('C$', 'ADMIN$', 'TestShare', 'IPC$')
foreach ($share in $sharesToTry) {
    $path = "\\$TargetIP\$share"
    try {
        $result = Test-Path $path -ErrorAction SilentlyContinue
        $shareResults["Anonymous $share"] = $result
        Write-Host "[DEBUG] Anonymous $share: $result"
    } catch {
        $shareResults["Anonymous $share"] = $false
        Write-Host "[DEBUG] Anonymous $share exception: $_"
    }
}

# Print summary table
Write-Host "\nTest Summary:"
Write-Host "------------------------------  ----------"
foreach ($key in $shareResults.Keys) {
    $status = if ($shareResults[$key]) { 'SUCCESS' } else { 'FAIL' }
    Write-Host ("{0,-30} {1,-10}" -f $key, $status)
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