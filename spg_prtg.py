import requests
import json
import MySQLdb
import os
from datetime import datetime
import time
import socket
import logging
import logging.handlers
import sys
#import psycopg2
## DB CONFIG ##
SPGMYDB="web_metrics"
SPGMYUSR="myuser"
SPGMYKEY="myuser@123!"
SPGMYHOST="35.222.85.241"
## - ##

## PRTG CONFIG
baseurl="""http://34.93.237.184/api/"""
apiuser="spoguser"
apitoken="Spoguser1234"
## -- ##

## Device, Sensor - inclusion, exclusion list
excl_device_ids=[40,2049]
excl_sensor_ids=[]
incl_sensors={
"CPU Load":["Total"],
'XX':["XX"]
}

incl_regex_sensors={
"^Memory*":["Percent Available Memory"],
"^Disk*":["Free Space"]
}
## -- ##

def getDevices():
    try:
        spglogger.debug("getDevices:START")

        url="""%stable.json?content=devices&columns=device,objid&username=%s&password=%s"""%(baseurl,apiuser,apitoken)
        spglogger.debug("getDevices:URL:%s"%url)
        res = requests.get(url)
        res = json.loads(res.text)
        spglogger.debug("getDevices:URL_RES:%s"%res)
        q = """ truncate spg_prtg_devices"""
        cur.execute(q)
        device_idlist=[]
        for r in res["devices"]:
            objid=int(r["objid"])
            device_name=str(r["device"])
            spglogger.debug("getDevices:DEVICE_LIST:%s|%s"%(objid,device_name))
            if objid not in excl_device_ids:
                q=""" insert into spg_prtg_devices (id,device_name) values (%s,'%s') """%(objid,device_name)
                print q
                cur.execute(q)
                device_idlist.append(objid)
        spglogger.debug("getDevices:END")

        return device_idlist
        
    except Exception,e:
        spglogger.exception(e)
        return False

def getSensors():
    try:
        spglogger.debug("getSensors:START")
        q = """ truncate spg_prtg_device_sensors"""
        cur.execute(q)
        device_idlist=[]
        q="""select distinct id from spg_prtg_devices"""
        cur.execute(q)
        qd = cur.fetchall()
        for r1 in qd:
            device_id=r1[0]
            url="""%stable.json?content=sensors&id=%s&columns=sensor,objid&username=%s&password=%s"""%(baseurl,device_id,apiuser,apitoken)
            spglogger.debug("getSensors:URL:%s"%url)
            res = requests.get(url)
            res = json.loads(res.text)
            #spglogger.debug("getSensors:URL_RES:%s"%res)
            for r in res["sensors"]:
                objid=int(r["objid"])
                sensor_name=str(r["sensor"])
                spglogger.debug("getSensors:DEVICE_LIST:%s|%s|%s"%(device_id,objid,sensor_name))
                if objid not in excl_sensor_ids:
                    q=""" insert into spg_prtg_device_sensors (id,device_id,sensor_name) values (%s,%s,'%s') """%(objid,device_id,sensor_name)
                    print q
                    cur.execute(q)
        spglogger.debug("getSensors:END")
        return device_idlist
    except Exception,e:
        spglogger.exception(e)
        return False

def getSensorData():
    try:
        spglogger.debug("getSensorData:START")
        q="""select id,device_id,sensor_name from spg_prtg_device_sensors where sensor_name in %s or sensor_name regexp "%s" """%(str(tuple(incl_sensors.keys())),"|".join(incl_regex_sensors.keys()))
        print q
        cur.execute(q)
        qd = cur.fetchall()
        sdate=datetime.utcfromtimestamp(time.time()-1800).strftime("%Y-%m-%d %H:%M:%S")
        edate=datetime.utcfromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
        sdate=sdate.replace(" ","-").replace(":","-")
        edate=edate.replace(" ","-").replace(":","-")
        data={}
        csvfile="/tmp/prtgsensordata.csv"
        fh=open(csvfile,"w")
        for r1 in qd:
            sensor_id=r1[0]
            device_id=r1[1]
            sensor_name=r1[2]
            sensor_cols=incl_sensors.get(sensor_name,None)
            if sensor_cols is None:
                for k,v in incl_regex_sensors.items():
                    _k = k.replace("*","")
                    _k = _k.replace("^","")
                    if sensor_name.find(_k) ==0:
                        sensor_cols=v

            if sensor_cols is None:
                continue
            url="""%shistoricdata.json?&usecaption=1&id=%s&sdate=%s&edate=%s&username=%s&password=%s"""%(baseurl,sensor_id,sdate,edate,apiuser,apitoken)
            #url="""historicdata.json?id=2017&avg=300&sdate=2020-01-26-13-00-00&edate=2020-01-26-14-00-00&username=spoguser&password=Spoguser1234"""
            spglogger.debug("getSensorData:URL:%s"%url)
            res = requests.get(url)
            res = json.loads(res.text)
            #spglogger.debug("getSensorData:URL_RES:%s"%res)
            for r in res["histdata"]:
                date_time = str(r["datetime"]).split(" ")
                date_time=datetime.strptime(date_time[0]+" "+date_time[1],"%m/%d/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
                try:
                    val = r[sensor_cols[0]]
                except Exception,reskeyerr:
                    print "RESPONSE_KEY_ERR|%s|%s|%s"%(device_id,sensor_id,reskeyerr)
                    continue
                if not val or val == "":
                    continue
                fh.write("%s,%s,%s,%s\n"%(date_time,device_id,sensor_id,val))
                q="""INSERT IGNORE into spg_prtg_sensor_data (date_time,device_id,sensor_id,avg_val) values ('%s',%s,%s,%s)"""%(date_time,device_id,sensor_id,val)
                #print q
                cur.execute(q)
        #q="""LOAD DATA LOCAL INFILE '%s' into table spg_prtg_sensor_data fields terminated by ',' """%csvfile
        #print q
        #cur.execute(q)
        #fh.close()
        spglogger.debug("getSensorData:END")
    except Exception,e:
        spglogger.exception(e)
        return False

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
    dbconn = MySQLdb.connect(SPGMYHOST,SPGMYUSR,SPGMYKEY,SPGMYDB,autocommit=True )
    cur = dbconn.cursor()    
    for r in sys.argv[1:]:
        globals()[r]()

    dbconn.commit()
    dbconn.close()


## tables
"""
create table spg_prtg_devices(id int not null,device_name varchar(512) not null);
alter table spg_prtg_devices add index(device_name);
alter table spg_prtg_devices add index(id);

create table spg_prtg_device_sensors(id int not null,device_id int not null, sensor_name varchar(512) not null);
alter table spg_prtg_device_sensors add index(sensor_name);
alter table spg_prtg_device_sensors add index(id);
alter table spg_prtg_device_sensors add index(device_id);

create table spg_prtg_sensor_data(date_time datetime not null,device_id int not null,sensor_id int not null,avg_val float not null);
alter table spg_prtg_sensor_data add index(device_id);
alter table spg_prtg_sensor_data add index(sensor_id);
alter table spg_prtg_sensor_data add index(date_time);
alter table spg_prtg_sensor_data add unique(date_time,device_id,sensor_id);
"""
