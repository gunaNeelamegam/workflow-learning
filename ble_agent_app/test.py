from requests import get
from time import sleep
from json import load
keys = open("ble_agent_app/key_events.json")

for key,value in load(keys)["key_events"].items():
    sleep(1)
    response = get(f"http://10.42.0.27:5000/python/{value}")
    print(f"{key} : {value} = {response}")