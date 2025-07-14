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

# Create IAM role for Windows SSM
# resource "aws_iam_role" "windows_ssm" {
#   name = "windows-ssm-role"
#
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "ec2.amazonaws.com"
#         }
#       }
#     ]
#   })
# }

# Attach SSM managed policy to the role
# resource "aws_iam_role_policy_attachment" "windows_ssm_policy" {
#   role       = aws_iam_role.windows_ssm.name
#   policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
# }

# Create IAM instance profile
# resource "aws_iam_instance_profile" "windows_ssm" {
#   name = "windows-ssm-profile"
#   role = aws_iam_role.windows_ssm.name
# }

resource "aws_instance" "windows" {
  ami           = data.aws_ami.windows.id
  instance_type = var.instance_type_windows
  subnet_id     = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.main.id]
  key_name      = aws_key_pair.windows.key_name
  associate_public_ip_address = true
  user_data_base64 = base64encode(<<-EOF
    <powershell>
    # Set Administrator password
    $password = ConvertTo-SecureString "${var.windows_password}" -AsPlainText -Force
    Set-LocalUser -Name "Administrator" -Password $password
    
    # Enable RDP (Remote Desktop)
    Write-Host "Enabling Remote Desktop..."
    Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -value 0
    Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
    
    # Enable WinRM for remote management
    Enable-PSRemoting -Force
    Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
    
    # SMB Configuration with Better Security
    Write-Host "Configuring SMB with enhanced security..."
    
    # 1. Enable specific SMB firewall rules
    Write-Host "Enabling specific SMB firewall rules..."
    Enable-NetFirewallRule -DisplayName "File and Printer Sharing (SMB-In)" -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "Allow SMB Inbound" -Direction Inbound -LocalPort 445 -Protocol TCP -Action Allow -Profile Any -ErrorAction SilentlyContinue
    
    # 2. Ensure SMB Server Service is Running
    Write-Host "Ensuring 'Server' service is running..."
    Set-Service -Name 'LanmanServer' -StartupType Automatic
    Start-Service -Name 'LanmanServer'
    if ((Get-Service -Name 'LanmanServer').Status -ne 'Running') {
        throw "Failed to start LanmanServer service"
    }
    
    # 3. Configure SMB protocols (enable SMB1 for compatibility)
    Write-Host "Configuring SMB protocols..."
    Set-SmbServerConfiguration -EnableSMB2Protocol $true -Force
    Set-SmbServerConfiguration -EnableSMB3Protocol $true -Force
    Set-SmbServerConfiguration -EnableSMB1Protocol $true -Force  # Enable SMB1 for compatibility
    
    # 4. Create TestShare with better security
    $sharePath = "C:\TestShare"
    if (-Not (Test-Path $sharePath)) {
        Write-Host "Creating folder $sharePath..."
        New-Item -Path $sharePath -ItemType Directory | Out-Null
    }
    
    # Remove existing share if it exists
    $existingShare = Get-SmbShare -Name "TestShare" -ErrorAction SilentlyContinue
    if ($existingShare) {
        Write-Host "Removing existing TestShare..."
        Remove-SmbShare -Name "TestShare" -Force
    }
    
    Write-Host "Creating SMB share 'TestShare' with compatible permissions..."
    New-SmbShare -Name "TestShare" -Path $sharePath -FullAccess "Administrators" -ChangeAccess "Everyone" -CachingMode None
    
    # 5. Set NTFS permissions (compatible)
    Write-Host "Setting NTFS permissions..."
    $acl = Get-Acl $sharePath
    # Remove existing Everyone permissions
    $acl.Access | Where-Object {$_.IdentityReference -eq "Everyone"} | ForEach-Object { $acl.RemoveAccessRule($_) }
    # Add new permissions
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone","Modify","ContainerInherit,ObjectInherit","None","Allow")
    $acl.SetAccessRule($rule)
    Set-Acl $sharePath $acl
    
    # 6. Configure SMB Security Settings (compatible)
    Write-Host "Configuring SMB security settings..."
    Set-SmbServerConfiguration -RequireSecuritySignature $false -Force  # Disable for compatibility
    Set-SmbServerConfiguration -EnableGuestAccess $false -Force  # Keep guest access disabled
    Set-SmbServerConfiguration -RestrictNullSessAccess $false -Force  # Allow null sessions for testing
    Set-SmbServerConfiguration -RestrictNullSessPipes $false -Force
    Set-SmbServerConfiguration -RestrictNullSessShares $false -Force
    
    # 7. Configure registry settings for compatibility
    Write-Host "Configuring registry settings for compatibility..."
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "RestrictNullSessAccess" -Value 0 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "NullSessionShares" -Value "TestShare" -Type String -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "NullSessionPipes" -Value "spoolss" -Type String -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "AutoShareWks" -Value 1 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" -Name "AutoShareServer" -Value 1 -Type DWord -Force
    
    # 8. Configure local security policy for compatibility
    Write-Host "Configuring local security policy for compatibility..."
    secedit /export /cfg C:\secpol.cfg
    (Get-Content C:\secpol.cfg) -replace 'RestrictAnonymousSAM = 1', 'RestrictAnonymousSAM = 0' | Set-Content C:\secpol.cfg
    (Get-Content C:\secpol.cfg) -replace 'RestrictAnonymous = 1', 'RestrictAnonymous = 0' | Set-Content C:\secpol.cfg
    secedit /configure /db C:\Windows\Security\Local.sdb /cfg C:\secpol.cfg /areas SECURITYPOLICY
    Remove-Item C:\secpol.cfg -Force
    
    # 9. Configure network access settings for compatibility
    Write-Host "Configuring network access settings..."
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "EveryoneIncludesAnonymous" -Value 1 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "NoLMHash" -Value 0 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "LmCompatibilityLevel" -Value 1 -Type DWord -Force
    
    # 10. Create test file
    Write-Host "Creating test file..."
    "This is a test file for SMB connectivity - $(Get-Date)" | Out-File -FilePath "$sharePath\test.txt" -Encoding ASCII
    
    # 11. Restart SMB services to apply changes
    Write-Host "Restarting SMB services..."
    Restart-Service -Name "LanmanServer" -Force
    Restart-Service -Name "LanmanWorkstation" -Force
    Start-Sleep -Seconds 10
    
    # 12. Output Diagnostics
    Write-Host "=== SMB Setup Complete ==="
    Write-Host "SMB Server Configuration:"
    Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol, EnableSMB3Protocol, RequireSecuritySignature, EnableGuestAccess, RestrictNullSessAccess | Format-Table
    Write-Host "SMB Shares:"
    Get-SmbShare | Format-Table
    Write-Host "SMB Share Permissions:"
    Get-SmbShareAccess -Name "TestShare" | Format-Table
    Write-Host "Test file contents:"
    Get-Content "$sharePath\test.txt"
    Write-Host "Windows instance configured successfully for SMB testing"
    
    # RDP and Authentication Debug Information
    Write-Host "=== RDP AND AUTHENTICATION DEBUG ==="
    Write-Host "Administrator account status:"
    Get-LocalUser -Name "Administrator" | Select-Object Name, Enabled, PasswordLastSet
    Write-Host "RDP status:"
    Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections"
    Write-Host "RDP firewall rules:"
    Get-NetFirewallRule -DisplayGroup "Remote Desktop" | Select-Object DisplayName, Enabled
    Write-Host "=== END DEBUG ==="
    </powershell>
    EOF
  )
  # iam_instance_profile = aws_iam_instance_profile.windows_ssm.name  # Commented out due to IAM permissions
  tags = {
    Name = "hai-windows-ci"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    OS = "Windows"
    OSVersion = "Server2022"
    WorkflowRunID = var.workflow_run_id
  }
} 