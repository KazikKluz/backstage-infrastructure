"Pulumi script for provisionining RDS instance on AWS"

import os

import pulumi
from pulumi_aws import ec2, rds

instance_name = os.environ.get("INSTANCE_NAME")
instance_type = os.environ.get("INSTANCE_TYPE")
instance_storage = os.environ.get("INSTANCE_STORAGE")
instance_password = os.environ.get("INSTANCE_PASSWORD")
instance_username = os.environ.get("INSTANCE_USERNAME")
instance_region = os.environ.get("INSTANCE_REGION")
instance_engine = os.environ.get("INSTANCE_ENGINE")
local_ip = os.environ.get("LOCAL_IP")


# Create a VPC for the RDS instance
vpc = ec2.Vpc(
    "my-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={"Name": f"{instance_name}-vpc"},
)

# Create an Internet Gateway
internet_gateway = ec2.InternetGateway(
    "my-internet-gateway",
    vpc_id=vpc.id,
    tags={"Name": f"{instance_name}-internet-gateway"},
)

# Create a route table
route_table = ec2.RouteTable(
    "my-route-table",
    vpc_id=vpc.id,
    routes=[
        {
            "cidr_block": "0.0.0.0/0",
            "gateway_id": internet_gateway.id,
        }
    ],
    tags={"Name": f"{instance_name}-route-table"},
)


# Create subnets in different availability zones
subnet1 = ec2.Subnet(
    "subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone={f"{instance_region}a"},  # Change this according to your region
    map_public_ip_on_launch=True,
    tags={"Name": f"{instance_name}-rds-subnet-1"},
)

subnet2 = ec2.Subnet(
    "subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone={f"{instance_region}b"},  # Change this according to your region
    map_public_ip_on_launch=True,
    tags={"Name": f"{instance_name}-rds-subnet-2"},
)

# Associate the route table with the subnets
route_table_association1 = ec2.RouteTableAssociation(
    "rt-association1",
    subnet_id=subnet1.id,
    route_table_id=route_table.id,
)

route_table_association2 = ec2.RouteTableAssociation(
    "rt-association2",
    subnet_id=subnet2.id,
    route_table_id=route_table.id,
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
            "cidr_blocks": [f"{local_ip}/32"],
        }
    ],
    tags={"Name": f"{instance_name}-db-security-group"},
)

# Create an RDS instance
db_instance = rds.Instance(
    f"{instance_name}-db-instance",
    engine="mysql",
    instance_class=instance_type,
    allocated_storage=instance_storage,  # type: ignore
    username=instance_username,
    password=instance_password,
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[db_security_group.id],
    skip_final_snapshot=True,  # For development only, not recommended for production
    tags={"Name": f"{instance_name}-db-instance"},
)


# Export the necessary values
pulumi.export("rds_endpoint", db_instance.endpoint)
pulumi.export("rds_port", db_instance.port)
