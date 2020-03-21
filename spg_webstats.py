import pycurl
from StringIO import StringIO
import sys
import threading
import time
import MySQLdb
import os
from datetime import datetime
import socket
import logging
import logging.handlers

class myThread (threading.Thread):
   def __init__(self, threadID, name, db_cur,counter=None):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
      self.db_cur =db_cur
   def run(self):
      #print "Starting " + self.name
      spgUrlMetrics(self.name,self.db_cur)
      #print "Exiting " + self.name

def spgUrlMetrics(url,db_cur):
    response_code =0
    dns_time =0
    app_time =0
    conn_time =0
    starttransfer_time =0
    total_time = 0
    redirect_count =0
    redirect_time =0
    redirect_url = ""
    speed_download =0
    size_download = 0
    effective_url = ""
    try:
        buffer = StringIO()
	hdr = StringIO()
        c = pycurl.Curl()
        c.setopt(c.URL,url)
        c.setopt(c.WRITEFUNCTION, buffer.write)
        c.setopt(pycurl.SSL_VERIFYPEER, False)
	c.setopt(pycurl.HEADERFUNCTION, hdr.write)
	c.setopt(pycurl.TIMEOUT,30)
	c.setopt(pycurl.USERAGENT,'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36')
        c.perform()
	#print "ERRRRRROR:%s"%(c.errstr())
        response_code = c.getinfo(pycurl.RESPONSE_CODE) #DNS time
        dns_time = c.getinfo(pycurl.NAMELOOKUP_TIME) #DNS time
        app_time = c.getinfo(pycurl.APPCONNECT_TIME) #DNS r
        conn_time = c.getinfo(pycurl.CONNECT_TIME)   #TCP/IP 3-way handshaking time
        starttransfer_time = c.getinfo(pycurl.STARTTRANSFER_TIME)  #time-to-first-byte time
        total_time = c.getinfo(pycurl.TOTAL_TIME)  #last equst time
        redirect_count = c.getinfo(pycurl.REDIRECT_COUNT)
        redirect_time = c.getinfo(pycurl.REDIRECT_TIME) 
        redirect_url = c.getinfo(pycurl.REDIRECT_URL)
        speed_download = c.getinfo(pycurl.SPEED_DOWNLOAD) 
        size_download = c.getinfo(pycurl.SIZE_DOWNLOAD) 
        effective_url = c.getinfo(pycurl.EFFECTIVE_URL) 
        error=""
	if response_code >= 400:
		error=hdr.getvalue().splitlines()[0]
        if redirect_url is None or redirect_url == "None":
            redirect_url = ""
        if effective_url is None or effective_url == "None":
            effective_url = ""
        c.close()
        spglogger.debug("%s|processed|%s"%(url,response_code))
    except Exception,e:
        #print "ERROR:%s"%str(e)
        error = str(e)
        error=error.replace(","," ")
        error=error.replace("'"," ")
        spglogger.error("%s|%s"%(url,error))
    q = """ insert into spg_url_metrics (agent,url,tstamp_gmt,date_gmt,error,response_code, dns_time, app_time, connect_time, starttransfer_time, total_time,redirect_count,redirect_time,redirect_url,speed_download,size_download,effective_url) values ('%s','%s',%s,'%s','%s',%s,%s,%s,%s,%s,%s,%s,%s,'%s',%s,%s,'%s')"""%(agent,url,tstamp_gmt,date_gmt,error,response_code, dns_time, app_time, conn_time, starttransfer_time, total_time,redirect_count,redirect_time,redirect_url,speed_download,size_download,effective_url)
    lines.append(q)

if __name__ == "__main__":
    scriptname=sys.argv[0]
    LOG_LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}
    LOG_FILENAME = scriptname.replace(".py",".log")
    LOG_FILENAME = LOG_FILENAME.split("/")[-1]
    LOG_FILENAME = "/spgwd/scripts/logs/%s"%LOG_FILENAME
    # Set up a specific logger with our desired output level
    spglogger=logging.basicConfig(format="%(asctime)s:%(levelname)s:%(message)s",level=logging.DEBUG)
    spglogger = logging.getLogger('SPGLOGGER')


    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=(10*1024*1024), backupCount=5)
    spglogger.addHandler(handler)
    if len(sys.argv) <= 1:
        print "ERROR: input argument (URL) required, USAGE: %s.py <URL>"%scriptname
        sys.exit(1)

    lines=[] 
    tstamp_gmt= int(time.time())
    date_gmt=datetime.utcfromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
    SPGMYDB="web_metrics"
    SPGMYUSR="myuser"
    SPGMYKEY="myuser@123!"
    SPGMYHOST="localhost"
    agent="localhost"
    dbconn = MySQLdb.connect(SPGMYHOST,SPGMYUSR,SPGMYKEY,SPGMYDB )
    cur = dbconn.cursor()
    threads=[]

    for i in range(len(sys.argv) - 1):
        url = sys.argv[i+1]
        try:
            th =  myThread(i,url,cur)
            threads.append(th)
            th.start()
        except Exception,e:
            error_msg="%s|%s|%s"%("ERROR",e,url)
            spglogger.error(error_msg)
            print error_msg
    #print threads
    for each_thread in threads:
        each_thread.join()

    for q in lines:
        cur.execute(q)
    dbconn.commit()
    dbconn.close()

# create table spg_agents( id int primary key auto_increment, displayname  varchar(255) not null, ipaddress varchar(16) not null unique, hostname varchar(255), city varchar(255) not null, state varchar(255) not null, country varchar(255) not null, isactive bool);
# create table spg_target_info( id int primary key auto_increment,target_type varchar(255) not null, target varchar(1024) not null, displayname varchar(1024) not null);
# create table  spg_url_metrics(agent varchar(128),url varchar(512), error varchar(2054), tstamp_gmt double, date_gmt datetime, response_code int, dns_time double, app_time double, connect_time double, starttransfer_time double, total_time double, redirect_count double,redirect_time double,redirect_url varchar(1024),speed_download double,size_download double,effective_url varchar(1024));
# alter table spg_url_metrics add unique(agent,url,tstamp_gmt);


