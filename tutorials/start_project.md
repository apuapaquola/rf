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
...