One of the Nautilus developer was working to test new changes on a container. He wants to keep a backup of his changes to the container. A new request has been raised for the DevOps team to create a new image from this container. Below are more details about it:

a. Create an image blog:xfusion on Application Server 1 from a container ubuntu_latest that is running on same server.


Solution:

```
ssh tony@stapp01

sudo su

docker commit ubuntu_latest blog:xfusion

docker images
```