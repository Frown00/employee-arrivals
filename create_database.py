from pymongo import MongoClient
import config
import datetime

def connect():
  client = MongoClient(config.MONGO_URL)
  return client[config.MONGO_DB]

def deleteDB():
  client = MongoClient(config.MONGO_URL)
  client.drop_database(config.MONGO_DB)

deleteDB()
db = connect()
db.employees.insert_many([
  {
    "employee_id": '1',
    "first_name": "John",
    "last_name": "Locke",
    "present": True,
    "rfid": "RF1324204400",
  },
  {
    "employee_id": '2',
    "first_name": "Kate",
    "last_name": "Richards",
    "present": False,
    "rfid": "RF1324204423",
  },
  {
    "employee_id": '3',
    "first_name": "Mary",
    "last_name": "Jones",
    "present": False,
    "rfid": "RF1324204433",
  },
  {
    "employee_id": '4',
    "first_name": "Radosław",
    "last_name": "Tymosiuk",
    "present": False,
    "rfid": None,
  },
  {
    "employee_id": '5',
    "first_name": "Adam",
    "last_name": "Bower",
    "present": False,
    "rfid": "RF1324204411",
  },
])

db.rfid_cards.insert_many([
  {
    "id": "RF1324204400",
    "isUsed": True,
    "owner": '1'
  },
  {
    "id": "RF1324204423",
    "isUsed": True,
    "owner": '2'
  },
  {
    "id": "RF1324204433",
    "isUsed": True,
    "owner": '3'
  },
  {
    "id": "RF1324204411",
    "isUsed": True,
    "owner": '5'
  }
])

db.arrivals.insert_one({
  "employee_id": "1",
  "arrival_time": datetime.datetime.now(),
  "leaving_time": None,
})

db.terminals.insert_many([
  {
    "id": '111',
    "label": "Terminal nr 1" 
  },
  {
    "id": '222',
    "label": "Terminal nr 2" 
  },
  {
    "id": '333',
    "label": "Terminal nr 3" 
  }
])