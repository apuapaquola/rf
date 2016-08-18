#####################################################
#####################################################
```
 _____  ______             
|  __ \|  ____|      /\    
| |__) | |__ (_)    /  \   
|  _  /|  __|      / /\ \  
| | \ \| |    _   / ____ \ 
|_|  \_\_|   (_) /_/    \_\
                           
                           
  __                                             _       __           
 / _|                                           | |     / _|          
| |_ _ __ __ _ _ __ ___   _____      _____  _ __| | __ | |_ ___  _ __ 
|  _| '__/ _` | '_ ` _ \ / _ \ \ /\ / / _ \| '__| |/ / |  _/ _ \| '__|
| | | | | (_| | | | | | |  __/\ V  V / (_) | |  |   <  | || (_) | |   
|_| |_|  \__,_|_| |_| |_|\___| \_/\_/ \___/|_|  |_|\_\ |_| \___/|_|   
                                                                      
                                                                      
           _ _       _                     _   _           
          | | |     | |                   | | (_)          
  ___ ___ | | | __ _| |__   ___  _ __ __ _| |_ ___   _____ 
 / __/ _ \| | |/ _` | '_ \ / _ \| '__/ _` | __| \ \ / / _ \
| (_| (_) | | | (_| | |_) | (_) | | | (_| | |_| |\ V /  __/
 \___\___/|_|_|\__,_|_.__/ \___/|_|  \__,_|\__|_| \_/ \___|
                                                           
                                                           
                                 _        _   _                   _ 
                                | |      | | (_)                 | |
  ___ ___  _ __ ___  _ __  _   _| |_ __ _| |_ _  ___  _ __   __ _| |
 / __/ _ \| '_ ` _ \| '_ \| | | | __/ _` | __| |/ _ \| '_ \ / _` | |
| (_| (_) | | | | | | |_) | |_| | || (_| | |_| | (_) | | | | (_| | |
 \___\___/|_| |_| |_| .__/ \__,_|\__\__,_|\__|_|\___/|_| |_|\__,_|_|
                    | |                                             
                    |_|                                             
                                   _     
                                  | |    
 _ __ ___  ___  ___  __ _ _ __ ___| |__  
| '__/ _ \/ __|/ _ \/ _` | '__/ __| '_ \ 
| | |  __/\__ \  __/ (_| | | | (__| | | |
|_|  \___||___/\___|\__,_|_|  \___|_| |_|

```
#########################################################
#########################################################

# Tutorial 1: Build your own repositories server

#########################################################
#########################################################
###### GIT ANNEX ON SERVER

Sources:
https://git-scm.com/book/it/v2/Git-on-the-Server-Setting-Up-the-Server
https://git-annex.branchable.com/tips/centralized_git_repository_tutorial/on_your_own_server/

###########################
## On server

*You will need administrative privileges for this part*
```
sudo apt-get updade; sudo apt-get upgrade -y
```

### Configure GIT Server
*You will need administrative privileges for this part*

```
# create a new user called git
sudo adduser git
# create the directory to host the repositories
sudo mkdir /opt/git
sudo chown git:git /opt/git
```

_Now with the new user **git**_
```
# change for user git
su git
cd ~
# prepare to set your keys
mkdir .ssh && chmod 700 .ssh
touch .ssh/authorized_keys && chmod 600 .ssh/authorized_keys
```

### Install git annex
*You will need administrative privileges for this part*
```
sudo apt-get install git git-annex
```

## Testing
### Create a new repository
```
cd /opt/git
# Create a new repo called rf_annex
git init rf_annex.git --bare --shared
```

### To add a collaborator

##### Get the id_rsa.pub on host

```
cat ~/.ssh/id_rsa.pub > id_rsa.user.pub
```

##### After upload the id_rsa.user.pub
```
su git
cat id_rsa.user.pub >> ~/.ssh/authorized_keys
```
#####################################################
#####################################################
## GIT ANNEX ON HOSTS

#####################################################
### On host collaborator A:

##### Clone repository
```
# replace server_ip_or_domain with your server address
git clone git@server_ip_or_domain:/opt/git/rf_annex.git
cd rf_annex/
```

##### First commit
```
# inside the repo
touch 'test' > test_file
mkdir bigfiles
git add .
git commit -m 'initial commit'
```

##### Push
```
git push origin master
```

##### Big file commit
```
git-annex init
# copy hg19.fa from another place or simply `touch bigfiles/hg19.fa`
git annex add bigfiles/hg19.fa
git commit -m "added a bigfile"
```

##### Push and sync
```
# No upload big files
git push origin master git-annex
# Now upload big files 
git annex sync --content
```

#####################################################
### On host collaborator B:


##### Clone repository
```
# replace server_ip_or_domain with your server address
git clone git@server_ip_or_domain:/opt/git/rf_annex.git
# let's check
cd rf_annex/
ls bigfiles/
# check content
head bigfiles/hg19.fa 
```

##### Sync repository
```
git annex sync --content
# or to get specific file
git annex get bigfiles/hg19.fa
# let's check again
ls bigfiles/
# check content
head bigfiles/hg19.fa
```
#####################################################
#####################################################
