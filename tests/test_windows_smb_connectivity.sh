#!/bin/bash

# Test SMB connectivity to Windows instance
# Usage: ./test_windows_smb_connectivity.sh <target_ip> [password]

TARGET_IP="$1"
WINDOWS_PASSWORD="$2"

if [ -z "$TARGET_IP" ]; then
    echo "Usage: $0 <target_ip> [password]"
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
echo "[DEBUG] Attempting anonymous SMB enumeration..."
echo "[DEBUG] Full command: smbclient -L //$TARGET_IP -U "" -N"
smbclient -L "//$TARGET_IP" -U "" -N 2>&1 > /tmp/smb_anonymous.txt

if grep -q "TestShare\|C\$" /tmp/smb_anonymous.txt; then
    echo "✅ SMB connectivity successful - shares found"
    echo "WINDOWS SMB CONNECTIVITY OK"
    cat /tmp/smb_anonymous.txt
    rm -f /tmp/smb_anonymous.txt
    exit 0
else
    echo "❌ Anonymous SMB enumeration failed"
    echo "[DEBUG] Anonymous enumeration output:"
    cat /tmp/smb_anonymous.txt
    echo ""
    
    # Try with guest access
    echo "[DEBUG] Attempting guest SMB enumeration..."
    echo "[DEBUG] Full command: smbclient -L //$TARGET_IP -U guest -N"
    smbclient -L "//$TARGET_IP" -U "guest" -N 2>&1 > /tmp/smb_guest.txt
    
    if grep -q "TestShare\|C\$" /tmp/smb_guest.txt; then
        echo "✅ SMB connectivity successful with guest access - shares found"
        echo "WINDOWS SMB CONNECTIVITY OK"
        cat /tmp/smb_guest.txt
        rm -f /tmp/smb_anonymous.txt /tmp/smb_guest.txt
        exit 0
    else
        echo "❌ Guest SMB enumeration also failed"
        echo "[DEBUG] Guest enumeration output:"
        cat /tmp/smb_guest.txt
        echo ""
        
        # Try with Administrator credentials (if we have them)
        echo "[DEBUG] Attempting Administrator SMB enumeration..."
        echo "[DEBUG] Full command: smbclient -L //$TARGET_IP -U Administrator -W . -N"
        smbclient -L "//$TARGET_IP" -U "Administrator" -W . -N 2>&1 > /tmp/smb_admin.txt
        
        if grep -q "TestShare\|C\$" /tmp/smb_admin.txt; then
            echo "✅ SMB connectivity successful with Administrator access - shares found"
            echo "WINDOWS SMB CONNECTIVITY OK"
            cat /tmp/smb_admin.txt
            rm -f /tmp/smb_anonymous.txt /tmp/smb_guest.txt /tmp/smb_admin.txt
            exit 0
        else
            echo "❌ Anonymous Administrator enumeration failed"
            echo "[DEBUG] Administrator enumeration output:"
            cat /tmp/smb_admin.txt
            echo ""
            
            # Try with provided password if available
            if [ -n "$WINDOWS_PASSWORD" ] && [ "$WINDOWS_PASSWORD" != "DECRYPTION_FAILED" ] && [ "$WINDOWS_PASSWORD" != "NO_PASSWORD_AVAILABLE" ] && [ "$WINDOWS_PASSWORD" != "NO_INSTANCE_FOUND" ]; then
                echo "[DEBUG] Timestamp: $(date -Iseconds)"
                echo "Attempting SMB enumeration with provided Administrator password..."
                echo "[DEBUG] Using connection parameters:"
                echo "  Host: $TARGET_IP"
                echo "  User: Administrator"
                # Clean the password by removing null bytes and other non-printable characters
                CLEAN_PASSWORD=$(echo "$WINDOWS_PASSWORD" | tr -d '\0' | tr -cd '[:print:]')
                pwlen=${#CLEAN_PASSWORD}
                echo "  Password: $CLEAN_PASSWORD (from previous step 'DEBUG WINDOWS ADMINISTRATOR PASSWORD', length: $pwlen) [CI DEBUG: DO NOT USE IN PRODUCTION]"
                echo "  Domain: (default/empty)"
                echo "[DEBUG] Full command: echo \"$CLEAN_PASSWORD\" | smbclient -L //$TARGET_IP -U Administrator -W ."
                echo "$CLEAN_PASSWORD" | smbclient -L "//$TARGET_IP" -U "Administrator" -W . 2>&1 > /tmp/smb_admin_auth.txt
                rc=$?
                echo "[DEBUG] smbclient exit code: $rc"
                echo "[DEBUG] smbclient output:"
                cat /tmp/smb_admin_auth.txt
                
                if grep -q "TestShare\|C\$" /tmp/smb_admin_auth.txt; then
                    echo "✅ SMB connectivity successful with Administrator password - shares found"
                    echo "WINDOWS SMB CONNECTIVITY OK"
                    cat /tmp/smb_admin_auth.txt
                    rm -f /tmp/smb_anonymous.txt /tmp/smb_guest.txt /tmp/smb_admin.txt /tmp/smb_admin_auth.txt
                    exit 0
                else
                    echo "❌ Administrator password authentication failed"
                    echo ""
                    echo "Authenticated Administrator enumeration output:"
                    cat /tmp/smb_admin_auth.txt
                    echo ""
                    # Fail the test if password authentication fails
                    rm -f /tmp/smb_anonymous.txt /tmp/smb_guest.txt /tmp/smb_admin.txt /tmp/smb_admin_auth.txt
                    exit 1
                fi
            fi
            
            echo "❌ All SMB enumeration attempts failed"
            echo "Debugging information:"
            echo "- Target IP: $TARGET_IP"
            echo "- Port 445: Reachable"
            echo "- SMB enumeration: Failed for all authentication methods"
            rm -f /tmp/smb_anonymous.txt /tmp/smb_guest.txt /tmp/smb_admin.txt /tmp/smb_admin_auth.txt
            exit 1
        fi
    fi
fi 