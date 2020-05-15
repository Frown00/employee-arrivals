from pymongo import MongoClient
import paho.mqtt.client as mqtt
import json
import config
from pprint import pprint
import datetime

def connect():
  client = MongoClient(config.MONGO_URL)
  return client[config.MONGO_DB]

db = connect()
broker = config.BROKER_ADDRESS
port = config.BROKER_PORT
client = mqtt.Client()

def onConnect(client, userdata, flags, rc):
  print('Connected to mqtt')
  client.subscribe(config.VERIFY_EMPLOYEE_TOPIC)
  client.subscribe(config.VERIFY_TERMINAL_TOPIC)

def sendVerificationMsg(employee):
  send_msg = {}
  if(employee):
    verifiedUserName = employee['first_name'] + " " + employee['last_name']
    present = employee['present']
    send_msg = {
      'is_verified': True,
      'is_present': not present,
      'content': verifiedUserName
    }
  else:
    send_msg = {
      'is_verified': False,
      'content': 'Wrong RFID!'
    }
  client.publish(config.MESSAGE_TOPIC, payload=json.dumps(send_msg), qos=2, retain=False)

def sendTerminalVerification(terminal):
  send_msg = {}
  if(terminal):
    label = terminal['label']
    send_msg = {
      'is_verified': True,
      'terminalId': terminal['id'],
      'terminalLabel': terminal['label'],
      'content': "Connected to terminal"
    }
  else:
    send_msg = {
      'is_verified': False,
      'content': "Terminal don't exist!"
    }
  client.publish(config.TERMINAL_TOPIC, payload=json.dumps(send_msg), qos=2, retain=False)

def leaving(employee):
  db.arrivals.update_one(
    {"employee_id": employee["employee_id"], "leaving_time": None},
    {"$set": {"leaving_time": datetime.datetime.now()}}
  )
  db.employees.update_one(
    {"employee_id": employee["employee_id"]},
    {"$set": {"present": False}}
  )
def arriving(employee):
  db.arrivals.insert_one(
    {
      "employee_id": employee["employee_id"],
      "arrival_time": datetime.datetime.now(),
      "leaving_time": None,
    }
  )
  db.employees.update_one(
    {"employee_id": employee["employee_id"]},
    {"$set": {"present": True}}
  )

def setArrival(employee):
  if(employee["present"] == True):
    leaving(employee)
  if(employee["present"] == False):
    arriving(employee)

def logMessage(topic, payload, result):
  if(topic == config.VERIFY_EMPLOYEE_TOPIC):
    db.logs.insert_one({
      "topic": topic,
      "terminal": payload["terminalLabel"],
      "rfid": payload["rfid"],
      "sucess": result,
      "created_date": datetime.datetime.now()
    })

def onMessage(client, userdata, msg):
  print(msg.topic+" "+msg.payload.decode())
  successVerification = False
  if(str(msg.topic) == config.VERIFY_EMPLOYEE_TOPIC):
    payload = json.loads(msg.payload.decode())
    verifiedEmployee = verifyEmployee(payload["rfid"])
    if(verifiedEmployee):
      setArrival(verifiedEmployee)
      successVerification = True
    sendVerificationMsg(verifiedEmployee)
  if(str(msg.topic) == config.VERIFY_TERMINAL_TOPIC):
    terminal = verifyTerminal(msg.payload.decode())
    sendTerminalVerification(terminal)
  logMessage(str(msg.topic), json.loads(msg.payload.decode()), successVerification)


client.on_connect = onConnect
client.on_message = onMessage
client.connect(broker, port)

def addTerminalRFID(id, label):
  db.terminals.insert_one({
    "id": id,
    "label": label
  })

def removeTerminalRFID(id):
  db.terminals.delete_one({"id": id})

