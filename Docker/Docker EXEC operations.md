One of the Nautilus DevOps team members was working to configure services on a kkloud container that is running on App Server 1 in Stratos Datacenter. Due to some personal work he is on PTO for the rest of the week, but we need to finish his pending work ASAP. Please complete the remaining work as per details given below:


a. Install apache2 in kkloud container using apt that is running on App Server 1 in Stratos Datacenter.

b. Configure Apache to listen on port 8087 instead of default http port. Do not bind it to listen on specific IP or hostname only, i.e it should listen on localhost, 127.0.0.1, container ip, etc.

c. Make sure Apache service is up and running inside the container. Keep the container in running state at the end.

Solution:

Log in to mentioned app server in the question

ssh tony@stapp01

Find the docker container

sudo docker ps

Enter inside the docker container

docker exec -it kkloud /bin/bash

Install the apache2 and update the configuration according to mention ports and hostname

apt install apache2 -y

cd  /etc/apache2

sed -i 's/Listen 80/Listen 8087/g' ports.conf

sed -i 's/:80/:8087/g' apache2.conf

sed -i 's/#ServerName www.example.com/ServerName localhost/g' apache2.conf

Restart and check the status of apache

service apache2 start

service apache2 enable

service apache2 status