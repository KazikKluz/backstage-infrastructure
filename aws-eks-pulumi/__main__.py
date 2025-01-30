import os
import json

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

# Create IAM role for EKS Cluster
eks_cluster_role = aws.iam.Role(
    "eks-cluster-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "eks.amazonaws.com"
                },
                "Effect": "Allow",
                "Sid": ""
            }
        ]
    }"""
)

# Attach required policies to cluster role
aws.iam.RolePolicyAttachment(
    "eks-cluster-policy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    role=eks_cluster_role.name,
)

aws.iam.RolePolicyAttachment(
    "eks-service-policy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSServicePolicy",
    role=eks_cluster_role.name,
)

# Create EKS Cluster
cluster = aws.eks.Cluster(
    "eks-cluster",
    name=cluster_name,
    role_arn=eks_cluster_role.arn,
    vpc_config=aws.eks.ClusterVpcConfigArgs(
        subnet_ids=[
            public_subnet_1.id,
            public_subnet_2.id,
            private_subnet_1.id,
            private_subnet_2.id,
        ],
    ),
    tags={
        "Name": f"{cluster_name}-eks-cluster",
    },
)

# Create IAM role for Node Group
node_group_role = aws.iam.Role(
    "eks-node-group-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Effect": "Allow",
                "Sid": ""
            }
        ]
    }"""
)

# Attach required policies to node group role
aws.iam.RolePolicyAttachment(
    "eks-worker-node-policy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    role=node_group_role.name,
)

aws.iam.RolePolicyAttachment(
    "eks-cni-policy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    role=node_group_role.name,
)

aws.iam.RolePolicyAttachment(
    "eks-container-registry-policy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    role=node_group_role.name,
)

# Create EKS Node Group
node_group = aws.eks.NodeGroup(
    "eks-node-group",
    cluster_name=cluster.name,
    node_group_name=f"{cluster_name}-node-group",
    node_role_arn=node_group_role.arn,
    subnet_ids=[
        private_subnet_1.id,
        private_subnet_2.id,
    ],
    scaling_config=aws.eks.NodeGroupScalingConfigArgs(
        desired_size=desired_capacity,
        max_size=max_size,
        min_size=min_size,
    ),
    instance_types=[instance_type],
    tags={
        "Name": f"{cluster_name}-node-group",
    },
)

# Export the cluster's kubeconfig

kubeconfig = pulumi.Output.all(cluster.endpoint, cluster.certificate_authority.data, cluster.name).apply(
    lambda args: json.dumps({
        "apiVersion": "v1",
        "clusters": [{
            "cluster": {
                "server": args[0],
                "certificate-authority-data": args[1]
            },
            "name": "kubernetes",
        }],
        "contexts": [{
            "context": {
                "cluster": "kubernetes",
                "user": "aws",
            },
            "name": "aws",
        }],
        "current-context": "aws",
        "kind": "Config",
        "users": [{
            "name": "aws",
            "user": {
                "exec": {
                    "apiVersion": "client.authentication.k8s.io/v1beta1",
                    "command": "aws",
                    "args": [
                        "eks",
                        "get-token",
                        "--cluster-name",
                        args[2],
                    ],
                },
            },
        }],
    })
)

# Add these exports
pulumi.export("cluster_name", cluster.name)
pulumi.export("cluster_endpoint", cluster.endpoint)
pulumi.export("cluster_ca_data", cluster.certificate_authority.data)
pulumi.export("kubeconfig", kubeconfig)
