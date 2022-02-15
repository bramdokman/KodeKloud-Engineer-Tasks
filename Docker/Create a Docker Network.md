The Nautilus DevOps team needs to set up several docker environments for different applications. One of the team members has been assigned a ticket where he has been asked to create some docker networks to be used later. Complete the task based on the following ticket description:



a. Create a docker network named as blog on App Server 1 in Stratos DC.

b. Configure it to use bridge drivers.

c. Set it to use subnet 192.168.0.0/24 and iprange 192.168.0.1/24.


ssh tony@stapp01

docker network create \
  blog \
  --driver=bridge \
  --subnet=192.168.0.0/24 \
  --ip-range=192.168.0.1/24 