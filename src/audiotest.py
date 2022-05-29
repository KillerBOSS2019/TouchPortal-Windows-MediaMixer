from audioUtil import audioSwitch
from pycaw.constants import ERole
from pycaw.pycaw import AudioUtilities

#Echo = audioSwitch.MyAudioUtilities.getAllDevices("Input")
#print(Echo)
# name = audioSwitch.MyGetAudioDevices("out")[0].FriendlyName

# print(Echo, name)
# # 0 = default
# # 
# audioSwitch.switchOutput(Echo, 2)


# print(AudioUtilities.GetMicrophone().id)
# print(AudioUtilities.GetSpeakers().id)
from pycaw.constants import CLSID_MMDeviceEnumerator
from pycaw.pycaw import (DEVICE_STATE, AudioUtilities, EDataFlow,
                         IMMDeviceEnumerator)

# import comtypes

# class MyAudioUtilities(AudioUtilities):
#     @staticmethod
#     def GetDeviceId(id, default=1):
#         device_enumerator = comtypes.CoCreateInstance(
#             CLSID_MMDeviceEnumerator,
#             IMMDeviceEnumerator,
#             comtypes.CLSCTX_INPROC_SERVER)

#         device_enumerator

#         thisDevice = device_enumerator.GetDevice(id)

#         if default == 0:
#             # output
#             thisDevice = device_enumerator.GetDefaultAudioEndpoint(EDataFlow.eRender.value, ERole.eMultimedia.value)
#         else:
#             # input
#             thisDevice = device_enumerator.GetDefaultAudioEndpoint(EDataFlow.eCapture.value, ERole.eCommunications.value)
#         return thisDevice

# print(MyAudioUtilities.GetDeviceId(Echo).GetId())
# try:
#     audioSwitch.MyAudioUtilities.GetDeviceState(EDataFlow.eCapture.value, ERole.eMultimedia.value)
# except Exception as e:
#     pass

def getDevicebydata(edata, erole):
    device = ""
    try:
        device = audioSwitch.MyAudioUtilities.GetDeviceState(edata, erole)
    except:
        pass

    if device:
        for x in audioSwitch.MyAudioUtilities.getAllDevices("Output" if edata == EDataFlow.eRender.value else "Input"):
            if device.GetId() == x.id:
                return x.FriendlyName

    return device
