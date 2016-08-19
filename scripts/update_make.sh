cd /tmp
wget http://ftp.gnu.org/gnu/make/make-4.2.tar.gz
tar xvf make-4.2.tar.gz
cd make-4.2
./configure
make
sudo make install
rm -rI make-4.2.tar.gz make-4.2