def assignRFIDToEmployee(employee, rfid):
  rfidCard = db.rfid_cards.find_one({'id': rfid})
  if(rfidCard):        
    if(rfidCard['isUsed'] == True):
      print('Trying to assign used card!')
      return
  removeEmployeeRFID(employee)
  if(rfidCard):
    db.rfid_cards.update_one(
      {'id': rfidCard['id']}, 
      {'$set': {'isUsed': True, 'owner': employee['employee_id']}}
    )
    db.employees.update_one(
      {'employee_id': employee['employee_id']}, 
      {'$set': {'rfid': rfid}}
    )
  else:
    db.rfid_cards.insert_one({
      'id': rfid, 
      'isUsed': True, 
      'owner': employee['employee_id']
    })
    db.employees.update_one(
      {'employee_id': employee['employee_id']}, 
      {'$set': {'rfid': rfid}}
    )

def removeEmployeeRFID(employee):
  if(employee['rfid']):
    lastUsed =  db.rfid_cards.find_one({'id': employee['rfid']})
    db.rfid_cards.update_one(
      {'id': lastUsed['id']}, 
      {'$set': {'isUsed': False, 'owner': None}}
    )
    db.employees.update_one(
      {'employee_id': employee['employee_id']}, 
      {'$set': {'rfid': None}}
    )

def verifyEmployee(rfid):
  employee = db.employees.find_one({'rfid': rfid})
  if(employee == None):
    return False
  return employee

def verifyTerminal(id):
  terminal = db.terminals.find_one({'id': id})
  if(terminal == None):
    return False
  return terminal

def displayLogs():
  logs = db.logs.find({})
  for log in logs:
    resultMsg = "SUCCESS" if log["sucess"] == True else "FORBIDDEN"
    print(f'{resultMsg} | {log["created_date"]} | {log["rfid"]} | {log["terminal"]} | {log["topic"]} ')

def menu():
  print("1. Add new RFID terminal")
  print("2. Remove RFID terminal")
  print("3. Asign RFID card to employee")
  print("4. Remove RFID employee's card")
  print("5. Return to log.")

def displayEmployees():
  employees = db.employees.find({})
  print('All employees')
  for e in employees:
    print(f'id:\t\t{e["employee_id"]}')
    print(f'first name:\t{e["first_name"]}')
    print(f'last name:\t{e["last_name"]}')
    print(f'rfid:\t\t{e["rfid"]}')
    print()

def displayTerminals():
  terminals = db.terminals.find({})
  print('All terminals')
  for t in terminals:
    print(f'id:\t\t{t["id"]}')
    print(f'label:\t{t["label"]}')
    print()

def wrongOption():
  print("There is no given option.")

def callAddTerminal():
  try:
    id = input('Enter id for new terminal: ')
    label = input('Enter label: ')
    addTerminalRFID(id, label)
  except KeyboardInterrupt:
    return

def callRemoveTerminal():
  try:
    displayTerminals()
    id = input('Enter terminal id: ')
    removeTerminalRFID(id)
  except KeyboardInterrupt:
    return


def callAssignRFID():
  try:
    displayEmployees()
    employeeId = input('Enter employee id: ')
    employee = db.employees.find_one({'employee_id': employeeId})
    if(employee == None):
      print('Employee doesnt exists')
      return
    rfid = input('Enter RFID card: ')
    assignRFIDToEmployee(employee, rfid)
  except KeyboardInterrupt:
    return
  
def callRemoveRFID():
  try:
    displayEmployees()
    employeeId = input('Enter employee id: ')
    employee = db.employees.find_one({'employee_id': employeeId})
    if(employee == None):
      print('Employee doesnt exists')
      return
    removeEmployeeRFID(employee)
  except KeyboardInterrupt:
    return

def callLogging():
  print('Log board')
  print('Ctrl + C returns to menu')
  while True:
    try:
      displayLogs()
      input()
    except KeyboardInterrupt:
      break

def chooseFunction(chosenOption):
  return {
    '1': callAddTerminal,
    '2': callRemoveTerminal,
    '3': callAssignRFID,
    '4': callRemoveRFID,
    '5': callLogging
  }.get(chosenOption, wrongOption)

def app():
  client.loop_start()
  while(True):
    try:
      menu()
      option = input("What you want to do?\n")
      chooseFunction(option)()
    except KeyboardInterrupt:
      break
    print()
    
app()