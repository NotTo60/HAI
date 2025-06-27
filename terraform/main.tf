provider "aws" {
  region = "us-east-1"
}

# Variable for Windows password
variable "windows_password" {
  description = "Password for Windows Administrator user"
  type        = string
  sensitive   = true
  default     = "TemporaryPassword123!"  # Default password if not provided
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
  
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "hai-ci-vpc"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
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

# Get details of existing subnets to check CIDR blocks
data "aws_subnet" "existing" {
  for_each = toset(data.aws_subnets.existing.ids)
  id       = each.value
}

# Find an available CIDR block
locals {
  # Define possible CIDR blocks to try
  possible_cidrs = [
    "10.0.100.0/24",
    "10.0.101.0/24", 
    "10.0.102.0/24",
    "10.0.103.0/24",
    "10.0.104.0/24",
    "10.0.105.0/24",
    "10.0.106.0/24",
    "10.0.107.0/24",
    "10.0.108.0/24",
    "10.0.109.0/24",
    "10.0.110.0/24",
    "10.0.200.0/24",
    "10.0.201.0/24",
    "10.0.202.0/24",
    "10.0.203.0/24",
    "10.0.204.0/24",
    "10.0.205.0/24",
    "10.0.206.0/24",
    "10.0.207.0/24",
    "10.0.208.0/24",
    "10.0.209.0/24",
    "10.0.210.0/24"
  ]
  
  # Get existing CIDR blocks with error handling
  existing_cidrs = try([
    for subnet in data.aws_subnet.existing : subnet.cidr_block
  ], [])
  
  # Find first available CIDR that doesn't conflict
  available_cidr = try([
    for cidr in local.possible_cidrs : cidr
    if !contains(local.existing_cidrs, cidr)
  ][0], "10.0.250.0/24")  # Fallback CIDR if all others are taken
}

# Create subnet in the VPC with an available CIDR
resource "aws_subnet" "main" {
  vpc_id     = local.vpc_id
  cidr_block = local.available_cidr
  availability_zone = "us-east-1a"
  map_public_ip_on_launch = true
  
  tags = {
    Name = "hai-ci-subnet"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
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
  }
}

resource "aws_key_pair" "main" {
  key_name   = "hai-ci-key"
  public_key = file("${path.module}/id_rsa.pub")
  
  tags = {
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
  }
}

resource "aws_key_pair" "ec2_user" {
  key_name   = "hai-ci-ec2-user-key"
  public_key = file("${path.module}/id_rsa.pub")
  
  tags = {
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
  }
}

resource "aws_instance" "linux" {
  ami           = "ami-0c7217cdde317cfec" # Amazon Linux 2023 in us-east-1
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.main.id]
  key_name      = aws_key_pair.ec2_user.key_name
  associate_public_ip_address = true
  tags = {
    Name = "hai-linux-ci"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
  }
}

resource "aws_instance" "windows" {
  ami           = "ami-053b0d53c279acc90" # Windows Server 2019 Base in us-east-1
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.main.id]
  key_name      = aws_key_pair.main.key_name
  associate_public_ip_address = true
  
  # User data to set Administrator password
  user_data_base64 = base64encode(<<-EOF
    <powershell>
    # Set Administrator password
    $password = ConvertTo-SecureString "${var.windows_password}" -AsPlainText -Force
    Set-LocalUser -Name "Administrator" -Password $password
    
    # Enable WinRM for remote management
    Enable-PSRemoting -Force
    Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
    
    # Configure SMB for file sharing
    Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -All
    
    Write-Host "Windows instance configured successfully"
    </powershell>
    EOF
  )
  
  tags = {
    Name = "hai-windows-ci"
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
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