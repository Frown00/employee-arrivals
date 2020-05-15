import paho.mqtt.client as mqtt
import random
import json
import time
import config

broker = config.BROKER_ADDRESS
port = config.BROKER_PORT
client = mqtt.Client()
terminal = {}

def onConnect(client, userdata, flags, rc):
  print('Connected to mqtt')
  client.subscribe(config.MESSAGE_TOPIC)
  client.subscribe(config.TERMINAL_TOPIC)

def onMessage(client, userdata, msg):
  if(str(msg.topic) == config.MESSAGE_TOPIC):
    payload = json.loads(msg.payload.decode())
    if(payload["is_verified"] == True):
      if(payload["is_present"] == True):
        print(f'Welcome on board { payload["content"] }')
      else:
        print(f'See you soon { payload["content"] }')
    else:
      print("Entrance forbidden! " + payload["content"])
  if(str(msg.topic) == config.TERMINAL_TOPIC):
    payload = json.loads(msg.payload.decode())
    if(payload["is_verified"] == True):
      global terminal
      terminal["id"] = payload["terminalId"]
      terminal["label"] = payload["terminalLabel"]
      print(f'Connected to { terminal["label"] }')
    else:
      print(f'{payload["content"]} + " Try again!')

client.on_connect = onConnect
client.on_message = onMessage
client.connect(broker, port)

def generateRFID():
  allRFID = ['RF1324204400', 'RF1324204423', 'RF1324204433', 'RF1324204411']
  wrongRFID = ['3243432', '0', '-1']
  allRFID += wrongRFID
  randId = random.randint(0, len(allRFID) - 1)
  return allRFID[randId]

def terminalVerification():
  while(terminal == {}):
    if(terminal):
      return
    terminalId = input('Enter terminal id: ')
    client.publish(config.VERIFY_TERMINAL_TOPIC, terminalId)
    time.sleep(1)

def program():
  client.loop_start()
  terminalVerification()
  print('Press any key to imitate employee verification')
  while True:
    try:
      input("Waiting... ")
      rfid = generateRFID()
      send_msg = {
        'rfid': rfid,
        'terminalId': terminal['id'],
        'terminalLabel': terminal['label'],
      }
      client.publish(config.VERIFY_EMPLOYEE_TOPIC, payload=json.dumps(send_msg), qos=2, retain=False)
    except KeyboardInterrupt:
      break

program()