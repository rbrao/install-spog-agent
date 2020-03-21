# spog agent installer
## Installation procedure

## Linux/Ubuntu/CentOS
1. Download contents to a temporary location
2. `cd /tmp/location`   (Replace /tmp/location to actual temporary location)
3. `./install-spog-agent.sh install | uninstall | reinstall | update`  (Run `chmod a+x *.sh` if unable to execute)
	- reinstall will uninstall and perform a fresh install
	- update will refresh script files installation directory

### Current changelist
* Python2.7 validation/installation 
	yum -y install python2.7
* pip validation/installation
	pyhton -> python2.7 in env
	python get-pip.py
* python modules installation
	pip install pycurl (dependency system packages - libcurl-devel, libcurl4-openssl-devel)
	pip install mysql-python (dependency system pacakges - libmysqlclient-dev)
* Create installation directory, etc
	mkdir -p /spgwd/scripts
* Copy source script/s to installation directory
	cp spg_webstats.py /spgwd/scripts
* Update MySQL DB connection variables in spg_webstats.py
	SPGMYDB="web_metrics"
	SPGMYUSR="myuser"
	SPGMYKEY="myuser@123!"
	SPGMYHOST="DB Server IP"
	agent="ip address of this host"
* Test script
	python /spgwd/scripts/spg_webstats.py www.google.com
* On success of test, add cron entry
	*/5 * * * * /bin/python /spgwd/scripts/spg_webstats.py url1 url2 url3 ...

### Future changelist

## Windows

