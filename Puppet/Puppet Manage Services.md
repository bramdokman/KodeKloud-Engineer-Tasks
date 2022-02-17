New packages need to be installed on some of the app servers in Stratos Datacenter. The Nautilus DevOps team has decided to install the same using Puppet. Since jump host is already configured to run as Puppet master server and all app servers are already configured to work as puppet agent nodes, we need to create the required manifests on the Puppet master server so that it can be applied on the required Puppet agent node. Please find more details about the task below.



Create a Puppet programming file cluster.pp under /etc/puppetlabs/code/environments/production/manifests directory on master node i.e Jump Host to perform the below given tasks.

Install package vsftpd using puppet package resource and start its service using puppet service resource on Puppet agent node 1 i.e App Server 1.
Notes: :- Please make sure to run the puppet agent test using sudo on agent nodes, otherwise you can face certificate issues. In that case you will have to clean the certificates first and then you will be able to run the puppet agent test.

:- Before clicking on the Check button please make sure to verify puppet server and puppet agent services are up and running on the respective servers, also please make sure to run puppet agent test to apply/test the changes manually first.

:- Please note that once lab is loaded, the puppet server service should start automatically on puppet master server, however it can take upto 2-3 minutes to start.

Solution:

```



```