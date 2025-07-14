#!/bin/bash

# Enhanced Windows Connectivity Test with RDP Fallback
# Tests SMB connectivity first, then RDP if SMB fails
# Usage: ./test_windows_connectivity_with_rdp_fallback.sh <target_ip> [password]

TARGET_IP="$1"
WINDOWS_PASSWORD="$2"

echo "=== ENHANCED WINDOWS CONNECTIVITY TEST WITH RDP FALLBACK ==="
echo "Target IP: $TARGET_IP"
echo "Timestamp: $(date -Iseconds)"

if [ -z "$TARGET_IP" ] || [ "$TARGET_IP" = "--help" ] || [ "$TARGET_IP" = "-h" ]; then
    echo "Usage: $0 <target_ip> [password]"
    echo ""
    echo "Enhanced Windows Connectivity Test with RDP Fallback"
    echo "Tests SMB connectivity first, then falls back to RDP if SMB fails"
    echo "Exits with error if both protocols fail"
    echo ""
    echo "Arguments:"
    echo "  target_ip    Target Windows IP address"
    echo "  password     Windows Administrator password (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 192.168.1.100"
    echo "  $0 192.168.1.100 mypassword"
    exit 1
fi

# Helper for running commands with timeout and error handling
echo_and_run() {
    desc="$1"
    cmd="$2"
    echo "[DEBUG] $desc"
    echo "[DEBUG] Running: $cmd"
    eval "$cmd"
    rc=$?
    if [ $rc -eq 124 ]; then
        echo "❌ $desc: Command timed out after 20 seconds"
    fi
    return $rc
}

# Function to test RDP connectivity
test_rdp_connectivity() {
    echo ""
    echo "=== TESTING RDP CONNECTIVITY ==="
    echo "Testing RDP port 3389 connectivity..."
    
    # Test if RDP port is open
    if nc -z -w5 "$TARGET_IP" 3389; then
        echo "✅ RDP port 3389 is open and accessible"
        
        # Test RDP connection attempt (without actually connecting)
        echo "Testing RDP connection attempt..."
        
        # Try to establish a TCP connection to RDP port
        timeout 10s bash -c "echo 'RDP Test' | nc -w 5 $TARGET_IP 3389" >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "✅ RDP connection test successful"
            echo "RDP connectivity is working"
            return 0
        else
            echo "❌ RDP connection test failed"
            return 1
        fi
    else
        echo "❌ RDP port 3389 is not accessible"
        return 1
    fi
}

# Function to test SMB connectivity
test_smb_connectivity() {
    echo ""
    echo "=== TESTING SMB CONNECTIVITY ==="
    
    # Retry loop for port 445
    max_attempts=5
    delay_seconds=5
    attempt=1
    port_open=0
    
    while [ $attempt -le $max_attempts ]; do
        echo "Testing port 445 connectivity (attempt $attempt of $max_attempts)..."
        if nc -z -w3 "$TARGET_IP" 445; then
            port_open=1
            echo "✅ Port 445 is reachable"
            break
        else
            echo "Port 445 not open yet."
            attempt=$((attempt+1))
            sleep $delay_seconds
        fi
    done

    if [ $port_open -ne 1 ]; then
        echo "❌ Port 445 is not reachable after $max_attempts attempts."
        return 1
    fi

    # Install smbclient if not available
    if ! command -v smbclient >/dev/null 2>&1; then
        echo "Installing smbclient..."
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update -qq
            sudo apt-get install -y samba-client
        elif command -v yum >/dev/null 2>&1; then
            sudo yum install -y samba-client
        elif command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y samba-client
        elif command -v brew >/dev/null 2>&1; then
            brew install samba
        else
            echo "❌ Cannot install smbclient - no supported package manager found"
            return 1
        fi
    fi

    echo "Testing SMB connectivity with smbclient..."

    # Try anonymous access first
    echo "Testing anonymous SMB enumeration..."
    if smbclient -L "//$TARGET_IP/" -U "" -N -d 0 2>/dev/null | grep -q "TestShare\|C\$"; then
        echo "✅ Anonymous SMB access successful"
        smbclient -L "//$TARGET_IP/" -U "" -N -d 0 2>/dev/null | grep -E "Sharename|TestShare|C\$"
        return 0
    fi

    # Try with credentials if available
    if [ -n "$WINDOWS_PASSWORD" ] && [ "$WINDOWS_PASSWORD" != "DECRYPTION_FAILED" ] && [ "$WINDOWS_PASSWORD" != "NO_PASSWORD_AVAILABLE" ] && [ "$WINDOWS_PASSWORD" != "NO_INSTANCE_FOUND" ]; then
        echo "Testing authenticated SMB access..."
        CLEAN_PASSWORD=$(echo "$WINDOWS_PASSWORD" | tr -d '\0' | tr -cd '[:print:]')
        if smbclient -L "//$TARGET_IP/" -U "Administrator%$CLEAN_PASSWORD" -d 0 2>/dev/null | grep -q "TestShare\|C\$"; then
            echo "✅ Authenticated SMB access successful"
            smbclient -L "//$TARGET_IP/" -U "Administrator%$CLEAN_PASSWORD" -d 0 2>/dev/null | grep -E "Sharename|TestShare|C\$"
            return 0
        fi
    fi

    echo "❌ All SMB authentication methods failed"
    return 1
}

# Main test execution
echo "Starting connectivity tests..."

# Test SMB first
if test_smb_connectivity; then
    echo ""
    echo "=== FINAL RESULT ==="
    echo "✅ SMB CONNECTIVITY SUCCESSFUL"
    echo "Windows SMB connectivity is working properly"
    echo "No need to test RDP - SMB is sufficient"
    exit 0
else
    echo ""
    echo "❌ SMB CONNECTIVITY FAILED"
    echo "Falling back to RDP connectivity test..."
    
    # Test RDP as fallback
    if test_rdp_connectivity; then
        echo ""
        echo "=== FINAL RESULT ==="
        echo "⚠️  SMB FAILED but RDP SUCCESSFUL"
        echo "SMB connectivity failed, but RDP connectivity is working"
        echo "Windows instance is reachable via RDP (port 3389)"
        echo ""
        echo "RDP connection command (for manual testing):"
        echo "xfreerdp /v:$TARGET_IP /u:Administrator /p:\"<password>\" /cert:ignore"
        echo ""
        echo "Troubleshooting SMB issues:"
        echo "- Check Windows Firewall rules for SMB (port 445)"
        echo "- Verify SMB service is running on Windows"
        echo "- Ensure TestShare is created with proper permissions"
        echo "- Check Administrator password and account status"
        echo "- Verify SMB protocol versions are enabled"
        exit 1  # Exit with error as requested
    else
        echo ""
        echo "=== FINAL RESULT ==="
        echo "❌ BOTH SMB AND RDP CONNECTIVITY FAILED"
        echo "Windows instance is not reachable via either protocol"
        echo ""
        echo "Debugging information:"
        echo "- Target IP: $TARGET_IP"
        echo "- SMB port 445: Not accessible"
        echo "- RDP port 3389: Not accessible"
        echo ""
        echo "Possible issues:"
        echo "- Windows instance may not be running"
        echo "- Network connectivity issues"
        echo "- Firewall blocking both ports"
        echo "- Instance security groups not configured properly"
        echo "- Windows services not started"
        exit 1
    fi
fi 