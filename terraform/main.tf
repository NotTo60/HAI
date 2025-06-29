provider "aws" {
  region = var.aws_region
}

# Infrastructure constants
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "availability_zone" {
  description = "Availability zone for resources"
  type        = string
  default     = "us-east-1a"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type_linux" {
  description = "EC2 instance type for Linux"
  type        = string
  default     = "t3.micro"
}

variable "instance_type_windows" {
  description = "EC2 instance type for Windows"
  type        = string
  default     = "t3.small"
}

# Variable for Windows password
variable "windows_password" {
  description = "Password for Windows Administrator user"
  type        = string
  sensitive   = true
  default     = "TemporaryPassword123!"  # Default password if not provided
}

# Variable for workflow run ID
variable "workflow_run_id" {
  description = "Unique ID for the current workflow run"
  type        = string
  default     = "manual-run"  # Default for manual runs
}

# Get all VPCs to find an existing one
data "aws_vpcs" "all" {}

# Use existing VPC if available, otherwise create a new one
locals {
  existing_vpc_id = length(data.aws_vpcs.all.ids) > 0 ? data.aws_vpcs.all.ids[0] : null
}

# Create VPC only if no existing VPC is found
resource "aws_vpc" "main" {
  count = local.existing_vpc_id == null ? 1 : 0
  
  cidr_block = var.vpc_cidr
  
  tags = {
    Name = "hai-ci-vpc"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    WorkflowRunID = var.workflow_run_id
  }
}

# Use existing VPC or the newly created one
locals {
  vpc_id = local.existing_vpc_id != null ? local.existing_vpc_id : aws_vpc.main[0].id
}

# Get existing subnets in the VPC
data "aws_subnets" "existing" {
  filter {
    name   = "vpc-id"
    values = [local.vpc_id]
  }
}

# Get details of existing subnets to check for CIDR conflicts
data "aws_subnet" "existing" {
  for_each = toset(data.aws_subnets.existing.ids)
  id       = each.value
}

# Get VPC CIDR for dynamic subnet generation
data "aws_vpc" "selected" {
  id = local.vpc_id
}

# Choose an available CIDR block dynamically
locals {
  # Get existing CIDR blocks
  existing_cidrs = [for subnet in data.aws_subnet.existing : subnet.cidr_block]
  
  # Generate potential CIDR blocks from VPC range (10.0.0.0/16)
  # This creates subnets like 10.0.1.0/24, 10.0.2.0/24, etc.
  potential_cidrs = [
    for i in range(1, 255) : "10.0.${i}.0/24"
  ]
  
  # Find first available CIDR block
  available_cidr = [
    for cidr in local.potential_cidrs : cidr
    if !contains(local.existing_cidrs, cidr)
  ][0]
}

# Create subnet in the VPC
resource "aws_subnet" "main" {
  vpc_id     = local.vpc_id
  cidr_block = local.available_cidr
  availability_zone = var.availability_zone
  map_public_ip_on_launch = true
  
  tags = {
    Name = "hai-ci-subnet"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    WorkflowRunID = var.workflow_run_id
  }
}

# Check for existing internet gateways in the VPC
data "aws_internet_gateway" "existing" {
  filter {
    name   = "attachment.vpc-id"
    values = [local.vpc_id]
  }
}

# Create Internet Gateway only if none exists
resource "aws_internet_gateway" "main" {
  count = length(data.aws_internet_gateway.existing) == 0 ? 1 : 0
  
  vpc_id = local.vpc_id

  tags = {
    Name = "hai-ci-igw"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    WorkflowRunID = var.workflow_run_id
  }
}

# Use existing internet gateway or the newly created one
locals {
  igw_id = length(data.aws_internet_gateway.existing) > 0 ? data.aws_internet_gateway.existing.id : aws_internet_gateway.main[0].id
}

# Create Route Table
resource "aws_route_table" "main" {
  vpc_id = local.vpc_id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = local.igw_id
  }

  tags = {
    Name = "hai-ci-rt"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    WorkflowRunID = var.workflow_run_id
  }
}

# Associate Route Table with Subnet
resource "aws_route_table_association" "main" {
  subnet_id      = aws_subnet.main.id
  route_table_id = aws_route_table.main.id
}

resource "aws_security_group" "main" {
  vpc_id = local.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # SSH
  }
  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # RDP
  }
  ingress {
    from_port   = 445
    to_port     = 445
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # SMB
  }
  ingress {
    from_port   = 5985
    to_port     = 5986
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WinRM
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "hai-ci-sg"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    WorkflowRunID = var.workflow_run_id
  }
}

resource "aws_key_pair" "ec2_user" {
  key_name   = "hai-ci-ec2-user-key"
  public_key = file("${path.module}/ec2_user_rsa.pub")
  
  tags = {
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    WorkflowRunID = var.workflow_run_id
  }
}

# Get latest Amazon Linux 2023 AMI

data "aws_ami" "linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Get latest Windows Server 2022 AMI

data "aws_ami" "windows" {
  most_recent = true
  owners      = ["801119661308"] # Amazon's official Windows AMIs
  filter {
    name   = "name"
    values = ["Windows_Server-2022-English-Full-Base-*"]
  }
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Infer Linux username from AMI name
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
  
  # Add user data to ensure the instance is properly configured
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
  
  # User data to set Administrator password and configure SMB (improved for accessibility)
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

resource "null_resource" "check_linux_instance" {
  depends_on = [aws_instance.linux]

  provisioner "local-exec" {
    command = "echo Linux instance created with IP: ${aws_instance.linux.public_ip}"
  }
}

resource "null_resource" "check_windows_instance" {
  depends_on = [aws_instance.windows]

  provisioner "local-exec" {
    command = "echo Windows instance created with IP: ${aws_instance.windows.public_ip}"
  }
}

output "linux_ssh_user" {
  value = local.linux_ssh_user
} 