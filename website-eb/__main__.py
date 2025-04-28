
import json
import zipfile
import os

import pulumi
import pulumi_aws as aws


solution_stack_name = "64bit Amazon Linux 2023 v4.5.0 running Docker"

app_name = os.environ.get("NAME")
env_name = os.environ.get("ENVIRONMENT_NAME")
docker_image = os.environ.get("DOCKER_IMAGE")
region = os.environ.get("REGION")
port = os.environ.get("PORT")
asg_min_size = os.environ.get("ASG_MIN_SIZE")
asg_max_size = os.environ.get("ASG_MAX_SIZE")
# Check if required environment variables are set


# Create an IAM role for Elastic Beanstalk service
eb_service_role = aws.iam.Role(
    "eb-service-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "elasticbeanstalk.amazonaws.com"
            }
        }]
    })
)

# Attach policies to the service role
aws.iam.RolePolicyAttachment(
    "eb-service-policy",
    role=eb_service_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSElasticBeanstalkService"
)

aws.iam.RolePolicyAttachment(
    "eb-enhanced-health-policy",
    role=eb_service_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSElasticBeanstalkEnhancedHealth"
)

# Create an IAM role for EC2 instances
eb_instance_role = aws.iam.Role(
    "eb-instance-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            }
        }]
    })
)

# Attach policies to the instance role
aws.iam.RolePolicyAttachment(
    "eb-instance-policy",
    role=eb_instance_role.name,
    policy_arn="arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier"
)

# Create an instance profile for EC2 instances
eb_instance_profile = aws.iam.InstanceProfile(
    "eb-instance-profile",
    role=eb_instance_role.name
)

# Create an Elastic Beanstalk Application
app = aws.elasticbeanstalk.Application(
    app_name,
    name=app_name,
    description="A containerized application deployed with Pulumi"
)

# Create a Dockerrun.aws.json file content for Elastic Beanstalk
dockerrun_content = {
    "AWSEBDockerrunVersion": "1",
    "Image": {
        "Name": docker_image,
        "Update": "true"
    },
    "Ports": [
        {
            "ContainerPort": port
        }
    ],
    "Logging": "/var/log/app"
}

# Save Dockerrun.aws.json to a zip file for Elastic Beanstalk
dockerrun_file = "Dockerrun.aws.json"
zip_file = "dockerrun.zip"

with open(dockerrun_file, "w") as f:
    json.dump(dockerrun_content, f)

with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(dockerrun_file)

# Upload the zip file to S3 for Elastic Beanstalk
s3_bucket = aws.s3.Bucket(
    f"{app_name}-bucket",
    bucket=f"{app_name}-artifacts-{pulumi.get_stack()}"
)

s3_object = aws.s3.BucketObject(
    f"{app_name}-dockerrun",
    bucket=s3_bucket.id,
    source=pulumi.FileAsset(zip_file),
    key=f"dockerrun-{app_name}.zip"
)

# Create an Elastic Beanstalk Application Version
app_version = aws.elasticbeanstalk.ApplicationVersion(
    f"{app_name}-version",
    application=app.name,
    name="v1.0.0",
    bucket=s3_bucket.id,
    key=s3_object.key
)

# Create an Elastic Beanstalk Environment
env = aws.elasticbeanstalk.Environment(
    f"{app_name}-env",
    application=app.name,
    name=env_name,
    solution_stack_name=solution_stack_name,
    version=app_version.name,
    settings=[
        aws.elasticbeanstalk.EnvironmentSettingArgs(
            namespace="aws:elasticbeanstalk:command",
            name="ServiceRole",
            value=eb_service_role.name
        ),
        aws.elasticbeanstalk.EnvironmentSettingArgs(
            namespace="aws:autoscaling:asg",
            name="MinSize",
            value=asg_min_size
        ),
        aws.elasticbeanstalk.EnvironmentSettingArgs(
            namespace="aws:autoscaling:asg",
            name="MaxSize",
            value=asg_max_size
        ),
        aws.elasticbeanstalk.EnvironmentSettingArgs(
            namespace="aws:elasticbeanstalk:environment",
            name="EnvironmentType",
            value="LoadBalanced"
        ),
        aws.elasticbeanstalk.EnvironmentSettingArgs(
            namespace="aws:autoscaling:launchconfiguration",
            name="IamInstanceProfile",
            value=eb_instance_profile.name
        )
    ]
)

# Export the Elastic Beanstalk Environment URL
pulumi.export("environment_url", env.cname)
