# Locals for Linux username
locals {
  linux_ami_name = data.aws_ami.linux.name
  linux_user_map = {
    "al2023"  = "ec2-user"
    "amzn"    = "ec2-user"
    "ubuntu"  = "ubuntu"
    "centos"  = "centos"
    "debian"  = "admin"
    "rhel"    = "ec2-user"
    "fedora"  = "fedora"
  }
  linux_ssh_user = lookup(local.linux_user_map, regex("^([a-z0-9]+)", local.linux_ami_name)[0], "ec2-user")
}

resource "aws_instance" "linux" {
  depends_on = [aws_key_pair.ec2_user]
  ami           = data.aws_ami.linux.id
  instance_type = var.instance_type_linux
  subnet_id     = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.main.id]
  key_name      = aws_key_pair.ec2_user.key_name
  associate_public_ip_address = true
  user_data = <<-EOF
              #!/bin/bash
              # Ensure the instance is properly configured
              echo "Linux instance user data executed"
              # Update system packages
              yum update -y
              # Install basic utilities
              yum install -y curl wget git
              echo "Linux instance configured successfully"
              EOF
  tags = {
    Name = "hai-linux-ci"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    WorkflowRunID = var.workflow_run_id
  }
}

resource "aws_instance" "windows" {
  ami           = data.aws_ami.windows.id
  instance_type = var.instance_type_windows
  subnet_id     = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.main.id]
  associate_public_ip_address = true
  user_data_base64 = base64encode(<<-EOF
    <powershell>
    # Set Administrator password
    $password = ConvertTo-SecureString "${var.windows_password}" -AsPlainText -Force
    Set-LocalUser -Name "Administrator" -Password $password
    # Enable WinRM for remote management
    Enable-PSRemoting -Force
    Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
    # 1. Enable SMB Firewall Rules
    Write-Host "Enabling File and Printer Sharing (SMB-In) firewall rules..."
    Enable-NetFirewallRule -DisplayGroup "File and Printer Sharing"
    New-NetFirewallRule -DisplayName "Allow SMB Inbound" -Direction Inbound -LocalPort 445 -Protocol TCP -Action Allow -Profile Any
    # 2. Ensure SMB Server Service is Running
    Write-Host "Ensuring 'Server' service is running..."
    Set-Service -Name 'LanmanServer' -StartupType Automatic
    Start-Service -Name 'LanmanServer'
    # 3. Enable SMB2 and SMB3 (SMB1 for legacy compatibility)
    Write-Host "Configuring SMB protocols..."
    Set-SmbServerConfiguration -EnableSMB2Protocol $true -Force
    Set-SmbServerConfiguration -EnableSMB3Protocol $true -Force
    Set-SmbServerConfiguration -EnableSMB1Protocol $true -Force  # For legacy compatibility
    # 4. Create TestShare with Open Permissions
    $sharePath = "C:\TestShare"
    if (-Not (Test-Path $sharePath)) {
        Write-Host "Creating folder $sharePath..."
        New-Item -Path $sharePath -ItemType Directory | Out-Null
    }
    # Create a test file in the share
    "This is a test file for SMB connectivity" | Out-File -FilePath "$sharePath\test.txt" -Encoding ASCII
    if (-Not (Get-SmbShare | Where-Object { $_.Name -eq "TestShare" })) {
        Write-Host "Creating SMB share 'TestShare' with Everyone:FullControl..."
        New-SmbShare -Name "TestShare" -Path $sharePath -FullAccess Everyone -CachingMode None
    }
    # 5. Set Share and NTFS Permissions
    Write-Host "Setting NTFS permissions for Everyone:FullControl on $sharePath..."
    $acl = Get-Acl $sharePath
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone","FullControl","ContainerInherit,ObjectInherit","None","Allow")
    $acl.SetAccessRule($rule)
    Set-Acl $sharePath $acl
    # 6. Enable Guest Access (for debugging/testing)
    Write-Host "Enabling SMB guest access for testing..."
    Set-SmbServerConfiguration -EnableGuestAccess $true -Force
    # 7. Configure SMB for easier access (disable security features that might block access)
    Write-Host "Configuring SMB security settings for testing..."
    Set-SmbServerConfiguration -RequireSecuritySignature $false -Force
    Set-SmbServerConfiguration -RestrictNullSessAccess $false -Force
    Set-SmbServerConfiguration -RestrictNullSessPipes $false -Force
    Set-SmbServerConfiguration -RestrictNullSessShares $false -Force
    # 8. Configure registry settings for anonymous access
    Write-Host "Configuring registry settings..."
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "RestrictNullSessAccess" -Value 0 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "NullSessionShares" -Value "TestShare" -Type String -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "NullSessionPipes" -Value "spoolss" -Type String -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "AutoShareWks" -Value 1 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "AutoShareServer" -Value 1 -Type DWord -Force
    # 9. Configure Local Security Policy for anonymous access
    Write-Host "Configuring local security policy..."
    secedit /export /cfg C:\secpol.cfg
    (Get-Content C:\secpol.cfg) -replace 'RestrictAnonymousSAM = 1', 'RestrictAnonymousSAM = 0' | Set-Content C:\secpol.cfg
    (Get-Content C:\secpol.cfg) -replace 'RestrictAnonymous = 1', 'RestrictAnonymous = 0' | Set-Content C:\secpol.cfg
    secedit /configure /db C:\Windows\Security\Local.sdb /cfg C:\secpol.cfg /areas SECURITYPOLICY
    Remove-Item C:\secpol.cfg -Force
    # 10. Enable Guest account for testing
    Write-Host "Enabling Guest account for testing..."
    Enable-LocalUser -Name "Guest" -ErrorAction SilentlyContinue
    Set-LocalUser -Name "Guest" -Password (ConvertTo-SecureString "Guest123!" -AsPlainText -Force) -ErrorAction SilentlyContinue
    # 11. Configure network access settings
    Write-Host "Configuring network access settings..."
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "EveryoneIncludesAnonymous" -Value 1 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "NoLMHash" -Value 0 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "LmCompatibilityLevel" -Value 1 -Type DWord -Force
    # 12. Restart SMB services to apply changes
    Write-Host "Restarting SMB services..."
    Restart-Service -Name "LanmanServer" -Force
    Restart-Service -Name "LanmanWorkstation" -Force
    # Wait for services to restart
    Start-Sleep -Seconds 10
    # 13. Output Diagnostics
    Write-Host "=== SMB Setup Complete ==="
    Write-Host "SMB Server Configuration:"
    Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol, EnableSMB3Protocol, RequireSecuritySignature, EnableGuestAccess, RestrictNullSessAccess
    Write-Host "SMB Shares:"
    Get-SmbShare
    Write-Host "SMB Share Permissions:"
    Get-SmbShareAccess -Name "TestShare"
    Write-Host "Windows instance configured successfully for SMB testing"
    </powershell>
    EOF
  )
  tags = {
    Name = "hai-windows-ci"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    OS = "Windows"
    OSVersion = "Server2022"
    WorkflowRunID = var.workflow_run_id
  }
} 