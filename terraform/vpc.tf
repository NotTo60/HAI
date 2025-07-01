# VPC and networking

data "aws_vpcs" "all" {}

locals {
  existing_vpc_id = length(data.aws_vpcs.all.ids) > 0 ? data.aws_vpcs.all.ids[0] : null
}

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

locals {
  vpc_id = local.existing_vpc_id != null ? local.existing_vpc_id : aws_vpc.main[0].id
}

data "aws_subnets" "existing" {
  filter {
    name   = "vpc-id"
    values = [local.vpc_id]
  }
}

data "aws_subnet" "existing" {
  for_each = toset(data.aws_subnets.existing.ids)
  id       = each.value
}

data "aws_vpc" "selected" {
  id = local.vpc_id
}

locals {
  existing_cidrs = [for subnet in data.aws_subnet.existing : subnet.cidr_block]
  potential_cidrs = [for i in range(1, 255) : "10.0.${i}.0/24"]
  available_cidr = [for cidr in local.potential_cidrs : cidr if !contains(local.existing_cidrs, cidr)][0]
}

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

data "aws_internet_gateway" "existing" {
  filter {
    name   = "attachment.vpc-id"
    values = [local.vpc_id]
  }
}

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

locals {
  igw_id = length(data.aws_internet_gateway.existing) > 0 ? data.aws_internet_gateway.existing.id : aws_internet_gateway.main[0].id
}

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

resource "aws_route_table_association" "main" {
  subnet_id      = aws_subnet.main.id
  route_table_id = aws_route_table.main.id
} 