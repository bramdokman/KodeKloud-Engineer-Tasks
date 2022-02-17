There are some applications that need to be deployed on Kubernetes cluster and these apps have some pre-requisites where some configurations need to be changed before deploying the app container. Some of these changes cannot be made inside the images so the DevOps team has come up with a solution to use init containers to perform these tasks during deployment. Below is a sample scenario that the team is going to test first.



Create a Deployment named as ic-deploy-devops.

Configure spec as replicas should be 1, labels app should be ic-devops, template's metadata lables app should be the same ic-devops.

The initContainers should be named as ic-msg-devops, use image debian, preferably with latest tag and use command '/bin/bash', '-c' and 'echo Init Done - Welcome to xFusionCorp Industries > /ic/official'. The volume mount should be named as ic-volume-devops and mount path should be /ic.

Main container should be named as ic-main-devops, use image debian, preferably with latest tag and use command '/bin/bash', '-c' and 'while true; do cat /ic/official; sleep 5; done'. The volume mount should be named as ic-volume-devops and mount path should be /ic.

Volume to be named as ic-volume-devops and it should be an emptyDir type.

Note: The kubectl utility on jump_host has been configured to work with the kubernetes cluster.

Solution:

```

apiVersion: apps/v1
kind: Deployment
metadata:
   name: ic-deploy-devops
   labels:
    app: ic-devops
spec:
  replicas: 1
  selector:
   matchLabels:
    app: ic-devops
  template:
   metadata:
    labels:
      app: ic-devops
   spec:
    containers:
     - name: ic-main-devops
       image: debian:latest
       command: ["/bin/bash"]
       args: ["-c", "while true; do cat /ic/official; sleep 5; done"]
       volumeMounts:
        - mountPath: /ic
          name: ic-volume-devops
    initContainers:
    - name: ic-msg-devops
      image: debian:latest
      command: ["/bin/bash"]
      args: ["-c", "echo Init Done - Welcome to xFusionCorp Industries > /ic/official"]
      volumeMounts:
      - name: ic-volume-devops
        mountPath: /ic
    volumes:
    - name: ic-volume-devops
      emptyDir: {}

```