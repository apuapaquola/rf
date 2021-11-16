# Script to install the tree command for non-root users.
# To copy this script locally and type:
# $ sh install_tree_non_root.sh

cd $HOME
mkdir src
mkdir $HOME/.local/bin -p
export PATH=$PATH:~/.local/bin

cd src

# download latest tree source to home directory
VERSION=1.8.0

wget http://mama.indstate.edu/users/ice/tree/src/tree-$VERSION.tgz

# unpack
tar xzfv tree-$VERSION.tgz
cd tree-$VERSION/
make

# install to $HOME directory
make install prefix=$HOME/.local
# this will create folders bin, and man

cd $HOME

# remove original source folder
rm -rf tree-$VERSION