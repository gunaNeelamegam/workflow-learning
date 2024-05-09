from requests import get
from time import sleep
from json import load
keys = open("ble_agent_app/key_events.json")

def test():
    for key,value in load(keys)["key_events"].items():
        try:
            print(key, value)
            response = get(f"http://10.42.0.27:5000/python/{value}",timeout=5)
            print(f"{response}")
        except Exception as e:
            print(e.args)
        sleep(1)

from requests import post
def open_app():
    body = {"name" : "com.android.settings", 
    "bname": "com.android.settings.fuelgauge.PowerUsageSummary"}
    response = post("http://10.42.0.27:5000/app", json=body)
    print(response)

def command(command):
    response = post("http://10.42.0.27:5000/command", json= {"command": command})
    print(response)
    return response


def java(command):
    response = get(f"http://10.42.0.27:5000/java/runtime1/{command}")
    return response
