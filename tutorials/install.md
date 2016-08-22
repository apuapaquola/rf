#####################################################
#####################################################

# Tutorial 2: SETUP RF

#####################################################
#####################################################

### Install git and git-annex
*You will need administrative privileges for this part*
```
sudo apt-get install git git-annex
```

### Set your python env or simply use sudo to install RF

#### Install with pip
pip install git+git://github.com/apuapaquola/rf.git

#### Or download and install manually
python rf/setup.py install

#### Or locally with pip
pip install --install-option="--prefix=$PREFIX_PATH" rf

## IMPORTANT

RF has some problems with older versions of Make
If you have an older version, please upgrade

To check make version:

```
make --version
```

To upgrade:

```
cd /tmp
wget http://ftp.gnu.org/gnu/make/make-4.2.tar.gz
tar xvf make-4.2.tar.gz
cd make-4.2
./configure
make
sudo make install
rm -rI make-4.2.tar.gz make-4.2
```

You can just download and execute our update_make.sh

```
bash <(curl -s https://raw.githubusercontent.com/apuapaquola/rf/master/scripts/update_make.sh)
```
