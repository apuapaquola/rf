#####################################################
#####################################################

# Tutorial 3: How to start

#####################################################
#####################################################

#### To view a sample of how to use RF

```
git clone git@server_ip_or_domain:/opt/git/rf_example.git
```

or 

```
rf clone git@server_ip_or_domain:/opt/git/rf_example.git
```

## To start a new analysis

#### Start from another repository or folder

Clone the example
```
rf clone git@52.67.129.216:/opt/git/rf_example.git tests
```

Restart the git
```
rf init_repo tests/ -ac
```

#### To start a new analysis

```
rf create_node my_new_analysis
```

Check created files
```
# This prints all files that are descendants of node directory, 
# skipping hidden files and directories
find my_new_analysis/ -not -path '*/\.*'
```

Run the driver
```
rf run my_new_analysis -v
```

Check the result
```
# This prints all files that are descendants of node directory, 
# skipping hidden files and directories
find my_new_analysis/ -not -path '*/\.*'
```

###### Now with a purpose

Create a new repository with a node
```
rf create_node --root_node my_new_analysis
```

Check created files
```
# This prints all files that are descendants of node directory, 
# skipping hidden files and directories
find my_new_analysis/ -not -path '*/\.*'
```

Edit the driver
```
vi my_new_analysis/_h/driver
```

Run the driver
```
rf run my_new_analysis -v
```

Check the result
```
# This prints all files that are descendants of node directory, 
# skipping hidden files and directories
find my_new_analysis/ -not -path '*/\.*'
```

Update the driver
```
vi my_new_analysis/_h/driver
```

Run again
```
rf run my_new_analysis -v
```

#### To add a remote

```
https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes
https://git-annex.branchable.com/walkthrough/adding_a_remote/
```