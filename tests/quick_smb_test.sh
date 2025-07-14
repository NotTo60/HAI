#!/bin/bash

# Quick SMB Test Script
# Usage: ./quick_smb_test.sh <target_ip> [password]

TARGET_IP="$1"
PASSWORD="$2"

echo "=== Quick SMB Test for $TARGET_IP ==="

# Check if smbclient is available
if ! command -v smbclient >/dev/null 2>&1; then
    echo "❌ smbclient not found. Please install samba-client."
    exit 1
fi

# Test 1: Port connectivity
echo "1. Testing port 445 connectivity..."
if nc -z -w3 "$TARGET_IP" 445; then
    echo "   ✅ Port 445 is reachable"
else
    echo "   ❌ Port 445 is not reachable"
    exit 1
fi

# Test 2: Anonymous enumeration
echo "2. Testing anonymous SMB enumeration..."
if smbclient -L "//$TARGET_IP/" -U "" -N -d 0 2>/dev/null | grep -q "TestShare\|C\$"; then
    echo "   ✅ Anonymous access successful"
    smbclient -L "//$TARGET_IP/" -U "" -N -d 0 2>/dev/null | grep -E "Sharename|TestShare|C\$"
    exit 0
else
    echo "   ❌ Anonymous access failed"
fi

# Test 3: Authenticated access (if password provided)
if [ -n "$PASSWORD" ]; then
    echo "3. Testing authenticated access..."
    if smbclient -L "//$TARGET_IP/" -U "Administrator%$PASSWORD" -d 0 2>/dev/null | grep -q "TestShare\|C\$"; then
        echo "   ✅ Authenticated access successful"
        smbclient -L "//$TARGET_IP/" -U "Administrator%$PASSWORD" -d 0 2>/dev/null | grep -E "Sharename|TestShare|C\$"
        exit 0
    else
        echo "   ❌ Authenticated access failed"
    fi
fi

echo "❌ All SMB tests failed"
echo "Debugging suggestions:"
echo "- Check if Windows instance is running"
echo "- Verify SMB service is started on Windows"
echo "- Check Windows Firewall settings"
echo "- Ensure TestShare is created"
echo "- Verify Administrator password is correct"

exit 1 