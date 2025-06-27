provider "aws" {
  region = "us-east-1"
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
  }
}

# Use existing VPC or the newly created one
locals {
  vpc_id = local.existing_vpc_id != null ? local.existing_vpc_id : aws_vpc.main[0].id
}

# Create subnet in the VPC
resource "aws_subnet" "main" {
  vpc_id     = local.vpc_id
  cidr_block = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  map_public_ip_on_launch = true
  
  tags = {
    Name = "hai-ci-subnet"
  }
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
}

resource "aws_key_pair" "main" {
  key_name   = "hai-ci-key"
  public_key = file("${path.module}/id_rsa.pub")
}

resource "aws_instance" "linux" {
  ami           = "ami-0c02fb55956c7d316" # Ubuntu 22.04 LTS in us-east-1
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.main.id]
  key_name      = aws_key_pair.main.key_name
  associate_public_ip_address = true
  tags = {
    Name = "hai-linux-ci"
  }
}

resource "aws_instance" "windows" {
  ami           = "ami-053b0d53c279acc90" # Windows Server 2019 Base in us-east-1
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.main.id]
  key_name      = aws_key_pair.main.key_name
  associate_public_ip_address = true
  tags = {
    Name = "hai-windows-ci"
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