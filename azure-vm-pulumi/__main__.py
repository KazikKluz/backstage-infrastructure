import pulumi
import pulumi_azure as azure
import os


public_key = os.environ.get("ID_RSA_PUB")
instance_location = os.environ.get("INSTANCE_LOCATION")
resource_group_name = os.environ.get("RESOURCE_GROUP_NAME")
instance_name = os.environ.get("INSTANCE_NAME")
# Read existing SSH public key from .ssh folder

# Create an SSH key resource in Azure
ssh_public_key = azure.compute.SshPublicKey(
    "exampleSshPublicKey",
    resource_group_name=resource_group_name,
    location=instance_location,
    public_key=public_key
)

# Create a network interface for the VM
network_interface = azure.network.NetworkInterface(
    "exampleNetworkInterface",
    resource_group_name=resource_group_name,
    location=instance_location,
    ip_configurations=[azure.network.NetworkInterfaceIpConfigurationArgs(
        name="internal",
        subnet=azure.network.VirtualNetworkSubnetArgs(
            name="internal",
            resource_group_name=resource_group_name,
            virtual_network_name=f"{instance_name}-vnet"
        ),
        private_ip_address_allocation="Dynamic"
    )]
)

# Create a Linux VM
vm = azure.compute.LinuxVirtualMachine(
    f"{instance_name}-vm",
    location=instance_location,
    resource_group_name=resource_group_name,
    size="Standard_B1s",
    admin_username="adminuser",
    network_interface_ids=[network_interface.id],
    os_disk=azure.compute.LinuxVirtualMachineOsDiskArgs(
        caching="ReadWrite",
        storage_account_type="Standard_LRS"
    ),
    disable_password_authentication=True,
    admin_ssh_keys=[azure.compute.LinuxVirtualMachineAdminSshKeyArgs(
        username="adminuser",
        public_key=ssh_public_key.public_key
    )]
)
