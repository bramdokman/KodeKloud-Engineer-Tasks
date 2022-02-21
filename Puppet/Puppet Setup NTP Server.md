While troubleshooting one of the issues on app servers in Stratos Datacenter DevOps team identified the root cause that the time isn't synchronized properly among the all app servers which causes issues sometimes. So team has decided to use a specific time server for all app servers, so that they all remain in sync. This task needs to be done using Puppet so as per details mentioned below please compete the task:

Create a puppet programming file apps.pp under /etc/puppetlabs/code/environments/production/manifests directory on puppet master node i.e on Jump Server. Within the programming file define a custom class ntpconfig to install and configure ntp server on app server 2.

Add NTP Server server 2.cn.pool.ntp.org in default configuration file on app server 2, also remember to use iburst option for faster synchronization at startup.

Please note that do not try to start/restart/stop ntp service, as we already have a scheduled restart for this service tonight and we don't want these changes to be applied right now.

Solution:

```
puppet module install puppetlabs-ntp

cd /etc/puppetlabs/code/environments/production/manifests

vi apps.pp

```

apps.pp
```
class ntpconfig {
include ntp
}

class { 'ntp':
servers => [ '2.cn.pool.ntp.org' ],
}

node 'jump_host.stratos.xfusioncorp.com','stapp01.stratos.xfusioncorp.com','stapp02.stratos.xfusioncorp.com','stapp03.stratos.xfusioncorp.com' {
include ntpconfig
}
```

