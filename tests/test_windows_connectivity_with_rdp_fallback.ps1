param(
    [string]$TargetIP,
    [string]$Password
)

if (-not $TargetIP) {
    Write-Host "Usage: .\test_windows_connectivity_with_rdp_fallback.ps1 -TargetIP <ip> [-Password <password>]"
    exit 1
}

Write-Host "=== ENHANCED WINDOWS CONNECTIVITY TEST WITH RDP FALLBACK ==="
Write-Host "Target IP: $TargetIP"
Write-Host "Timestamp: $(Get-Date -Format o)"

# Function to test RDP connectivity
function Test-RDPConnectivity {
    Write-Host ""
    Write-Host "=== TESTING RDP CONNECTIVITY ==="
    Write-Host "Testing RDP port 3389 connectivity..."
    
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $iar = $tcp.BeginConnect($TargetIP, 3389, $null, $null)
        $success = $iar.AsyncWaitHandle.WaitOne(5000, $false)
        
        if ($success -and $tcp.Connected) {
            $tcp.EndConnect($iar)
            $tcp.Close()
            Write-Host "✅ RDP port 3389 is open and accessible"
            
            # Test RDP connection attempt (without actually connecting)
            Write-Host "Testing RDP connection attempt..."
            try {
                $rdpTest = New-Object System.Net.Sockets.TcpClient
                $rdpIar = $rdpTest.BeginConnect($TargetIP, 3389, $null, $null)
                $rdpSuccess = $rdpIar.AsyncWaitHandle.WaitOne(10000, $false)
                
                if ($rdpSuccess -and $rdpTest.Connected) {
                    $rdpTest.EndConnect($rdpIar)
                    $rdpTest.Close()
                    Write-Host "✅ RDP connection test successful"
                    Write-Host "RDP connectivity is working"
                    return $true
                } else {
                    $rdpTest.Close()
                    Write-Host "❌ RDP connection test failed"
                    return $false
                }
            } catch {
                Write-Host "❌ RDP connection test failed: $_"
                return $false
            }
        } else {
            $tcp.Close()
            Write-Host "❌ RDP port 3389 is not accessible"
            return $false
        }
    } catch {
        Write-Host "❌ RDP port 3389 is not accessible: $_"
        return $false
    }
}

# Function to test SMB connectivity
function Test-SMBConnectivity {
    Write-Host ""
    Write-Host "=== TESTING SMB CONNECTIVITY ==="
    
    # Retry loop for port 445
    $maxAttempts = 5
    $delaySeconds = 5
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
                Write-Host "✅ Port 445 is reachable"
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
        Write-Host "❌ Port 445 is not reachable after $maxAttempts attempts."
        return $false
    }

    Write-Host "Testing SMB connectivity..."

    # Try to access TestShare
    $testPath = "\\$TargetIP\TestShare"
    Write-Host "Attempting to access: $testPath"

    # Try anonymous access first
    Write-Host "Testing anonymous SMB access..."
    try {
        if (Test-Path $testPath -ErrorAction SilentlyContinue) {
            Write-Host "✅ Anonymous SMB access successful"
            Get-ChildItem $testPath -ErrorAction SilentlyContinue | Select-Object Name
            return $true
        }
    } catch {
        Write-Host "Anonymous SMB access failed: $_"
    }

    # Try with credentials if available
    if ($Password) {
        Write-Host "Testing authenticated SMB access..."
        try {
            $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
            $credential = New-Object System.Management.Automation.PSCredential("Administrator", $securePassword)
            
            if (Test-Path $testPath -Credential $credential -ErrorAction SilentlyContinue) {
                Write-Host "✅ Authenticated SMB access successful"
                Get-ChildItem $testPath -Credential $credential -ErrorAction SilentlyContinue | Select-Object Name
                return $true
            }
        } catch {
            Write-Host "Authenticated SMB access failed: $_"
        }
    }

    # Try to access C$ share as fallback
    Write-Host "Trying to access C$ share as fallback..."
    $cSharePath = "\\$TargetIP\C$"
    try {
        if (Test-Path $cSharePath -ErrorAction SilentlyContinue) {
            Write-Host "✅ C$ share is accessible"
            return $true
        }
    } catch {
        Write-Host "C$ access failed: $_"
    }

    Write-Host "❌ All SMB authentication methods failed"
    return $false
}

# Main test execution
Write-Host "Starting connectivity tests..."

# Test RDP first
if (Test-RDPConnectivity) {
    Write-Host ""
    Write-Host "=== FINAL RESULT ==="
    Write-Host "✅ RDP CONNECTIVITY SUCCESSFUL"
    Write-Host "Windows RDP connectivity is working properly"
    Write-Host "No need to test SMB - RDP is sufficient"
    exit 0
} else {
    Write-Host ""
    Write-Host "❌ RDP CONNECTIVITY FAILED"
    Write-Host "Falling back to SMB connectivity test..."
    
    # Test SMB as fallback
    if (Test-SMBConnectivity) {
        Write-Host ""
        Write-Host "=== FINAL RESULT ==="
        Write-Host "⚠️  RDP FAILED but SMB SUCCESSFUL"
        Write-Host "RDP connectivity failed, but SMB connectivity is working"
        Write-Host "Windows instance is reachable via SMB (port 445)"
        Write-Host ""
        Write-Host "SMB connection command (for manual testing):"
        Write-Host "smbclient //$TargetIP/TestShare -U Administrator"
        Write-Host ""
        Write-Host "Troubleshooting RDP issues:"
        Write-Host "- Check Windows Firewall rules for RDP (port 3389)"
        Write-Host "- Verify Remote Desktop service is running on Windows"
        Write-Host "- Ensure Remote Desktop is enabled in System Properties"
        Write-Host "- Check if RDP is allowed in Windows Firewall"
        Write-Host "- Verify the instance security group allows port 3389"
        exit 1  # Exit with error as requested
    } else {
        Write-Host ""
        Write-Host "=== FINAL RESULT ==="
        Write-Host "❌ BOTH RDP AND SMB CONNECTIVITY FAILED"
        Write-Host "Windows instance is not reachable via either protocol"
        Write-Host ""
        Write-Host "Debugging information:"
        Write-Host "- Target IP: $TargetIP"
        Write-Host "- RDP port 3389: Not accessible"
        Write-Host "- SMB port 445: Not accessible"
        Write-Host ""
        Write-Host "Possible issues:"
        Write-Host "- Windows instance may not be running"
        Write-Host "- Network connectivity issues"
        Write-Host "- Firewall blocking both ports"
        Write-Host "- Instance security groups not configured properly"
        Write-Host "- Windows services not started"
        exit 1
    }
} 