A new java-based application is ready to be deployed on a Kubernetes cluster. The development team had a meeting with the DevOps team to share the requirements and application scope. The team is ready to setup an application stack for it under their existing cluster. Below you can find the details for this:

Create a namespace named tomcat-namespace-xfusion.

Create a deployment for tomcat app which should be named as tomcat-deployment-xfusion under the same namespace you created. Replica count should be 1, the container should be named as tomcat-container-xfusion, its image should be gcr.io/kodekloud/centos-ssh-enabled:tomcat and its container port should be 8080.

Create a service for tomcat app which should be named as tomcat-service-xfusion under the same namespace you created. Service type should be NodePort and nodePort should be 32227.

Before clicking on Check button please make sure the application is up and running.

You can use any labels as per your choice.

Note: The kubectl on jump_host has been configured to work with the kubernetes cluster.

Solution:

```
kubectl create namespace tomcat-namespace-xfusion

kubectl apply -f deploy.yml
```

Deploy.yml:
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tomcat-deployment-xfusion
  namespace: tomcat-namespace-xfusion
  labels:
    app: tomcat-deployment-xfusion
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tomcat-deployment-xfusion
  template:
    metadata:
      labels:
        app: tomcat-deployment-xfusion
    spec:
      containers:
      - name: tomcat-container-xfusion
        image: gcr.io/kodekloud/centos-ssh-enabled:tomcat
        ports:
        - containerPort: 8080
        
---        
apiVersion: v1
kind: Service
metadata:
  name: tomcat-service-xfusion
  namespace: tomcat-namespace-xfusion
spec:
  type: NodePort
  selector:
    app: tomcat-deployment-xfusion
  ports:
    - port: 8080
      protocol: TCP
      targetPort: 8080
      nodePort: 32227
```