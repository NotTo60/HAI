provider "aws" {
  region = "us-east-1"
}

# Use existing VPC instead of creating new one
data "aws_vpc" "existing" {
  # You can specify by ID, CIDR block, or tags
  # Option 1: By VPC ID (most specific)
  # id = "vpc-12345678"
  
  # Option 2: By CIDR block
  cidr_block = "10.0.0.0/16"
  
  # Option 3: By tags (recommended for CI)
  # tags = {
  #   Name = "default"
  # }
}

# Use existing subnet instead of creating new one
data "aws_subnet" "existing" {
  # Option 1: By subnet ID
  # id = "subnet-12345678"
  
  # Option 2: By availability zone and VPC
  availability_zone = "us-east-1a"
  vpc_id            = data.aws_vpc.existing.id
  
  # Option 3: By CIDR block
  # cidr_block = "10.0.1.0/24"
}

resource "aws_security_group" "main" {
  vpc_id = data.aws_vpc.existing.id

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
  subnet_id     = data.aws_subnet.existing.id
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
  subnet_id     = data.aws_subnet.existing.id
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