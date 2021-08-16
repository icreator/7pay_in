#!/bin/bash
echo "This script will:
1) install all modules need to run web2py on Ubuntu 14.04
2) install web2py in /home/www-data/
3) create a self signed ssl certificate
4) setup web2py with mod_wsgi

You may want to read this script before running it.

Press a key to continue...[ctrl+C to abort]"

read CONFIRM


# optional
# dpkg-reconfigure console-setup
# dpkg-reconfigure timezoneconf
# nano /etc/hostname
# nano /etc/network/interfaces
# nano /etc/resolv.conf
# reboot now
# ifconfig eth0

echo "installing useful packages"
echo "=========================="
apt-get update
apt-get -y install ssh
apt-get -y install zip unzip
apt-get -y install tar
apt-get -y install openssh-server
apt-get -y install build-essential
apt-get -y install python3
apt-get -y install ipython3
apt-get -y install python3-dev
apt-get -y install python3-psycopg2
apt-get -y install postfix
apt-get -y install wget
apt-get -y install python3-matplotlib
apt-get -y install python3-reportlab
apt-get -y install mercurial

# optional, uncomment for emacs
# apt-get -y install emacs

# optional, uncomment for backups using samba
# apt-get -y install samba
# apt-get -y install smbfs

echo "downloading, installing and starting web2py"
echo "==========================================="
cd /home
mkdir www-data
cd www-data
rm web2py_src.zip*
wget http://web2py.com/examples/static/web2py_src.zip
unzip web2py_src.zip
mv web2py/handlers/wsgihandler.py web2py/wsgihandler.py
chown -R www-data:www-data web2py

# echo "setting up PAM"
# echo "================"
# sudo apt-get install pwauth
# sudo ln -s /etc/apache2/mods-available/authnz_external.load /etc/apache2/mods-enabled
# ln -s /etc/pam.d/apache2 /etc/pam.d/httpd
# usermod -a -G shadow www-data

cd /home/www-data/web2py
sudo -u www-data python -c "from gluon.widget import console; console();"
sudo -u www-data python -c "from gluon.main import save_password; save_password(raw_input('admin password: '),443)"
echo "done!"