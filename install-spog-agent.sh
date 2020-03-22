#!/bin/bash
#Autho: SPOGWorks
#Version: 2020.03.18_03

user=`whoami`
option=$1

pkginstall() {
	yum -y install libcurl
	yum -y install openssl
	yum -y install mariadb
	yum -y install mariadb-devel
	yum -y install mariadb-libs
	yum -y install python2
	yum -y install python-devel
}

pymodules() {
	/bin/python get-pip.py
	/bin/pip install pycurl
	/bin/pip install MySQL-python
}

installdir() {
	mkdir -p /spgwd/scripts/logs
}

userinputs() {
	read -p "*** Edit install config file with appropriate values. Press any key to continue [Ctrl+C to abort] " dummy
	vi ./install.conf
}

readinputs() {
	DBNAME=`grep '^DBNAME=' ./install.conf|awk -F= '{print $2}'`
	DBUSER=`grep '^DBUSER=' ./install.conf|awk -F= '{print $2}'`
	DBPASS=`grep '^DBPASS=' ./install.conf|awk -F= '{print $2}'`
	DBHOST=`grep '^DBHOST=' ./install.conf|awk -F= '{print $2}'`
	AGENT=`grep '^AGENT=' ./install.conf|awk -F= '{print $2}'`
	PRTGURL=`grep '^PRTGURL=' ./install.conf|awk -F= '{print $2}'|sed 's#/#\\\/#g'`
	PRTGUSER=`grep '^PRTGUSER=' ./install.conf|awk -F= '{print $2}'`
	PRTGPASS=`grep '^PRTGPASS=' ./install.conf|awk -F= '{print $2}'`
	echo "$DBNAME | $DBUSER | $DBPASS | $DBHOST | $AGENT | $PRTGURL | $PRTGUSER | $PRTGPASS"
}

unpack() {
	cp ./spg_webstats.py /spgwd/scripts/
	cp ./spg_prtg.py /spgwd/scripts/
	## update webstats script ##
	sed -i "s/SPGMYDB=\"[a-z,A-Z,0-9,.,_,-,@,!]*\"/SPGMYDB=$DBNAME/g" /spgwd/scripts/spg_webstats.py
	sed -i "s/SPGMYUSR=\"[a-z,A-Z,0-9,.,_,-,@,!]*\"/SPGMYUSR=$DBUSER/g" /spgwd/scripts/spg_webstats.py
	sed -i "s/SPGMYKEY=\"[a-z,A-Z,0-9,.,_,-,@,!]*\"/SPGMYKEY=$DBPASS/g" /spgwd/scripts/spg_webstats.py
	sed -i "s/SPGMYHOST=\"[a-z,A-Z,0-9,.,_,-,@,!]*\"/SPGMYHOST=$DBHOST/g" /spgwd/scripts/spg_webstats.py
	sed -i "s/agent=\"[a-z,A-Z,0-9,.,_,-,@,!]*\"/agent=$AGENT/g" /spgwd/scripts/spg_webstats.py
	## update prtg script ##
	sed -i "s/SPGMYDB=\"[a-z,A-Z,0-9,.,_,-,@,!]*\"/SPGMYDB=$DBNAME/g" /spgwd/scripts/spg_prtg.py
	sed -i "s/SPGMYUSR=\"[a-z,A-Z,0-9,.,_,-,@,!]*\"/SPGMYUSR=$DBUSER/g" /spgwd/scripts/spg_prtg.py
	sed -i "s/SPGMYKEY=\"[a-z,A-Z,0-9,.,_,-,@,!]*\"/SPGMYKEY=$DBPASS/g" /spgwd/scripts/spg_prtg.py
	sed -i "s/SPGMYHOST=\"[a-z,A-Z,0-9,.,_,-,@,!]*\"/SPGMYHOST=$DBHOST/g" /spgwd/scripts/spg_prtg.py
	sed -i "s/apiuser=\"[a-z,A-Z,0-9,.,_,-,@,!]*\"/apiuser=$PRTGUSER/g" /spgwd/scripts/spg_prtg.py
	sed -i "s/apitoken=\"[a-z,A-Z,0-9,.,_,-,@,!]*\"/apitoken=$PRTGPASS/g" /spgwd/scripts/spg_prtg.py
	sed -i.bak "s/baseurl=\"\"\"[a-z,A-Z,0-9,.,_,-,@,!,:,/]*\"\"\"/baseurl=\"\"$PRTGURL\"\"/g" /spgwd/scripts/spg_prtg.py
}

remove() {
	rm -rf /spgwd
}

cronentry() {
	echo "*/5 * * * * /bin/python /spgwd/scripts/spg_webstats.py url1 url2"
	read -p "*** Copy/Paste the above line into crontab. Edit url1 url2 to appropriate values. Press any key to continue [Ctrl+C to abort] " dummy
	crontab -e
        echo "*** End of Installation ***"
}

test() {
	userinputs
	readinputs
	rpm -qa |egrep 'libcurl|openssl|mariadb|python2|python-devel'
	pip list|egrep 'pycurl|MySQL-python'
	/bin/python /spgwd/scripts/spg_webstats.py
}

install() {
	pkginstall
	pymodules
	userinputs
	readinputs
	installdir
	unpack
	cronentry
}

update() {
	userinputs
	readinputs
	unpack
}

uninstall() {
	remove
}

reinstall() {
	uninstall
	install
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
		test )
			test ;;
        esac
else
        echo "Please execute as root with appropriate parameters
        USAGE: $0 install|uninstall|reinstall|update"
fi
