A new teammate has joined the Nautilus application development team, the application development team has asked the DevOps team to create a new user account for the new teammate on application server 3 in Stratos Datacenter. The task needs to be performed using Puppet only. You can find more details below about the task.

Create a Puppet programming file media.pp under /etc/puppetlabs/code/environments/production/manifests directory on master node i.e Jump Server, and using Puppet user resource add a user on all app servers as mentioned below:

Create a user ammar and set its UID to 1375 on Puppet agent nodes 3 i.e App Servers 3.

Solution:

```
cd /etc/puppetlabs/code/environments/production/manifests

sudo vi media.pp

ssh banner@stapp03

sudo puppet agent -t

```

```
node 'stapp01.stratos.xfusioncorp.com','stapp02.stratos.xfusioncorp.com','stapp03.stratos.xfusioncorp.com' {
include user
}

class user {
   user { 'ammar':
      ensure => present,
      uid => '1375'
   }
}
```