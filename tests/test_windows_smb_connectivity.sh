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

# Print environment and system info
echo "[DEBUG] ENVIRONMENT VARIABLES:"
env | grep -E 'USER|DOMAIN|PWD|HOME'
echo "[DEBUG] Hostname: $(hostname)"
echo "[DEBUG] Current directory: $(pwd)"
echo "[DEBUG] Date: $(date -Iseconds)"
echo "[DEBUG] Resolved IP for $TARGET_IP: $(getent hosts $TARGET_IP 2>/dev/null | awk '{print $1}')"
echo "[DEBUG] smbclient version: $(smbclient -V 2>&1)"

# Try different SMB protocol versions
echo "[DEBUG] Testing SMB protocol versions..."
for proto in NT1 SMB2 SMB3; do
  echo "[DEBUG] Trying protocol: $proto"
  smbclient -L //$TARGET_IP/ -U "" -N --option="client min protocol=$proto" -d 3 2>&1 | tee /tmp/smb_proto_${proto}.txt
  if grep -q "Sharename" /tmp/smb_proto_${proto}.txt; then
    echo "[DEBUG] Protocol $proto supported."
  else
    echo "[DEBUG] Protocol $proto not supported or failed."
  fi
done

# Try to list shares anonymously
echo "[DEBUG] Attempting anonymous SMB enumeration..."
echo_and_run "Anonymous enumeration" "timeout 20s smbclient -L //${TARGET_IP}/ -U \"\" -N -d 3 2>&1 > /tmp/smb_anonymous.txt"
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
    echo_and_run "Guest enumeration" "timeout 20s smbclient -L //${TARGET_IP}/ -U \"guest\" -N -d 3 2>&1 > /tmp/smb_guest.txt"
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
        echo_and_run "Administrator enumeration (no password)" "timeout 20s smbclient -L //${TARGET_IP}/ -U \"Administrator\" -W . -N -d 3 2>&1 > /tmp/smb_admin.txt"
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
                echo_and_run "Administrator enumeration (with password)" "timeout 20s bash -c 'printf \"%s\" \"$0\" | smbclient -L //${TARGET_IP}/ -U \"Administrator\" -W . -d 3 2>&1' \"$CLEAN_PASSWORD\" > /tmp/smb_admin_auth.txt"
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

# Try with explicit domain/workgroup
for user in "Administrator" ".\\Administrator" "WORKGROUP\\Administrator"; do
  echo "[DEBUG] Attempting SMB enumeration as $user (no password)"
  echo_and_run "Enumeration as $user (no password)" "timeout 20s smbclient -L //${TARGET_IP}/ -U \"$user\" -N -d 3 2>&1 > /tmp/smb_${user//\\/_}.txt"
  cat /tmp/smb_${user//\\/_}.txt
  if grep -q "TestShare\|C\$" /tmp/smb_${user//\\/_}.txt; then
    echo "[DEBUG] $user (no password) succeeded."
  else
    echo "[DEBUG] $user (no password) failed."
  fi
done

# Try with password if available
if [ -n "$WINDOWS_PASSWORD" ] && [ "$WINDOWS_PASSWORD" != "DECRYPTION_FAILED" ] && [ "$WINDOWS_PASSWORD" != "NO_PASSWORD_AVAILABLE" ] && [ "$WINDOWS_PASSWORD" != "NO_INSTANCE_FOUND" ]; then
  for user in "Administrator" ".\\Administrator" "WORKGROUP\\Administrator"; do
    echo "[DEBUG] Attempting SMB enumeration as $user (with password)"
    echo_and_run "Enumeration as $user (with password)" "timeout 20s smbclient -L //${TARGET_IP}/ -U \"$user\"%\"$WINDOWS_PASSWORD\" -d 3 2>&1 > /tmp/smb_${user//\\/_}_pw.txt"
    cat /tmp/smb_${user//\\/_}_pw.txt
    if grep -q "TestShare\|C\$" /tmp/smb_${user//\\/_}_pw.txt; then
      echo "[DEBUG] $user (with password) succeeded."
    else
      echo "[DEBUG] $user (with password) failed."
    fi
  done

  # Try accessing specific shares
  for share in "C$" "ADMIN$" "TestShare" "IPC$"; do
    echo "[DEBUG] Attempting to list $share as Administrator"
    echo_and_run "List $share" "timeout 20s smbclient //${TARGET_IP}/$share -U \"Administrator%$WINDOWS_PASSWORD\" -c 'ls' -d 3 2>&1 > /tmp/smb_ls_${share}.txt"
    cat /tmp/smb_ls_${share}.txt
  done

  # Try file upload/download if C$ is accessible
  if grep -q "C$" /tmp/smb_Administrator_pw.txt; then
    echo "[DEBUG] Attempting file upload/download to C$..."
    echo "Test file from SMB test" > /tmp/smb_testfile.txt
    echo_and_run "Upload test file" "timeout 20s smbclient //${TARGET_IP}/C$ -U \"Administrator%$WINDOWS_PASSWORD\" -c 'put /tmp/smb_testfile.txt smb_testfile.txt' -d 3 2>&1 > /tmp/smb_upload.txt"
    echo_and_run "Download test file" "timeout 20s smbclient //${TARGET_IP}/C$ -U \"Administrator%$WINDOWS_PASSWORD\" -c 'get smb_testfile.txt /tmp/smb_testfile_downloaded.txt' -d 3 2>&1 > /tmp/smb_download.txt"
    if [ -f /tmp/smb_testfile_downloaded.txt ]; then
      echo "[DEBUG] File upload/download succeeded."
      diff /tmp/smb_testfile.txt /tmp/smb_testfile_downloaded.txt && echo "[DEBUG] File contents match."
    else
      echo "[DEBUG] File upload/download failed."
    fi
    rm -f /tmp/smb_testfile.txt /tmp/smb_testfile_downloaded.txt
  fi
fi

# Print summary table
printf '\n%-30s %-10s\n' "Test" "Result"
printf '%-30s %-10s\n' "------------------------------" "----------"
for f in /tmp/smb_*.txt; do
  if grep -q "Sharename" "$f" || grep -q "C$" "$f"; then
    printf '%-30s %-10s\n' "${f##*/}" "SUCCESS"
  else
    printf '%-30s %-10s\n' "${f##*/}" "FAIL"
  fi
done

# At the end, print a summary and suggestions if all fail
echo "[DEBUG] SMB diagnostics complete."
echo "[DEBUG] Suggestions:"
echo "- Check Windows Firewall rules for SMB (port 445)"
echo "- Ensure the Administrator account is enabled and password is correct"
echo "- Check Windows Event Viewer for failed logon attempts"
echo "- Try with a different password or user if possible"
echo "- Ensure SMBv1/v2/v3 is enabled on the server"
echo "- If using a domain, try DOMAIN\\Administrator as the user"
echo "- If password has special characters, ensure proper quoting/escaping" 