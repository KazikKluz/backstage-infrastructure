import os

import pulumi
import pulumi_aws as aws

# Configuration

cluster_name = os.environ.get("CLUSTER_NAME")
instance_type = os.environ.get("INSTANCE_TYPE")
cluster_region = os.environ.get("CLUSTER_REGION")
desired_capacity = os.environ.get("DESIRED_CAPACITY")
min_size = os.environ.get("MIN_SIZE")
max_size = os.environ.get("MAX_SIZE")

# VPC Configuration
vpc = aws.ec2.Vpc(
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
public_subnet_1 = aws.ec2.Subnet(
    "public-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone=f"{cluster_region}a",
    map_public_ip_on_launch=True,
    tags={
        "Name": f"{cluster_name}-public-subnet-1",
        "kubernetes.io/role/elb": "1",
    },
)

public_subnet_2 = aws.ec2.Subnet(
    "public-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone=f"{cluster_region}b",
    map_public_ip_on_launch=True,
    tags={
        "Name": f"{cluster_name}-public-subnet-2",
        "kubernetes.io/role/elb": "1",
    },
)

# Create private subnets
private_subnet_1 = aws.ec2.Subnet(
    "private-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone=f"{cluster_region}a",
    tags={
        "Name": f"{cluster_name}-private-subnet-1",
        "kubernetes.io/role/internal-elb": "1",
    },
)

private_subnet_2 = aws.ec2.Subnet(
    "private-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.4.0/24",
    availability_zone=f"{cluster_region}b",
    tags={
        "Name": f"{cluster_name}-private-subnet-2",
        "kubernetes.io/role/internal-elb": "1",
    },
)

# Create Internet Gateway
igw = aws.ec2.InternetGateway(
    "vpc-igw",
    vpc_id=vpc.id,
    tags={
        "Name": f"{cluster_name}-igw",
    },
)

# Create public route table
public_rt = aws.ec2.RouteTable(
    "public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ),
    ],
    tags={
        "Name": f"{cluster_name}-public-rt",
    },
)

# Associate public subnets with public route table
public_subnet_1_rta = aws.ec2.RouteTableAssociation(
    "public-subnet-1-rta",
    subnet_id=public_subnet_1.id,
    route_table_id=public_rt.id,
)

public_subnet_2_rta = aws.ec2.RouteTableAssociation(
    "public-subnet-2-rta",
    subnet_id=public_subnet_2.id,
    route_table_id=public_rt.id,
)


cluster = aws.eks.Cluster(
    "eks-cluster",
    vpc_id=vpc.id,
    subnet_ids=[
        public_subnet_1.id,
        public_subnet_2.id,
        private_subnet_1.id,
        private_subnet_2.id,
    ],
    instance_type=instance_type,
    desired_capacity=desired_capacity,
    min_size=min_size,
    max_size=max_size,
    node_associate_public_ip_address=False,
    tags={
        "Name": f"{cluster_name}-eks-cluster",
    },
)


# Export the cluster's kubeconfig
pulumi.export("kubeconfig", cluster.kubeconfig)
