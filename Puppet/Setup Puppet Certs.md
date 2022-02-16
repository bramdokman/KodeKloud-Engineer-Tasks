The Nautilus DevOps team has set up a puppet master and an agent node in Stratos Datacenter. Puppet master is running on jump host itself (also note that Puppet master node is also running as Puppet CA server) and Puppet agent is running on App Server 3. Since it is a fresh set up, the team wants to sign certificates for puppet master as well as puppet agent nodes so that they can proceed with the next steps of set up. You can find more details about the task below:



Puppet server and agent nodes are already have required packages, but you may need to start puppetserver (on master) and puppet service on both nodes.

Assign and sign certificates for both master and agent node.

Solution:

```

sudo vi /etc/hosts

add puppet alias for jump_host

systemctl status puppet

puppetserver ca list --all

ssh banner@stapp03

vi /etc/hosts

add puppet alias for jump_host

systemctl restart puppet

exit

puppetserver ca list --all

puppetserver ca sign --all

ssh banner@stapp03

puppet agent -t

```
