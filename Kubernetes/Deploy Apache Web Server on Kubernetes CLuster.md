There is an application that needs to be deployed on Kubernetes cluster under Apache web server. The Nautilus application development team has asked the DevOps team to deploy it. We need to develop a template as per requirements mentioned below:

Create a namespace named as httpd-namespace-devops.

Create a deployment named as httpd-deployment-devops under newly created namespace. For the deployment use httpd image with latest tag only and remember to mention the tag i.e httpd:latest, and make sure replica counts are 2.

Create a service named as httpd-service-devops under same namespace to expose the deployment, nodePort should be 30004.

Note: The kubectl utility on jump_host has been configured to work with the kubernetes cluster.

```
kubectl create namespace httpd-service-devops
```

```
apiVersion: v1
kind: Service
metadata:
  name: httpd-service-devops
  namespace: httpd-namespace-devops
spec:
  type: NodePort
  selector:
    app: httpd_app_devops
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30004
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: httpd-deployment-devops
  namespace: httpd-namespace-devops
  labels:
    app: httpd_app_devops
spec:
  replicas: 2
  selector:
    matchLabels:
      app: httpd_app_devops
  template:
    metadata:
      labels:
        app: httpd_app_devops
    spec:
      containers:
        - name: httpd-container-devops
          image: httpd:latest
          ports:
            - containerPort: 80
```