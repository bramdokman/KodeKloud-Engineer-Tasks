Nautilus developers are actively working on one of the project repositories, /usr/src/kodekloudrepos/official. They recently decided to implement some new features in the application, and they want to maintain those new changes in a separate branch. Below are the requirements that have been shared with the DevOps team:

On Storage server in Stratos DC create a new branch xfusioncorp_official from master branch in /usr/src/kodekloudrepos/official git repo.

Please do not try to make any changes in code

Solution:

```

ssh natasha@stapp03

git checkout master

git checkout -b xfusioncorp_official

git branch -all

```