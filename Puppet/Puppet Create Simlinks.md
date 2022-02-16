Some directory structure in the Stratos Datacenter needs to be changed, there is a directory that needs to be linked to the default Apache document root. We need to accomplish this task using Puppet, as per the instructions given below:



Create a puppet programming file news.pp under /etc/puppetlabs/code/environments/production/manifests directory on puppet master node i.e on Jump Server. Within that define a class symlink and perform below mentioned tasks:

Create a symbolic link through puppet programming code. The source path should be /opt/sysops and destination path should be /var/www/html on Puppet agents 3 i.e on App Servers 3.

Create a blank file blog.txt under /opt/sysops directory on puppet agent 3 nodes i.e on App Servers 3.

Notes: :- Please make sure to run the puppet agent test using sudo on agent nodes, otherwise you can face certificate issues. In that case you will have to clean the certificates first and then you will be able to run the puppet agent test.

:- Before clicking on the Check button please make sure to verify puppet server and puppet agent services are up and running on the respective servers, also please make sure to run puppet agent test to apply/test the changes manually first.

:- Please note that once lab is loaded, the puppet server service should start automatically on puppet master server, however it can take upto 2-3 minutes to start.

Solution:

```

cd /etc/puppetlabs/code/environments/production/manifests

vi news.pp

```

```

class symlink {

  # First create a symlink to /var/www/html

  file { '/opt/sysops':

    ensure => 'link',

    target => '/var/www/html',

  }

   # Now create media.txt under /opt/sysops

  file { '/opt/sysops/blog.txt':

    ensure => 'present',

  }

}

node 'stapp01.stratos.xfusioncorp.com', 'stapp02.stratos.xfusioncorp.com', 'stapp03.stratos.xfusioncorp.com' {

  include symlink

}

```

```
ssh banner@stapp03

puppet agent -tv

```