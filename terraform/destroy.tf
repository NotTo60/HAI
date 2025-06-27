provider "aws" {
  region = "us-east-1"
}

# Simple resource definitions for destruction
# These will be imported or created as needed for destruction

resource "aws_subnet" "main" {
  vpc_id     = "vpc-placeholder"
  cidr_block = "10.0.200.0/24"
  availability_zone = "us-east-1a"
  
  tags = {
    Name = "hai-ci-subnet"
  }
  
  lifecycle {
    ignore_changes = all
  }
}

resource "aws_security_group" "main" {
  vpc_id = "vpc-placeholder"
  name   = "hai-ci-sg"
  
  lifecycle {
    ignore_changes = all
  }
}

resource "aws_key_pair" "main" {
  key_name   = "hai-ci-key"
  public_key = "dummy-key"
  
  lifecycle {
    ignore_changes = all
  }
}

resource "aws_key_pair" "ec2_user" {
  key_name   = "hai-ci-ec2-user-key"
  public_key = "dummy-key"
  
  lifecycle {
    ignore_changes = all
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = "vpc-placeholder"
  
  tags = {
    Name = "hai-ci-igw"
  }
  
  lifecycle {
    ignore_changes = all
  }
}

resource "aws_route_table" "main" {
  vpc_id = "vpc-placeholder"
  
  tags = {
    Name = "hai-ci-rt"
  }
  
  lifecycle {
    ignore_changes = all
  }
}

resource "aws_route_table_association" "main" {
  subnet_id      = aws_subnet.main.id
  route_table_id = aws_route_table.main.id
  
  lifecycle {
    ignore_changes = all
  }
} 