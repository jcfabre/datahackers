import json
import requests
from datetime import datetime
from pytz import timezone
import re
import MySQLdb
from mysql.connector import Error
import time

records_inserted = 0
existing_records = 0  #not inserted
stations_inserted = 0
existing_stations = 0

url = """http://opendata.paris.fr/api/records/1.0/search/?dataset=stations-velib-disponibilites-en-temps-reel&rows=2000&facet=banking&facet=bonus&facet=status&facet=contract_name&pretty_print=true"""

def create_json(url):
    '''Gets an url an creates a JSON doc out of it'''

    response = requests.get(url)
    doc = response.text
    parsed_json = json.loads(doc)

    return parsed_json

def parse_json(doc):
    ''' Yields a list for every record of the parsed JSON document'''
    paristime = timezone('Europe/Paris')
    utctime = timezone('UTC')
    format = "%Y-%m-%d %H:%M:%S %Z%z"

    for e1 in doc["records"]:

        # Record
        recordid = e1["recordid"]
        insert_date = datetime.now(paristime).strftime(format)
        last_update = e1["fields"]["last_update"]
        re_date = re.search(r'\d{4}-\d{2}-\d{2}', last_update).group()
        re_hour = re.search(r'\d{2}:\d{2}:\d{2}', last_update).group()
        last_update = utctime.localize(datetime.strptime(re_date +' '+ re_hour,"%Y-%m-%d %H:%M:%S" )).astimezone(paristime).strftime(format)
        available_bike_stands = int(e1["fields"]["available_bike_stands"])
        available_bikes = int(e1["fields"]["available_bikes"])

        # Station
        status = str(e1["fields"]["status"])
        name = e1["fields"]["name"].encode('utf8','replace')
        bonus = bool(e1["fields"]["bonus"])
        banking = bool(e1["fields"]["banking"])
        bike_stands = int(e1["fields"]["bike_stands"])
        number = e1["fields"]["number"]
        address = e1["fields"]["address"].encode('utf8','replace')
        latitude = e1["fields"]["position"][0]
        longitude= e1["fields"]["position"][1]

        # Station: if name not exists then create station_id otherwise nothing
        try:
            cursor.execute("select distinct station_id from velib.station where station.name = %s", (name,))
            data = cursor.fetchall()
            station_id = int(data[0][0])

        except Exception,e:
            station_id = None
            #print str(e)

        yield [recordid, insert_date, last_update, available_bike_stands, available_bikes, station_id, status, name, bonus,
                  banking, bike_stands, number, address, latitude, longitude]

def stations_in_db():
    db = MySQLdb.connect(host = "HOST",port = "PORT", db='DBNAME',user='USERNAME',passwd='PASSWORD')
    cursor = db.cursor()
    query = """select distinct station_id from velib.station"""

    try:
        cursor.execute(query)
        data = cursor.fetchall()
        station_id_list = list()
        for elt in data:
            station_id_list.append(elt[0])
        return station_id_list

    except Exception,e:
        print str(e)

    finally:
        cursor.close()
        db.commit()
        db.close()

def latest_records_in_db():
    db = MySQLdb.connect(host = "HOST",port = "PORT", db='DBNAME',user='USERNAME',passwd='PASSWORD')
    cursor = db.cursor()
    query = '''select max(r2.last_update) as last_update, r2.station_id
from velib.record as r1 join velib.record as r2
on r1.station_id = r2.station_id
group by r2.station_id
order by last_update desc;'''
    try:
        cursor.execute(query)
        data = cursor.fetchall()
        x = list()
        for elt in data:
            x.append(elt)
        return x

    except Exception,e:
        print str(e)

    finally:
        cursor.close()
        db.commit()
        db.close()

def is_station_in_db(lst):
    return lst[0] in station_id_list

def is_latest_record(record):
    return not (record[2],record[5]) in latest_records_list

def record_has_station_id(record):
    return record[-1:][0] != None

def insert_into_station(lst):
    query = '''insert into velib.station (status, name, bonus,
                  banking, bike_stands, number, address, latitude, longitude) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
    try:
        cursor.execute(query,lst)
        if cursor.lastrowid:
            global stations_inserted
            stations_inserted += 1
        db.commit()

    except Error, error:
        db.rollback()
        print error

def insert_into_record(lst):
    query = '''insert into velib.record (recordid, insert_date, last_update, available_bike_stands, available_bike,
                    station_id) values (%s,%s,%s,%s,%s,%s)'''
    try:
        cursor.execute(query,lst)
        if cursor.lastrowid:
            global records_inserted
            records_inserted += 1
            db.commit()

    except Error, error:
        db.rollback()
        print error

def main():
    start = time.time()
    parsed_doc = parse_json(create_json(url))

    while True:
        try:
            entry = parsed_doc.next()
            record = entry[0:6]
            station = entry[5:]

            if is_station_in_db(station):
                global existing_stations
                existing_stations += 1
            else:
                insert_into_station(station[1:])

            if is_latest_record(record) and record_has_station_id(record):
                insert_into_record(record)
            else:
                global existing_records
                existing_records += 1

        except Exception,e:
            print str(e)
            break


    end = time.time()
    diff = end-start

    print "Hello @ {0}".format(datetime.now())
    print "records_inserted: {0}".format(records_inserted)
    print "existing_records: {0}".format(existing_records)
    print "stations_inserted: {0}".format(stations_inserted)
    print "existing_stations: {0}".format(existing_stations)
    print "Done in {0} seconds".format(diff)


if __name__ == "__main__":
    station_id_list = stations_in_db()
    latest_records_list = latest_records_in_db()
    db = MySQLdb.connect(host = "HOST",port = "PORT", db='DBNAME',user='USERNAME',passwd='PASSWORD')
    cursor = db.cursor()
    main()
    cursor.close()
    db.close()