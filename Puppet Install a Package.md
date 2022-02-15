Some new packages need to be installed on app server 2 in Stratos Datacenter. The Nautilus DevOps team has decided to install the same using Puppet. Since jump host is already configured to run as Puppet master server and all app servers are already configured to work as the puppet agent nodes, we need to create required manifests on the Puppet master server so that the same can be applied on all Puppet agent nodes. Please find more details about the task below.

Create a Puppet programming file games.pp under /etc/puppetlabs/code/environments/production/manifests directory on master node i.e Jump Server and using puppet package resource perform the tasks given below.

Install package httpd through Puppet package resource only on App server 2i.epuppet agent node 2`.

Please make sure to run the puppet agent test using sudo on agent nodes, otherwise you can face certificate issues. In that case you will have to clean the certificates first and then you will be able to run the puppet agent test. Before clicking on the Check button please make sure to verify puppet server and puppet agent services are up and running on the respective servers, also please make sure to run puppet agent test to apply/test the changes manually first. Please note that once lab is loaded, the puppet server service should start automatically on puppet master server, however it can take upto 2-3 minutes to start.


Solution:

Create games.pp under /etc/puppetlabs/code/environments/production/manifests:

class httpd {
package { 'httpd':
ensure => installed,
}
}

node 'stapp02.stratos.xfusioncorp.com' {
  include httpd
}


ssh stapp02

puppet agent -tv