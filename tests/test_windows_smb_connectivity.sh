#!/bin/bash

# Test SMB connectivity to Windows instance
# Usage: ./test_windows_smb_connectivity.sh <target_ip>

TARGET_IP="$1"

if [ -z "$TARGET_IP" ]; then
    echo "Usage: $0 <target_ip>"
    exit 1
fi

echo "Testing SMB connectivity to $TARGET_IP..."

# Retry loop for port 445
max_attempts=10
delay_seconds=10
attempt=1
port_open=0
while [ $attempt -le $max_attempts ]; do
    echo "Testing port 445 connectivity (attempt $attempt of $max_attempts)..."
    nc -z -w3 "$TARGET_IP" 445 && port_open=1 && break
    echo "Port 445 not open yet."
    attempt=$((attempt+1))
    sleep $delay_seconds
done

if [ $port_open -ne 1 ]; then
    echo "Port 445 is not reachable after $max_attempts attempts."
    exit 1
fi

# Test 2: Try to enumerate shares using smbclient if available
echo "Testing SMB share enumeration..."
SHARE_ACCESSIBLE=false

# Check if smbclient is available
if command -v smbclient >/dev/null 2>&1; then
    echo "Using smbclient to test SMB connectivity..."
    
    # Try to list shares anonymously
    if smbclient -L "//$TARGET_IP" -U "" -N 2>/dev/null | grep -q "TestShare\|C\$"; then
        echo "Successfully enumerated shares with smbclient"
        SHARE_ACCESSIBLE=true
    else
        echo "smbclient enumeration failed, trying alternative methods..."
    fi
else
    echo "smbclient not available, trying alternative methods..."
fi

# Test 3: Try using nmap if available
if [ "$SHARE_ACCESSIBLE" = false ] && command -v nmap >/dev/null 2>&1; then
    echo "Using nmap to scan for SMB services..."
    if nmap -p 445 --script smb-enum-shares "$TARGET_IP" 2>/dev/null | grep -q "TestShare\|C\$"; then
        echo "nmap SMB scan successful"
        SHARE_ACCESSIBLE=true
    else
        echo "nmap SMB scan failed"
    fi
fi

# Test 4: Try using telnet to test SMB port
if [ "$SHARE_ACCESSIBLE" = false ]; then
    echo "Testing SMB port with telnet..."
    if timeout 5 bash -c "echo 'exit' | telnet $TARGET_IP 445" 2>/dev/null | grep -q "Connected"; then
        echo "SMB port is accessible via telnet"
        SHARE_ACCESSIBLE=true
    else
        echo "SMB port not accessible via telnet"
    fi
fi

# Test 5: Try using curl if available (for HTTP-like testing)
if [ "$SHARE_ACCESSIBLE" = false ] && command -v curl >/dev/null 2>&1; then
    echo "Testing with curl..."
    if curl --connect-timeout 5 "smb://$TARGET_IP" 2>/dev/null; then
        echo "curl SMB test successful"
        SHARE_ACCESSIBLE=true
    else
        echo "curl SMB test failed"
    fi
fi

# Final result
if [ "$SHARE_ACCESSIBLE" = true ]; then
    echo "WINDOWS SMB CONNECTIVITY OK"
    exit 0
else
    echo "ERROR: No accessible SMB shares found. SMB may not be working as expected."
    echo ""
    echo "Debugging information:"
    echo "- Target IP: $TARGET_IP"
    echo "- Port 445: Reachable"
    echo "- Share enumeration: Failed"
    echo ""
    echo "Possible issues:"
    echo "1. Windows Firewall blocking SMB"
    echo "2. SMB service not running"
    echo "3. Network connectivity issues"
    echo "4. Authentication problems"
    echo "5. SMB version compatibility issues"
    echo ""
    echo "Available tools:"
    echo "- smbclient: $(command -v smbclient >/dev/null 2>&1 && echo "Available" || echo "Not available")"
    echo "- nmap: $(command -v nmap >/dev/null 2>&1 && echo "Available" || echo "Not available")"
    echo "- telnet: $(command -v telnet >/dev/null 2>&1 && echo "Available" || echo "Not available")"
    echo "- curl: $(command -v curl >/dev/null 2>&1 && echo "Available" || echo "Not available")"
    exit 1
fi 