from flask import render_template, Flask,request
from jnius import autoclass, cast
from platform import platform
from android.broadcast import BroadcastReceiver
from android import api_version, mActivity
from android.permissions import request_permissions, Permission, check_permission
from typing import Any,Union
from jnius import autoclass
PORT = 5000
HOST = "0.0.0.0"
Runtime = autoclass("java.lang.Runtime")
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')

class BleController:

    class BleDevice:
        def __init__(self, name ="", address= "") -> None:
            self.name = name
            self.address = address

        def __eq__(self, other):
            return isinstance(other, BleController.BleDevice) and (self.name == other.name and self.address == other.address)

        def __hash__(self):
            return hash((self.name, self.address))

    def __init__(self) -> None:
        # Change based on android docs
        self.BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
        self.UUID = "00001101-0000-1000-8000-00805F9B34FB"

        self.ble_adapter = self.BluetoothAdapter.getDefaultAdapter()
        self.device_scanned_count = 0
        self.scanned_devices = set()
        self.connected_device = None
        self.is_connected = False
        self.FOUND = BluetoothDevice.ACTION_FOUND
        self.STARTED = self.BluetoothAdapter.ACTION_DISCOVERY_STARTED
        self.FINISHED = self.BluetoothAdapter.ACTION_DISCOVERY_FINISHED

    def on_scanning(self, context, intent):
        action = intent.getAction()
        if action == self.STARTED:
            self.device_scanned_count = 0
            self.scanned_devices = None
            self.scanned_devices = set()
            print("SCANNING STARTED ")

        elif action == self.FOUND:
            device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
            name = intent.getExtra(BluetoothDevice.EXTRA_NAME)
            self.device_scanned_count =+ 1
            if device:
                print("SCANNING : ", name, device.toString())
                if not name:
                    name = ""
            self.scanned_devices.add(BleController.BleDevice(name, device.toString()))

        elif action == self.FINISHED:
            self.ble_adapter.cancelDiscovery()
            self.boardcast_receiver.stop()
            self.boardcast_receiver = None
            print("SCANNING STOPED")

    def enable_adapter(self) -> bool:
        if (self.ble_adapter and not self.ble_adapter.isEnabled()):
            self.ble_adapter.enable()
        return self.ble_adapter.isEnabled()

    def disable_adapter(self)->bool:
        if (self.ble_adapter and self.ble_adapter.isEnabled()):
            self.ble_adapter.disable()
        return self.ble_adapter.isEnabled()

    def paired_devices(self):
        if self.ble_adapter:
            bounded_devices = self.ble_adapter.getBondedDevices().toArray()
            response = {}
            for device in bounded_devices:
                response = {**response , device.getName() : device.getAddress()}
        return response

    def scan(self):
        actions = [self.FOUND, self.STARTED, self.FINISHED]
        self.boardcast_receiver = BroadcastReceiver(self.on_scanning, actions=actions)
        self.boardcast_receiver.start()
        self.ble_adapter.startDiscovery()

    def is_device_paired(self, remote_info: dict) -> bool:
        name = remote_info.get("name", "").lower()
        mac_address = remote_info.get("mac_address","").lower()
        bounded_devices = self.ble_adapter.getBondedDevices().toArray()

        def equals(device):
            if name == device.getName().lower() or mac_address == device.getAddress().lower():
                return True
            return False

        filtered_devices = filter(equals, bounded_devices)
        return (True,filtered_devices[0]) if len(filtered_devices) else (False, None)

    def pair(self, mac_address: str):
        if self.ble_adapter and mac_address.strip() != "":
            device = self.ble_adapter.getRemoteDevice(mac_address)
            if device and device.getBondState() != BluetoothDevice.BOND_BONDED:
                device.createBond()

    def connect(self, device_info: dict = {}):
        self.connected_device = None
        device = self.ble_adapter.getRemoteDevice(device_info.get("address"))
        if device and device.getBondState()  != BluetoothDevice.BOND_NONE:
            UUID = autoclass('java.util.UUID')
            self.connected_device = device.createRfcommSocketToServiceRecord(UUID.fromString(self.UUID))
            self.connected_device.getInputStream()
            self.connected_device.getOutputStream()
            self.connected_device.connect()
            print("CONNECTED DEVICE : ", self.connected_device.isConnected(), self.connected_device.getRemoteDevice().toString())

    def disconnect(self):
        if self.connected_device:
            print("DISCONNECTED : ", self.connected_device.isConnected())
            self.connected_device.close()
            self.is_connected = False
            self.connected_device = None

    def unpair(self, address: Union[str, Any]):
        if self.ble_adapter and address.strip():
            device = self.ble_adapter.getRemoteDevice(address)
            if (device.getBondState() == BluetoothDevice.BOND_BONDED):
                   device.removeBond();

class PermissionController:
    def __init__(self) -> None:
        self.ble_permissions = [Permission.BLUETOOTH_CONNECT, Permission.BLUETOOTH_SCAN]
        self.location_permissions = [Permission.ACCESS_FINE_LOCATION]

    def check_run_permission(self, permission):
         return check_permission(permission)

    def permission_status_callback(self, permissions, grants):
        print(f"PERMISSIONS {permissions} GRANTS : {grants}")

    def request_location_permission(self):
        permission_status = {}
        for permission in self.location_permissions:
              response = check_permission(permission)
              permission_status = {**permission_status, permission: response}
              print(f"{permission} : {response}")
        requesting_permissions = filter(lambda permission: not permission_status.get(permission), permission_status)
        request_permissions([*requesting_permissions], self.permission_status_callback)

    def request_bluetooth_permission(self):
        loc_permission_status = {}
        for permission in self.ble_permissions:
            response = check_permission(permission)
            loc_permission_status = {**loc_permission_status, permission: response}
            print(f"{permission}: {response}")
        requesting_permission = filter(lambda permission: not loc_permission_status.get(permission), loc_permission_status)
        request_permissions([*requesting_permission], self.permission_status_callback)

