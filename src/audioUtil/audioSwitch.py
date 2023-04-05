from __future__ import print_function

import comtypes
from pycaw.constants import CLSID_MMDeviceEnumerator
from pycaw.pycaw import (DEVICE_STATE, AudioUtilities, EDataFlow,
                         IMMDeviceEnumerator)

from . import policyconfig as pc
from pycaw.constants import ERole
import ctypes

audioDll = ctypes.CDLL("src/AudioDLL.dll")

class MyAudioUtilities(AudioUtilities):
    @staticmethod
    def GetDeviceState(devicetype, roletype):
        device_enumerator = comtypes.CoCreateInstance(
            CLSID_MMDeviceEnumerator,
            IMMDeviceEnumerator,
            comtypes.CLSCTX_INPROC_SERVER)

        default_device = device_enumerator.GetDefaultAudioEndpoint(devicetype, roletype)
        return default_device

    @staticmethod
    def getAllDevices(direction, State = DEVICE_STATE.ACTIVE.value):
        devices = []
        # for all use EDataFlow.eAll.value
        if direction == "Input":
            Flow = EDataFlow.eCapture.value     # 1
        else:
            # Output
            Flow = EDataFlow.eRender.value      # 0
        
        deviceEnumerator = comtypes.CoCreateInstance(
            CLSID_MMDeviceEnumerator,
            IMMDeviceEnumerator,
            comtypes.CLSCTX_INPROC_SERVER)
        if deviceEnumerator is None:
            return devices
        

        collection = deviceEnumerator.EnumAudioEndpoints(Flow, State)
        if collection is None:
            return devices

        count = collection.GetCount()
        for i in range(count):
            dev = collection.Item(i)
            if dev is not None:
                if not ": None" in str(AudioUtilities.CreateDevice(dev)):
                    devices.append(AudioUtilities.CreateDevice(dev))
        return devices



def switchOutput(deviceId, role):
    policy_config = comtypes.CoCreateInstance(
        pc.CLSID_PolicyConfigClient,
        pc.IPolicyConfig,
        comtypes.CLSCTX_ALL
    )
    print(deviceId, role)
    policy_config.SetDefaultEndpoint(deviceId, role)

SetApplicationEndpoint = audioDll.SetApplicationEndpoint



