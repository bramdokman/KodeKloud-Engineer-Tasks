Last week the Nautilus DevOps team met with the application development team and decided to containerize several of their applications. The DevOps team wants to do some testing per the following:

Install docker-ce and docker-compose packages on App Server 2.

Start docker service.

Solution:

```

ssh steve@stapp02

sudo su

yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

yum install docker-ce docker-compose -y

systemctl start docker

systemctl status docker

```