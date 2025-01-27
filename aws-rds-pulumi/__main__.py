"Pulumi script for provisionining RDS instance on AWS"

import os

import pulumi
from pulumi_aws import ec2, rds, s3

instance_name = os.environ.get("INSTANCE_NAME")
instance_type = os.environ.get("INSTANCE_TYPE")
instance_storage = os.environ.get("INSTANCE_STORAGE")
instance_password = os.environ.get("INSTANCE_PASSWORD")
instance_username = os.environ.get("INSTANCE_USERNAME")
instance_region = os.environ.get("INSTANCE_REGION")

# Create an AWS resource (S3 Bucket)
bucket = s3.BucketV2(f"{instance_name}-bucket")

# Create a VPC for the RDS instance
vpc = ec2.Vpc(
    "my-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={"Name": f"{instance_name}-vpc"},
)


# Create subnets in different availability zones
subnet1 = ec2.Subnet(
    "subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-east-1a",  # Change this according to your region
    tags={"Name": f"{instance_name}-rds-subnet-1"},
)

subnet2 = ec2.Subnet(
    "subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-east-1b",  # Change this according to your region
    tags={"Name": f"{instance_name}-rds-subnet-2"},
)

# Create a subnet group for RDS
db_subnet_group = rds.SubnetGroup(
    "my-db-subnet-group",
    subnet_ids=[subnet1.id, subnet2.id],
    tags={"Name": f"{instance_name}-db-subnet-group"},
)

# Create a security group for RDS
db_security_group = ec2.SecurityGroup(
    f"{instance_name}-db-security-group",
    vpc_id=vpc.id,
    description="Allow database access",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 3306,  # MySQL default port
            "to_port": 3306,
            # Be more restrictive in production
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
    tags={"Name": f"{instance_name}-db-security-group"},
)

# Create an RDS instance
db_instance = rds.Instance(
    f"{instance_name}-db-instance",
    engine="mysql",
    instance_class="db.t4g.micro",
    allocated_storage=instance_storage,  # type: ignore
    username="admin",
    password="your-password-here",  # Use pulumi config for sensitive data
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[db_security_group.id],
    skip_final_snapshot=True,  # For development only, not recommended for production
    tags={"Name": f"{instance_name}-db-instance"},
)


# Export the necessary values
pulumi.export("bucket_name", bucket.id)
pulumi.export("rds_endpoint", db_instance.endpoint)
pulumi.export("rds_port", db_instance.port)
