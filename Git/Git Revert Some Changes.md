The Nautilus application development team was working on a git repository /usr/src/kodekloudrepos/blog present on Storage server in Stratos DC. However, they reported an issue with the recent commits being pushed to this repo. They have asked the DevOps team to revert repo HEAD to last commit. Below are more details about the task:

In /usr/src/kodekloudrepos/blog git repository, revert the latest commit ( HEAD ) to the previous commit (JFYI the previous commit hash should be with initial commit message ).

Use revert blog message (please use all small letters for commit message) for the new revert commit.

```
ssh natasha@ststor01

sudo su

cd /usr/src/kodekloudrepos/blog

git status

git log

git revert HEAD

git add .

git commit -m "revert blog"

```