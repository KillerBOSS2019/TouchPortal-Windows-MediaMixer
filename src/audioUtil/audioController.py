from ctypes import POINTER, cast

import comtypes
import pythoncom
from comtypes import CLSCTX_ALL
from pycaw.constants import CLSID_MMDeviceEnumerator
from pycaw.pycaw import (AudioUtilities, EDataFlow, IAudioEndpointVolume,
                         IMMDeviceEnumerator)


class AudioController(object):
    pythoncom.CoInitialize()
    def __init__(self, process_name):
        self.process_name = process_name
        self.volume = self.process_volume()

    def process_volume(self):
        pythoncom.CoInitialize()  # 3rd coinitilize...
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            interface = session.SimpleAudioVolume
            if session.Process and session.Process.name() == self.process_name:
                return interface.GetMasterVolume()

    def set_volume(self, decibels):
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            interface = session.SimpleAudioVolume
            if session.Process and session.Process.name() == self.process_name:
                # only set volume in the range 0.0 to 1.0
                self.volume = min(1.0, max(0.0, decibels))
                interface.SetMasterVolume(self.volume, None)

    def decrease_volume(self, decibels):
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            interface = session.SimpleAudioVolume
            if session.Process and session.Process.name() == self.process_name:
                # 0.0 is the min value, reduce by decibels
                self.volume = max(0.0, self.volume-decibels)
                interface.SetMasterVolume(self.volume, None)

    def increase_volume(self, decibels):
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            interface = session.SimpleAudioVolume
            if session.Process and session.Process.name() == self.process_name:

                # 1.0 is the max value, raise by decibels
                self.volume = min(1.0, self.volume+decibels)
                interface.SetMasterVolume(self.volume, None)


def muteAndUnMute(process, value):
    pythoncom.CoInitialize()
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        volume = session.SimpleAudioVolume
        if session.Process and session.Process.name() == process:
            if value == "Toggle":
                value = 0 if volume.GetMute() == 1 else 1
            elif value == "Mute":
                value = 1
            elif value == "Unmute":
                value = 0
            volume.SetMute(value, None)


def volumeChanger(process, action, value):
    pythoncom.CoInitialize()
    if process == "Master Volume":
        if action == "Set":
            setMasterVolume(value)
        else:
            value = +value if action == "Increase" else -value
            setMasterVolume(100 if (master_vol := getMasterVolume() + value) and master_vol > 100 else master_vol)
    elif action == "Set":
        AudioController(str(process)).set_volume((int(value)*0.01))
    elif action == "Increase":
        AudioController(str(process)).increase_volume((int(value)*0.01))

    elif action == "Decrease":
        AudioController(str(process)).decrease_volume((int(value)*0.01))


def setMasterVolume(Vol):
    pythoncom.CoInitialize()
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    scalarVolume = int(Vol) / 100
    volume.SetMasterVolumeLevelScalar(scalarVolume, None)

def getMasterVolume() -> int:
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)

    # Get the volume range and current volume level
    volume = interface.QueryInterface(IAudioEndpointVolume)
    volume_percent = int(round(volume.GetMasterVolumeLevelScalar() * 100))

    devices.Release()
    # Release the interface COM object
    comtypes.CoUninitialize()
    return volume_percent

def getDeviceObject(device_id, direction="Output"):
    deviceEnumerator = comtypes.CoCreateInstance(
            CLSID_MMDeviceEnumerator,
            IMMDeviceEnumerator,
            comtypes.CLSCTX_INPROC_SERVER)
    
    if deviceEnumerator is None: return None

    flow = EDataFlow.eCapture.value
    if direction.lower() == "output":
        flow = EDataFlow.eRender.value

    devices = deviceEnumerator.EnumAudioEndpoints(flow, 1)

    for dev in devices:
        if dev.GetId() == device_id:
            return dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    
    return None
    
def setDeviceVolume(device_id, direction, volume_level):
    pythoncom.CoInitialize()
    if device_id == "default":
        if direction.lower() == "output":
            device = AudioUtilities.GetSpeakers()
        else:
            device = AudioUtilities.GetMicrophone()
        device_object = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    else:
        device_object = getDeviceObject(device_id, direction)

    if device_object:
        volume = cast(device_object, POINTER(IAudioEndpointVolume))
        scalar_volume = float(volume_level) / 100
        volume.SetMasterVolumeLevelScalar(scalar_volume, None)

    pythoncom.CoUninitialize()

def get_process_id(name):
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.name() == name:
            return session.Process.pid
    return None
