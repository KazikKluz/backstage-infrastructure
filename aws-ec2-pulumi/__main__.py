import os

import pulumi
import pulumi_aws as aws

# Choose the lates minimal amzn2 Linux AMI
ami = aws.ec2.get_ami(
    most_recent="true",
    owners=["amazon"],
    filters=[aws.ec2.GetAmiFilterArgs(name="name", values=["*amzn2-ami-minimal-hvm*"])],
)

group = aws.ec2.SecurityGroup(
    "web-secgrp",
    description="Enable SSH access",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=22, to_port=22, cidr_blocks=["0.0.0.0/0"]
        )
    ],
)


public_key = os.environ.get("ID_RSA_PUB")

print(f"Public Key: '{public_key}'\n")

if public_key is not None:
    public_key = public_key.strip()

print(f"Public Key: '{public_key}'\n")

keypair = aws.ec2.KeyPair("deployer-key", public_key=public_key)

server = aws.ec2.Instance(
    "backstage-pulumi-server",
    instance_type=os.environ.get("INSTANCE_TYPE"),
    tags={
        "Name": os.environ.get("instanceName"),
    },
    vpc_security_group_ids=[group.id],
    key_name=keypair.key_name,
    ami=ami.id,
)

pulumi.export("instance_type", server.instance_type)
pulumi.export("public_key", keypair.public_key)
pulumi.export("public_ip", server.public_ip)
pulumi.export("public_dns", server.public_dns)
