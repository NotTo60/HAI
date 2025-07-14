#!/bin/bash

# Test SMB connectivity to Windows instance
# Usage: ./test_windows_smb_connectivity.sh <target_ip> [password]

TARGET_IP="$1"
WINDOWS_PASSWORD="$2"

echo "[DEBUG] Using TARGET_IP: $TARGET_IP"
if [ -z "$TARGET_IP" ]; then
    echo "ERROR: TARGET_IP is not set!"
    exit 1
fi

# Helper for running smbclient with timeout and error handling
echo_and_run() {
    # $1 = description, $2 = command
    desc="$1"
    cmd="$2"
    echo "[DEBUG] $desc"
    echo "[DEBUG] Running: $cmd"
    eval "$cmd"
    rc=$?
    if [ $rc -eq 124 ]; then
        echo "❌ $desc: smbclient timed out after 20 seconds"
    fi
    return $rc
}

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
    echo "=== FINAL RESULT ==="
    echo "❌ SMB CONNECTIVITY FAILED (port unreachable)"
    exit 1
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
        echo "ERROR: Cannot install smbclient - no supported package manager found"
        echo "=== FINAL RESULT ==="
        echo "❌ SMB CONNECTIVITY FAILED (no smbclient)"
        exit 1
    fi
fi

echo "Testing SMB connectivity with smbclient..."

# Try to list shares anonymously
echo "[DEBUG] Attempting anonymous SMB enumeration..."
echo_and_run "Anonymous enumeration" "timeout 20s smbclient -L \\"//$TARGET_IP\\" -U \"\" -N 2>&1 > /tmp/smb_anonymous.txt"
if grep -q "TestShare\|C\$" /tmp/smb_anonymous.txt; then
    echo ""
    echo "=== FINAL RESULT ==="
    echo "✅ SMB CONNECTIVITY SUCCESSFUL"
    echo "Anonymous access worked - shares found"
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
    echo_and_run "Guest enumeration" "timeout 20s smbclient -L \\"//$TARGET_IP\\" -U \"guest\" -N 2>&1 > /tmp/smb_guest.txt"
    if grep -q "TestShare\|C\$" /tmp/smb_guest.txt; then
        echo ""
        echo "=== FINAL RESULT ==="
        echo "✅ SMB CONNECTIVITY SUCCESSFUL"
        echo "Guest access worked - shares found"
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
        echo_and_run "Administrator enumeration (no password)" "timeout 20s smbclient -L \\"//$TARGET_IP\\" -U \"Administrator\" -W . -N 2>&1 > /tmp/smb_admin.txt"
        if grep -q "TestShare\|C\$" /tmp/smb_admin.txt; then
            echo ""
            echo "=== FINAL RESULT ==="
            echo "✅ SMB CONNECTIVITY SUCCESSFUL"
            echo "Administrator access (no password) worked - shares found"
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
                CLEAN_PASSWORD=$(echo "$WINDOWS_PASSWORD" | tr -d '\0' | tr -cd '[:print:]')
                pwlen=${#CLEAN_PASSWORD}
                echo "  Password: $CLEAN_PASSWORD (from previous step 'DEBUG WINDOWS ADMINISTRATOR PASSWORD', length: $pwlen) [CI DEBUG: DO NOT USE IN PRODUCTION]"
                echo "  Domain: (default/empty)"
                echo_and_run "Administrator enumeration (with password)" "timeout 20s bash -c 'printf \"%s\" \"\$0\" | smbclient -L \"//$TARGET_IP\" -U \"Administrator\" -W . 2>&1' \"$CLEAN_PASSWORD\" > /tmp/smb_admin_auth.txt"
                # Always print output, even if timeout or error
                echo "[DEBUG] smbclient output (admin with password):"
                cat /tmp/smb_admin_auth.txt
                if grep -q "TestShare\|C\$" /tmp/smb_admin_auth.txt; then
                    echo ""
                    echo "=== FINAL RESULT ==="
                    echo "✅ SMB CONNECTIVITY SUCCESSFUL"
                    echo "Administrator access with password worked - shares found"
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
                    rm -f /tmp/smb_anonymous.txt /tmp/smb_guest.txt /tmp/smb_admin.txt /tmp/smb_admin_auth.txt
                    echo ""
                    echo "=== FINAL RESULT ==="
                    echo "❌ SMB CONNECTIVITY FAILED (all methods, including password, failed)"
                    exit 1
                fi
            fi
            echo "❌ All SMB enumeration attempts failed"
            echo "Debugging information:"
            echo "- Target IP: $TARGET_IP"
            echo "- Port 445: Reachable"
            echo "- SMB enumeration: Failed for all authentication methods"
            rm -f /tmp/smb_anonymous.txt /tmp/smb_guest.txt /tmp/smb_admin.txt /tmp/smb_admin_auth.txt
            echo ""
            echo "=== FINAL RESULT ==="
            echo "❌ SMB CONNECTIVITY FAILED"
            echo "All authentication methods (anonymous, guest, Administrator) failed to enumerate shares."
            exit 1
        fi
    fi
fi 