import pulumi
import pulumi_azure as azure
import os

# Read existing SSH public key from .ssh folder
with open(os.path.expanduser('~/.ssh/id_rsa.pub'), 'r') as f:
    ssh_public_key_data = f.read().strip()

# Create an SSH key resource in Azure
ssh_public_key = azure.compute.SshPublicKey(
    "exampleSshPublicKey",
    resource_group_name="example-resource-group",
    location="WestUS",
    public_key=ssh_public_key_data
)

# Create a network interface for the VM
network_interface = azure.network.NetworkInterface(
    "exampleNetworkInterface",
    resource_group_name="example-resource-group",
    ip_configurations=[azure.network.NetworkInterfaceIpConfigurationArgs(
        name="internal",
        subnet=azure.network.VirtualNetworkSubnetArgs(
            name="internal",
            resource_group_name="example-resource-group",
            virtual_network_name="example-vnet"
        ),
        private_ip_address_allocation="Dynamic"
    )]
)

# Create a Linux VM
vm = azure.compute.LinuxVirtualMachine(
    "exampleLinuxVM",
    location="WestUS",
    resource_group_name="example-resource-group",
    size="Standard_B2s",
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
