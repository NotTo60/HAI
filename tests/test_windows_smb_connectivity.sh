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

# Install smbclient if not available
if ! command -v smbclient >/dev/null 2>&1; then
    echo "Installing smbclient..."
    if command -v apt-get >/dev/null 2>&1; then
        # Ubuntu/Debian
        sudo apt-get update -qq
        sudo apt-get install -y samba-client
    elif command -v yum >/dev/null 2>&1; then
        # CentOS/RHEL/Amazon Linux
        sudo yum install -y samba-client
    elif command -v dnf >/dev/null 2>&1; then
        # Fedora
        sudo dnf install -y samba-client
    elif command -v brew >/dev/null 2>&1; then
        # macOS
        brew install samba
    else
        echo "ERROR: Cannot install smbclient - no supported package manager found"
        exit 1
    fi
fi

# Test SMB connectivity using smbclient
echo "Testing SMB connectivity with smbclient..."

# Try to list shares anonymously
echo "Attempting anonymous SMB enumeration..."
smbclient -L "//$TARGET_IP" -U "" -N 2>&1 > /tmp/smb_anonymous.txt

if grep -q "TestShare\|C\$" /tmp/smb_anonymous.txt; then
    echo "✅ SMB connectivity successful - shares found"
    echo "WINDOWS SMB CONNECTIVITY OK"
    cat /tmp/smb_anonymous.txt
    rm -f /tmp/smb_anonymous.txt
    exit 0
else
    echo "❌ Anonymous SMB enumeration failed"
    echo ""
    echo "Anonymous enumeration output:"
    cat /tmp/smb_anonymous.txt
    echo ""
    
    # Try with guest access
    echo "Attempting guest SMB enumeration..."
    smbclient -L "//$TARGET_IP" -U "guest" -N 2>&1 > /tmp/smb_guest.txt
    
    if grep -q "TestShare\|C\$" /tmp/smb_guest.txt; then
        echo "✅ SMB connectivity successful with guest access - shares found"
        echo "WINDOWS SMB CONNECTIVITY OK"
        cat /tmp/smb_guest.txt
        rm -f /tmp/smb_anonymous.txt /tmp/smb_guest.txt
        exit 0
    else
        echo "❌ Guest SMB enumeration also failed"
        echo ""
        echo "Guest enumeration output:"
        cat /tmp/smb_guest.txt
        echo ""
        
        # Try with Administrator credentials (if we have them)
        echo "Attempting Administrator SMB enumeration..."
        smbclient -L "//$TARGET_IP" -U "Administrator" -N 2>&1 > /tmp/smb_admin.txt
        
        if grep -q "TestShare\|C\$" /tmp/smb_admin.txt; then
            echo "✅ SMB connectivity successful with Administrator access - shares found"
            echo "WINDOWS SMB CONNECTIVITY OK"
            cat /tmp/smb_admin.txt
            rm -f /tmp/smb_anonymous.txt /tmp/smb_guest.txt /tmp/smb_admin.txt
            exit 0
        else
            echo "❌ All SMB enumeration attempts failed"
            echo ""
            echo "Administrator enumeration output:"
            cat /tmp/smb_admin.txt
            echo ""
            
            echo "Debugging information:"
            echo "- Target IP: $TARGET_IP"
            echo "- Port 445: Reachable"
            echo "- SMB enumeration: Failed for all authentication methods"
            echo ""
            echo "Possible issues:"
            echo "1. Windows Firewall blocking SMB"
            echo "2. SMB service not running"
            echo "3. Authentication required (anonymous access disabled)"
            echo "4. SMB version compatibility issues"
            echo "5. Windows security policies blocking access"
            echo ""
            echo "Try connecting manually with:"
            echo "  smbclient -L //$TARGET_IP -U Administrator"
            echo "  smbclient -L //$TARGET_IP -U guest"
            echo "  smbclient -L //$TARGET_IP -U \"\""
            
            rm -f /tmp/smb_anonymous.txt /tmp/smb_guest.txt /tmp/smb_admin.txt
            exit 1
        fi
    fi
fi 