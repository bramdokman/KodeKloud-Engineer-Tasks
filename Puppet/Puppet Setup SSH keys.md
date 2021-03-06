The Puppet master and Puppet agent nodes have been set up by the Nautilus DevOps team to perform some testing. In Stratos DC all app servers have been configured as Puppet agent nodes. They want to setup a password less SSH connection between Puppet master and Puppet agent nodes and this task needs to be done using Puppet itself. Below are details about the task:

Create a Puppet programming file news.pp under /etc/puppetlabs/code/environments/production/manifests directory on the Puppet master node i.e on Jump Server. Define a class ssh_node1 for agent node 1 i.e App Server 1, ssh_node2 for agent node 2 i.e App Server 2, ssh_node3 for agent node3 i.e App Server 3. You will need to generate a new ssh key for thor user on Jump Server, that needs to be added on all App Servers.

Configure a password less SSH connection from puppet master i.e jump host to all App Servers. However, please make sure the key is added to the authorized_keys file of each app's sudo user (i.e tony for App Server 1).

Notes: :- Before clicking on the Check button please make sure to verify puppet server and puppet agent services are up and running on the respective servers, also please make sure to run puppet agent test to apply/test the changes manually first.

:- Please note that once lab is loaded, the puppet server service should start automatically on puppet master server, however it can take upto 2-3 minutes to start.

Solution:

```

cat /root/.ssh/id_rsa.pub

copy key

cd /etc/puppetlabs/code/environments/production/manifests

vi news.pp

```

Puppet file:

```
$public_key = 'AAAAB3NzaC1yc2EAAAADAQABAAABAQDPRCd5qERxOQgXkHrEmIV701X8UbIrhcECzJgAY2x95i4upimadIj+va9qnRnMlyTPalWYJGOJ9ZpGnMsehUzrGC0kkDHTwuOe/ZyVbX22AGMCIgE1BbaJbrV13lV08bgNCLM2fy3QCmpIxchaGhuJmeIX8+whFbrO51mugGtXuXCkVs2B9EJHl+wMgmfV8VuWCJzJ/dkY3TaC9tMMyZdU21kdyoEYzZfZJc46QByvVApFh7ZGANDw/NsCnYPAsGrAgq/XYfNNtwO+kszZwPChvB6un8DlnoL6EDs9oQYPfBlTsyJz84TOLY/UJnFI91UQq2Q9XEPNBxesepLltlJT'



```` 