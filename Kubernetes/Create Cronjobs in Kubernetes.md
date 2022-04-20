There are some jobs/tasks that need to be run regularly on different schedules. Currently the Nautilus DevOps team is working on developing some scripts that will be executed on different schedules, but for the time being the team is creating some cron jobs in Kubernetes cluster with some dummy commands (which will be replaced by original scripts later). Create a cronjob as per details given below:

Create a cronjob named devops.

Set schedule to */12 * * * *.

Container name should be cron-devops.

Use nginx image with latest tag only and remember to mention the tag i.e nginx:latest.

Run a dummy command echo Welcome to xfusioncorp!.

Ensure restart policy is OnFailure.

Note: The kubectl utility on jump_host has been configured to work with the kubernetes cluster.

```
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: devops
spec:
  schedule: "*/12 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cron-devops
            image: nginx:latest
            args:
            - /bin/sh
            - -c
            - echo Welcome to xfusioncorp!
          restartPolicy: OnFailure
```