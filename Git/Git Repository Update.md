The Nautilus development team started with new project development. They have created different Git repositories to manage respective project's source code. One of the repo /opt/cluster.git was created recently. The team has given us a sample index.html file that is currently present on jump host under /tmp. The repository has been cloned at /usr/src/kodekloudrepos on storage server in Stratos DC.

Copy sample index.html file from jump host to storage server under cloned repository at /usr/src/kodekloudrepos, add/commit the file and push to master branch.

```
scp /tmp/index.html natasha@ststor01:/

ssh natasha@ststor01

sudo su

mv index.html /usr/src/kodekloudrepos/cluster

git status 

git add .

git commit -m "added index.html"

git push

```