app = Flask(__name__, static_folder="static", template_folder="templates")
ble_controller = BleController()
permission_controller = PermissionController()

@app.get("/")
def index():
    return render_template("index.html")

Intent = autoclass("android.content.Intent")
ComponentName = autoclass("android.content.ComponentName")
@app.post("/app")
def start():
    try:
        body = request.json
        package_name = body.get("name")
        class_name = body.get("bname")

        intent = Intent().setClassName(package_name, class_name)
        # intent.addCategory(Intent.CATEGORY_LAUNCHER);
        # cn = ComponentName(package_name, class_name);
        # intent.setComponent(cn);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        context = mActivity.getApplicationContext()
        context.startActivity(intent)
    except Exception as e:
        print(e.args)
    return "success"

@app.post("/command")
def runwithsu():
    command = request.json.get("command")
    try:
       response = check_output(command.split())
       return str(response)
    except Exception as e:
        print(e.args)
        return "".join(e.args)

@app.post("/process")
def runwithprocess():
    command = request.json.get("command")
    try:
       response = check_output(command.split())
       return str(response)
    except Exception as e:
        print(e.args)
        return "".join(e.args)
    
@app.post("/open")
def open():
    response = check_output(request.json.get("name"))
    return str(response)

    # intent = mActivity.getPackageManager().getLaunchIntentForPackage(packagename)
    # context = mActivity.getApplicationContext()
    # intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
    # context.startActivity(intent)

@app.get("/close")
def close():
    mActivity.finishAndRemoveTask()

@app.get("/request_location_permission")
def request_location_permission():
        try:
            permission_controller.request_location_permission()
            return {
                "status": True,
                "message": "request location permission success"
            }
        except Exception as e:
            return {
                "status": False,
                "message": e.args[0]
            }

@app.get("/request_bluetooth_permission")
def request_bluetooth_run_permission():
        try:
            permission_controller.request_bluetooth_permission()
            return {
                "status": True,
                "message": "request location permission success"
            }
        except Exception as e:
            return {
                "status": False,
                "message": e.args[0]
            }

@app.route("/enable")
def on_bluetooth_adapter():
    response = ble_controller.enable_adapter()
    return {
         "status" : response,
         "message" : "Enabled "if response else "Not Enabled"
    }

@app.route("/disable")
def off_bluetooth_adapter():
    response = ble_controller.disable_adapter()
    return {
         "status" : not response,
         "message" : "Disabled "if not response else "Not Disabled"
    }

@app.route("/paired_devices")
def bounded_devices():
    try:
        response = ble_controller.paired_devices()
        return response
    except Exception as e:
        return {
            "status": False,
            "message": e.args[0]
        }

@app.route("/scan")
def connect_device():
    try:
        ble_controller.scan()
        return {
            "success": True,
            "message": "Scanning Successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message" : e.args[0] if len(e.args) else "Scanning Failed"
        }

@app.route("/scanning_results")
def scanning_result():
    devices = []
    for device in ble_controller.scanned_devices:
        devices.append({"name": device.name ,"address": device.address})

    return {
        "scanning_count": ble_controller.device_scanned_count,
        "devices": devices
    }

@app.post("/pair")
def pair_with_device():
    mac_address = request.json.get("address")
    ble_controller.pair(mac_address)
    return {}

@app.post("/unpair")
def unpair_with_device():
    mac_address = request.json.get("address")
    ble_controller.unpair(mac_address)
    return {}

@app.post("/connect")
def connect_ble():
    device_info = request.json
    try:
        ble_controller.connect(device_info)
        return {
            "status": True,
            "message": "Connection Established"
        }
    except Exception as e:
        return {
            "status": False,
            "message": e.args[0]
        }

from os import system
from subprocess import check_output

@app.get("/java/<command>")
def command(command):
    try:
        respose = system(command)
        return  {
            "message": respose
        }
    except Exception as e:
        return {"failure": "".join(e.args)}

@app.get("/java/runtime1/<command>")
def runtime(command):
    try:
        runtime = Runtime.getRuntime()
        process = runtime.exec(command.split())
        process.wait(10)
        stream = process.getInputStream()
        return str(stream.readAllBytes())
    except Exception as e:
        return "".join(e.args)
    
@app.get("/python/<command>")
def command1(command):
    try:
        from subprocess import Popen
        process = Popen(command.split(), shell= True)
        process.wait(10)
        return str(process.stdout.read())
    
    except Exception as e:
        return {"failure": "".join(e.args)}

@app.get("/disconnect")
def disconnect_with_device():
    try:
        ble_controller.disconnect()
        return {
            "status": True,
            "message": "Disconnected Successfully"
        }
    except Exception as e:
        return {
            "status": False,
            "message": e.args[0]
        }

if __name__ == "__main__":
    app.run(host = HOST, port = PORT,debug = False, threaded=False)
