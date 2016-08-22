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

#### To start a new analysis

###### Naive mode
```
rf create_node my_new_analysis
```

Check created files
```
find .
```

Run the driver
```
cd my_new_analysis
rf run . -v
```

Check the result
```
find .
```

###### Now with a purpose
```
rf create_node my_new_analysis
```

### Start from another

Clone the example
```
rf clone git@52.67.129.216:/opt/git/rf_example.git tests
```

Restart the git
```
cd tests/
rf init_repo . -ac
```


# To add a remote

```
https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes
https://git-annex.branchable.com/walkthrough/adding_a_remote/
```

...

