#citi bike analysis
import requests
import time
import pandas as pd
from pandas.io.json import json_normalize
import matplotlib.pyplot as plt
import sqlite3 as lite
import time
from dateutil.parser import parse
import collections

r = requests.get('http://www.citibikenyc.com/stations/json')
df = json_normalize(r.json()['stationBeanList'])
con = lite.connect('citi_bike.db')
cur = con.cursor()
with con:
    cur.execute('DROP TABLE citibike_reference')
    cur.execute('CREATE TABLE citibike_reference (id INT PRIMARY KEY, totalDocks INT, city TEXT, altitude INT, stAddress2 TEXT, longitude NUMERIC, postalCode TEXT, testStation TEXT, stAddress1 TEXT, stationName TEXT, landMark TEXT, latitude NUMERIC, location TEXT )')
sql = "INSERT INTO citibike_reference (id, totalDocks, city, altitude, stAddress2, longitude, postalCode, testStation, stAddress1, stationName, landMark, latitude, location) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
with con:
     for station in r.json()['stationBeanList']:
         cur.execute(sql,(station['id'],station['totalDocks'],station['city'],station['altitude'],station['stAddress2'],station['longitude'],station['postalCode'],station['testStation'],station['stAddress1'],station['stationName'],station['landMark'],station['latitude'],station['location']))
station_ids = df['id'].tolist()
station_ids = ['_' + str(x) + ' INT' for x in station_ids]
with con:
     cur.execute('DROP TABLE available_bikes')
     cur.execute("CREATE TABLE available_bikes ( execution_time INT, " +  ", ".join(station_ids) + ");")
exec_time = parse(r.json()['executionTime'])
with con:
     cur.execute('INSERT INTO available_bikes (execution_time) VALUES (?)', (exec_time.strftime('%s'),))
id_bikes = collections.defaultdict(int)
for station in r.json()['stationBeanList']:
    id_bikes[station['id']] = station['availableBikes']
with con:
     for k, v in id_bikes.iteritems():
         cur.execute("UPDATE available_bikes SET _" + str(k) + " = " + str(v) + " WHERE execution_time = " + exec_time.strftime('%s') + ";")
#check
with con:
     cur.execute('SELECT * FROM available_bikes')
     data = cur.fetchall()
     data = pd.DataFrame(data)
     print(data[0])

for i in range(10):
    r = requests.get('http://www.citibikenyc.com/stations/json')
    exec_time = parse(r.json()['executionTime']).strftime("%s")

    cur.execute('INSERT INTO available_bikes (execution_time) VALUES (?)', (exec_time,))

    for station in r.json()['stationBeanList']:
        cur.execute("UPDATE available_bikes SET _%d = %d WHERE execution_time = %s" % (station['id'], station['availableBikes'], exec_time))
    con.commit()

    time.sleep(5)
    
df = pd.read_sql_query("SELECT * FROM available_bikes ORDER BY execution_time",con,index_col='execution_time')    
         
hour_change = collections.defaultdict(int)
for col in df.columns:
    station_vals = df[col].tolist()
    station_id = col[1:] #trim the "_"
    station_change = 0
    for k,v in enumerate(station_vals):
        if k < len(station_vals) - 1:
            station_change += abs(station_vals[k] - station_vals[k+1])
    hour_change[int(station_id)] = station_change
    
def keywithmaxval(d):
    #Find the key with the greatest value
    return max(d, key=lambda k: d[k])

max_station = keywithmaxval(hour_change)

cur.execute("SELECT id, stationname, latitude, longitude FROM citibike_reference WHERE id = ?", (max_station,))
data = cur.fetchone()
print("The most active station is station id %s at %s latitude: %s longitude: %s " % data)
print("With %d bicycles coming and going in the hour between %s and %s" % (
    hour_change[max_station],
    datetime.datetime.fromtimestamp(int(df.index[0])).strftime('%Y-%m-%dT%H:%M:%S'),
    datetime.datetime.fromtimestamp(int(df.index[-1])).strftime('%Y-%m-%dT%H:%M:%S'),
))

plt.bar(hour_change.keys(), hour_change.values())
plt.show()

