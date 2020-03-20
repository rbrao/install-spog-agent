#!/bin/bash
#Autho: SPOGWorks
#Version: 2020.03.18_01

user=`whoami`
option=$1

install() {
	yum -y install libcurl
	yum -y install openssl
	yum -y install mariadb
	yum -y install mariadb-devel
	yum -y install mariadb-libs
	yum -y install python2
	yum -y install python-devel
	/bin/python get-pip.py
	/bin/pip install pycurl
	/bin/pip install MySQL-python
}

if [ "$user" = "root" ] && [ "$option" != "" ]; then
        case $option in
                install )
                        install ;;
                uninstall )
                        uninstall ;;
                update )
                        update ;;
                reinstall )
                        reinstall ;;
        esac
else
        echo "Please execute as root with appropriate parameters
        USAGE: $0 install|uninstall|reinstall|update"
fi
