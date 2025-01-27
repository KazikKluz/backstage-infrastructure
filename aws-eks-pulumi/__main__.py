import os

import pulumi
import pulumi_aws as aws
import pulumi_eks as eks
from pulumi_aws import ec2, iam

# Configuration

cluster_name = os.environ.get("CLUSTER_NAME")
instance_type = os.environ.get("INSTANCE_TYPE")
instance_storage = os.environ.get("INSTANCE_STORAGE")
instance_password = os.environ.get("INSTANCE_PASSWORD")
instance_username = os.environ.get("INSTANCE_USERNAME")
instance_region = os.environ.get("INSTANCE_REGION")

# VPC Configuration
vpc = ec2.Vpc(
    "eks-vpc",
    cidr_block="10.0.0.0/16",
    instance_tenancy="default",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": f"{cluster_name}-vpc",
    },
)

# Create public subnets
public_subnet_1 = ec2.Subnet(
    "public-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-west-2a",
    map_public_ip_on_launch=True,
    tags={
        "Name": f"{cluster_name}-public-subnet-1",
        "kubernetes.io/role/elb": "1",
    },
)

public_subnet_2 = ec2.Subnet(
    "public-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-west-2b",
    map_public_ip_on_launch=True,
    tags={
        "Name": f"{cluster_name}-public-subnet-2",
        "kubernetes.io/role/elb": "1",
    },
)

# Create private subnets
private_subnet_1 = ec2.Subnet(
    "private-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone="us-west-2a",
    tags={
        "Name": f"{cluster_name}-private-subnet-1",
        "kubernetes.io/role/internal-elb": "1",
    },
)

private_subnet_2 = ec2.Subnet(
    "private-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.4.0/24",
    availability_zone="us-west-2b",
    tags={
        "Name": f"{project_name}-private-subnet-2-{stack_name}",
        "kubernetes.io/role/internal-elb": "1",
    },
)

# Create Internet Gateway
igw = ec2.InternetGateway(
    "vpc-igw",
    vpc_id=vpc.id,
    tags={
        "Name": f"{project_name}-igw-{stack_name}",
    },
)

# Create public route table
public_rt = ec2.RouteTable(
    "public-rt",
    vpc_id=vpc.id,
    routes=[
        ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ),
    ],
    tags={
        "Name": f"{project_name}-public-rt-{stack_name}",
    },
)

# Associate public subnets with public route table
public_subnet_1_rta = ec2.RouteTableAssociation(
    "public-subnet-1-rta",
    subnet_id=public_subnet_1.id,
    route_table_id=public_rt.id,
)

public_subnet_2_rta = ec2.RouteTableAssociation(
    "public-subnet-2-rta",
    subnet_id=public_subnet_2.id,
    route_table_id=public_rt.id,
)

# Create EKS Cluster
cluster = eks.Cluster(
    "eks-cluster",
    vpc_id=vpc.id,
    subnet_ids=[
        public_subnet_1.id,
        public_subnet_2.id,
        private_subnet_1.id,
        private_subnet_2.id,
    ],
    instance_type="t3.medium",
    desired_capacity=2,
    min_size=1,
    max_size=3,
    node_associate_public_ip_address=False,
    tags={
        "Name": f"{project_name}-eks-cluster-{stack_name}",
    },
)

# Export the cluster's kubeconfig
pulumi.export("kubeconfig", cluster.kubeconfig)
