import os
import sys
from argparse import ArgumentParser
from ctypes import windll
from logging import (DEBUG, INFO, WARNING, FileHandler, Formatter, NullHandler,
                     StreamHandler, getLogger)
from threading import Thread
from time import sleep

import psutil
import pygetwindow
import pythoncom
import TouchPortalAPI as TP
import win32process
from comtypes import COMError
from pycaw.constants import AudioSessionState
from pycaw.magic import MagicManager, MagicSession
from pycaw.pycaw import EDataFlow, ERole

from audioUtil import audioSwitch
from audioUtil.audioController import (AudioController, get_process_id,
                                       getMasterVolume, muteAndUnMute,
                                       setMasterVolume, volumeChanger,
                                       setDeviceVolume)
from tppEntry import *
from tppEntry import __version__

sys.coinit_flags = 0

try:
    TPClient = TP.Client(
        pluginId = PLUGIN_ID,  # required ID of this plugin
        sleepPeriod = 0.05,    # allow more time than default for other processes
        autoClose = True,      # automatically disconnect when TP sends "closePlugin" message
        checkPluginId = True,  # validate destination of messages sent to this plugin
        maxWorkers = 4,        # run up to 4 event handler threads
        updateStatesOnBroadcast = False,  # do not spam TP with state updates on every page change
    )
except Exception as e:
    sys.exit(f"Could not create TP Client, exiting. Error was:\n{repr(e)}")

g_log = getLogger()

audio_ignore_list = []
volumeprocess = ["Master Volume", "Current app"]
running = False
pythoncom.CoInitialize()

dataMapper = {
            "Output": EDataFlow.eRender.value,
            "Input": EDataFlow.eCapture.value,
            "Default": ERole.eMultimedia.value,
            "Communications": ERole.eCommunications.value
        }

def updateVolumeMixerChoicelist():
    TPClient.choiceUpdate(TP_PLUGIN_ACTIONS["Inc/DecrVol"]['data']['AppChoice']['id'], volumeprocess[1:])
    TPClient.choiceUpdate(TP_PLUGIN_ACTIONS["AppMute"]['data']['appChoice']['id'], volumeprocess[1:])
    TPClient.choiceUpdate(TP_PLUGIN_CONNECTORS["APP control"]["data"]["appchoice"]['id'], volumeprocess)
    TPClient.choiceUpdate(TP_PLUGIN_ACTIONS["AppAudioSwitch"]["data"]["AppChoice"]["id"], volumeprocess[1:])

def removeAudioState(app_name):
    global volumeprocess
    TPClient.removeStateMany([
            PLUGIN_ID + f".createState.{app_name}.muteState",
            PLUGIN_ID + f".createState.{app_name}.volume",
            PLUGIN_ID + f".createState.{app_name}.active"
            ])
    volumeprocess.remove(app_name)
    updateVolumeMixerChoicelist() # Update with new changes

def audioStateManager(app_name):
    global volumeprocess
    g_log.debug(f"AUDIO EXEMPT LIST {audio_ignore_list}")

    if app_name not in volumeprocess:
        g_log.info("Creating states")
        TPClient.createStateMany([
                {   
                    "id": PLUGIN_ID + f".createState.{app_name}.muteState",
                    "desc": f"{app_name} Mute State",
                    "parentGroup": "Audio process state",
                    "value": ""
                },
                {
                    "id": PLUGIN_ID + f".createState.{app_name}.volume",
                    "desc": f"{app_name} Volume",
                    "parentGroup": "Audio process state",
                    "value": ""
                },
                {
                    "id": PLUGIN_ID + f".createState.{app_name}.active",
                    "desc": f"is {app_name} Active",
                    "parentGroup": "Audio process state",
                    "value": ""
                },
                ])
        volumeprocess.append(app_name)

        """UPDATING CHOICES WITH GLOBALS"""
        updateVolumeMixerChoicelist()
        g_log.debug(f"{app_name} state added")

    """ Checking for Exempt Audio"""
    if app_name in audio_ignore_list:
        removeAudioState(app_name)
        return True
    return False

class WinAudioCallBack(MagicSession):
    def __init__(self):
        super().__init__(volume_callback=self.update_volume,
                         mute_callback=self.update_mute,
                         state_callback=self.update_state)

        # ______________ DISPLAY NAME ______________
        self.app_name = self.magic_root_session.app_exec
        #print(f":: new session: {self.app_name}")
        
        if self.app_name not in audio_ignore_list:
            # set initial:
            self.update_mute(self.mute)
            self.update_state(self.state)
            self.update_volume(self.volume)
        

    def update_state(self, new_state):
        """
        when status changed
        (see callback -> AudioSessionEvents -> OnStateChanged)
        """
        
        if self.app_name not in audio_ignore_list:
            if new_state == AudioSessionState.Inactive:
                # AudioSessionStateInactive
                """Sesssion is Inactive"""
                g_log.info(f"{self.app_name} not active")
                TPClient.stateUpdate(PLUGIN_ID + f".createState.{self.app_name}.active","False")
    
            elif new_state == AudioSessionState.Active:
                """Session Active"""
                g_log.info(f"{self.app_name} is an Active Session")
                TPClient.stateUpdate(PLUGIN_ID + f".createState.{self.app_name}.active","True")
    
        if new_state == AudioSessionState.Expired:
            """Removing Expired States"""
            removeAudioState(self.app_name)

    
    def update_volume(self, new_volume):
        """
        when volume is changed externally - Updating Sliders and Volume States
        (see callback -> AudioSessionEvents -> OnSimpleVolumeChanged )
        """
        if self.app_name not in audio_ignore_list:
            TPClient.stateUpdate(PLUGIN_ID + f".createState.{self.app_name}.volume", str(round(new_volume*100)))
            #print(f"{self.app_name} NEW VOLUME", str(round(new_volume*100)))
            TPClient.connectorUpdate(
                f"pc_{TP_PLUGIN_INFO['id']}_{TP_PLUGIN_CONNECTORS['APP control']['id']}|{TP_PLUGIN_CONNECTORS['APP control']['data']['appchoice']['id']}={self.app_name}",
                round(new_volume*100))
            
            """Checking for Current App If Its Active, Adjust it also"""
            if (activeWindow := getActiveExecutablePath()) != "":
                TPClient.connectorUpdate(
                    f"pc_{TP_PLUGIN_INFO['id']}_{TP_PLUGIN_CONNECTORS['APP control']['id']}|{TP_PLUGIN_CONNECTORS['APP control']['data']['appchoice']['id']}=Current app",
                    int(new_volume*100) if os.path.basename(activeWindow) == self.app_name else 0)

    def update_mute(self, muted):
        """ when mute state is changed by user or through other app """
        
        if self.app_name not in audio_ignore_list:
            isDeleted = audioStateManager(self.app_name)

            if not isDeleted:
                TPClient.stateUpdate(PLUGIN_ID + f".createState.{self.app_name}.muteState", "Muted" if muted else "Un-muted")

def updateDevice(options, choiceId, instanceId=None):
    deviceList = list(audioSwitch.MyAudioUtilities.getAllDevices(options).keys())
    if (choiceId == TP_PLUGIN_ACTIONS["AppAudioSwitch"]["data"]["devicelist"]["id"] or \
            choiceId == TP_PLUGIN_ACTIONS["setDeviceVolume"]["data"]["deviceOption"]["id"]):

        deviceList.insert(0, "Default")
    if instanceId:
        TPClient.choiceUpdateSpecific(choiceId, deviceList, instanceId)
    else:
        TPClient.choiceUpdate(choiceId, deviceList)
    g_log.debug(f'updating {options} {deviceList}')


def getActiveExecutablePath():
    hWnd = windll.user32.GetForegroundWindow()
    if hWnd == 0:
        return None # Note that this function doesn't use GetLastError().
    else:
        _, pid = win32process.GetWindowThreadProcessId(hWnd)
        return psutil.Process(pid).exe()

import comtypes

STGM_READ = 0x00000000
def getDevicebydata(edata, erole):
    DEVPKEY_Device_FriendlyName = "{a45c254e-df1c-4efd-8020-67d146a850e0} 14".upper()

    device = ""
    audioDevice = None

    comtypes.CoInitialize()
    try:
        audioDevice = audioSwitch.MyAudioUtilities.GetDeviceState(edata, erole)
        if audioDevice:
            properties = {}
            store = audioDevice.OpenPropertyStore(STGM_READ)
            try:
                propCount = store.GetCount()
                for j in range(propCount):
                    pk = store.GetAt(j)
                    value = store.GetValue(pk)
                    v = value.GetValue()
                    value.clear()

                    name = str(pk)
                    properties[name] = v
                device = properties.get(DEVPKEY_Device_FriendlyName, "")

            finally:
                value.clear()
                store.Release()
                del store
                del properties

    except COMError as exc:
        pass

    finally:
        if audioDevice:
            audioDevice.Release()
            del audioDevice
        comtypes.CoUninitialize()
    return str(device)
        

def stateUpdate():
    updateSwitch = 1
    while running:
        sleep(0.5)
        TPClient.stateUpdate(TP_PLUGIN_STATES['FocusedAPP']['id'], pygetwindow.getActiveWindowTitle())

        master_volume = getMasterVolume()

        TPClient.connectorUpdate(
                f"pc_{TP_PLUGIN_INFO['id']}_{TP_PLUGIN_CONNECTORS['APP control']['id']}|{TP_PLUGIN_CONNECTORS['APP control']['data']['appchoice']['id']}=Master Volume",
                master_volume)
        
        TPClient.stateUpdate(TP_PLUGIN_STATES["master volume"]["id"], str(master_volume))

        activeWindow = getActiveExecutablePath()
        if activeWindow != "" and activeWindow != None and (current_app_volume := AudioController(os.path.basename(activeWindow)).process_volume()):
            TPClient.connectorUpdate(
                    f"pc_{TP_PLUGIN_INFO['id']}_{TP_PLUGIN_CONNECTORS['APP control']['id']}|{TP_PLUGIN_CONNECTORS['APP control']['data']['appchoice']['id']}=Current app",
                    int(current_app_volume*100.0))
            TPClient.stateUpdate(TP_PLUGIN_STATES['currentAppVolume']['id'], str(int(current_app_volume*100.0)))
        else:
            TPClient.connectorUpdate(
                    f"pc_{TP_PLUGIN_INFO['id']}_{TP_PLUGIN_CONNECTORS['APP control']['id']}|{TP_PLUGIN_CONNECTORS['APP control']['data']['appchoice']['id']}=Current app",
                    0)
            TPClient.stateUpdate(TP_PLUGIN_STATES['currentAppVolume']['id'], 0)

        if (updateSwitch == 1):
            TPClient.stateUpdate(TP_PLUGIN_STATES["outputDevice"]["id"], getDevicebydata(EDataFlow.eRender.value, ERole.eMultimedia.value))
            updateSwitch = 2
        elif (updateSwitch == 2):
            TPClient.stateUpdate(TP_PLUGIN_STATES["outputcommicationDevice"]["id"], getDevicebydata(EDataFlow.eRender.value, ERole.eCommunications.value))
            updateSwitch = 3
        elif (updateSwitch == 3):
            TPClient.stateUpdate(TP_PLUGIN_STATES["inputDevice"]["id"], getDevicebydata(EDataFlow.eCapture.value, ERole.eMultimedia.value))
            updateSwitch = 4
        elif (updateSwitch == 4):
            TPClient.stateUpdate(TP_PLUGIN_STATES["inputDeviceCommication"]["id"], getDevicebydata(EDataFlow.eCapture.value, ERole.eCommunications.value))
            updateSwitch = 1
        
        pythoncom.CoUninitialize()

def handleSettings(settings, on_connect=False):
    global audio_ignore_list

    settings = { list(settings[i])[0] : list(settings[i].values())[0] for i in range(len(settings)) }

    if (value := settings.get(TP_PLUGIN_SETTINGS['ignore list']['name'])) is not None:
        audio_ignore_list = value if value != TP_PLUGIN_SETTINGS['ignore list']['default'] else []

@TPClient.on(TP.TYPES.onConnect)
def onConnect(data):
    global running
    g_log.info(f"Connected to TP v{data.get('tpVersionString', '?')}, plugin v{data.get('pluginVersion', '?')}.")
    g_log.debug(f"Connection: {data}")
    if settings := data.get('settings'):
        handleSettings(settings, True)

    running = True
    run_callback()
    #g_log.debug(f"--------- Magic already in session!! ---------\n------{err}------")
    
    Thread(target=stateUpdate).start()

def run_callback():
    pythoncom.CoInitialize()
    try:
        MagicManager.magic_session(WinAudioCallBack)
    except Exception as e:
        g_log.info(e, exc_info=True)


# Settings handler
@TPClient.on(TP.TYPES.onSettingUpdate)
def onSettingUpdate(data):
    g_log.debug(f"Settings: {data}")
    if (settings := data.get('values')):
        handleSettings(settings, False)

# Action handler
@TPClient.on(TP.TYPES.onAction)
def onAction(data):
    g_log.debug(f"Action: {data}")
    # check that `data` and `actionId` members exist and save them for later use
    if not (action_data := data.get('data')) or not (actionid := data.get('actionId')):
        return

    elif actionid == TP_PLUGIN_ACTIONS['AppMute']['id']:
        if action_data[0]['value'] != '':
            if action_data[0]['value'] == "Current app":
                activeWindow = getActiveExecutablePath()
                if activeWindow != "":
                    muteAndUnMute(os.path.basename(activeWindow), action_data[1]['value'])
            elif action_data[0]['value'] == "Master Volume":
                pass # idk
            else:
                muteAndUnMute(action_data[0]['value'], action_data[1]['value'])
    elif actionid == TP_PLUGIN_ACTIONS['Inc/DecrVol']['id']:
        volume_value = int(action_data[2]['value'])
        volume_value = max(0, min(volume_value, 100))

        if action_data[0]['value'] == "Current app":
            activeWindow = getActiveExecutablePath()
            if activeWindow != "":
                volumeChanger(os.path.basename(activeWindow), action_data[1]['value'], volume_value)
        else:
            volumeChanger(action_data[0]['value'], action_data[1]['value'], volume_value)
    elif actionid == TP_PLUGIN_ACTIONS["ChangeOut/Input"]["id"] and action_data[0]['value'] != "Pick One": 
        deviceId = audioSwitch.MyAudioUtilities.getAllDevices(action_data[0]['value'])
        deviceId = deviceId.get(action_data[1]['value'])
        if (deviceId):
            audioSwitch.switchOutput(deviceId, dataMapper[action_data[2]['value']])
        # for device in audioSwitch.MyAudioUtilities.getAllDevices(action_data[0]['value']):
        #     if device.FriendlyName == action_data[1]['value']:
        #         audioSwitch.switchOutput(device.id, dataMapper[action_data[2]['value']])

    elif actionid == TP_PLUGIN_ACTIONS["ToggleOut/Input"]["id"] and action_data[0]['value'] != "Pick One":
        deviceId = audioSwitch.MyAudioUtilities.getAllDevices(action_data[0]['value'])
        currentDeviceId = deviceId.get(getDevicebydata(dataMapper[action_data[0]['value']], dataMapper[action_data[3]['value']]))
        choiceDeviceId1 = deviceId.get(action_data[1]['value'])
        choiceDeviceId2 = deviceId.get(action_data[2]['value'])
        if (choiceDeviceId1,choiceDeviceId2):
            if choiceDeviceId1 == currentDeviceId:
                audioSwitch.switchOutput(choiceDeviceId2, dataMapper[action_data[3]['value']])
            else:
                audioSwitch.switchOutput(choiceDeviceId1, dataMapper[action_data[3]['value']])
        # for device in audioSwitch.MyAudioUtilities.getAllDevices(action_data[0]['value']):
        #     if device.FriendlyName == action_data[1]['value']:
        #         audioSwitch.switchOutput(device.id, dataMapper[action_data[2]['value']])
               
    elif actionid == TP_PLUGIN_ACTIONS["AppAudioSwitch"]["id"] and action_data[2]["value"] != "Pick One":
        deviceId = ""
        if (action_data[1]["value"] != "Default"):
            deviceId = audioSwitch.MyAudioUtilities.getAllDevices(action_data[2]["value"])
            deviceId = deviceId.get(action_data[1]["value"])

        if ((processid := get_process_id(action_data[0]['value'])) != None):
            g_log.info(f"args devId: {deviceId}, processId: {processid}")
            if (deviceId == "" and action_data[1]["value"] == "Default") or deviceId:
                audioSwitch.SetApplicationEndpoint(deviceId, 1 if action_data[2]["value"] == "Input" else 0, processid)

    elif actionid == TP_PLUGIN_ACTIONS["setDeviceVolume"]["id"] and action_data[0]["value"] != "Pick One":
        device = "default"
        if action_data[1]['value'].lower() != "default":
            devices = audioSwitch.MyAudioUtilities.getAllDevices(action_data[0]["value"])
            device = devices.get(action_data[1]['value'], "")

        if device:
            try:
                volume = int(action_data[2]['value'])
            except ValueError:
                return
            
            setDeviceVolume(device, action_data[0]["value"], volume)
        # for device in audioSwitch.MyAudioUtilities.getAllDevices(action_data[2]["value"]):
        #     if (deviceId := '' if action_data[1]["value"] == "Default" == 'Default' else device.id if device.FriendlyName == action_data[1]["value"] else None) != None:
                # if (processid := get_process_id(action_data[0]['value'])) != None:
                #     g_log.info(f"args devId: {deviceId}, processId: {processid}")
                #     audioSwitch.SetApplicationEndpoint(deviceId, 1 if action_data[2]["value"] == "Input" else 0, processid)
            

    else:
        g_log.warning("Got unknown action ID: " + actionid)

@TPClient.on(TP.TYPES.onHold_down)
def heldingButton(data):
    g_log.debug(f"heldingButton: {data}")
    while True:
        if TPClient.isActionBeingHeld(TP_PLUGIN_ACTIONS['Inc/DecrVol']['id']):
            volume_value = int(data['data'][2]['value'])
            volume_value = max(0, min(volume_value, 100))
            volumeChanger(data['data'][0]['value'], data['data'][1]['value'], volume_value)
            sleep(0.05)
        else:
            break
    g_log.debug(f"Not helding button {data}")

@TPClient.on(TP.TYPES.onConnectorChange)
def connectors(data):
    g_log.info(f"connector Change: {data}")
    if data['connectorId'] == TP_PLUGIN_CONNECTORS["APP control"]['id']:
        if data['data'][0]['value'] == "Master Volume":
            setMasterVolume(data['value'])
        elif data['data'][0]['value'] == "Current app":
            activeWindow = getActiveExecutablePath()
            
            if activeWindow != "":
                volumeChanger(os.path.basename(activeWindow), "Set", data['value'])
        else:
            try:
                volumeChanger(data['data'][0]['value'], "Set", data['value'])
            except Exception as e:
                g_log.debug(f"Exception in other app volume change Error: " + str(e))
    
    elif data["connectorId"] == TP_PLUGIN_CONNECTORS["Windows Audio"]["id"]:
        device = "default"
        if data['data'][0]['value'].lower() != "default":
            devices = audioSwitch.MyAudioUtilities.getAllDevices(data['data'][0]['value'])
            device = devices.get(data['data'][1]['value'], "")

        if device:
            print(data)
            setDeviceVolume(device, data['data'][0]['value'], data['value'])

@TPClient.on(TP.TYPES.onListChange)
def onListChange(data):
    g_log.info(f"onlistChange: {data}")
    if data['actionId'] == TP_PLUGIN_ACTIONS["ChangeOut/Input"]['id'] and \
        data['listId'] == TP_PLUGIN_ACTIONS["ChangeOut/Input"]["data"]["optionSel"]["id"]:
        try:
            updateDevice(data['value'], TP_PLUGIN_ACTIONS["ChangeOut/Input"]['data']['deviceOption']['id'], data['instanceId'])
        except Exception as e:
            g_log.info("Update device input/output KeyError: " + str(e))
    elif data['actionId'] == TP_PLUGIN_ACTIONS["ToggleOut/Input"]['id'] and \
        data['listId'] == TP_PLUGIN_ACTIONS["ToggleOut/Input"]["data"]["optionSel"]["id"]:
        try:
            updateDevice(data['value'], TP_PLUGIN_ACTIONS["ToggleOut/Input"]['data']['deviceOption1']['id'], data['instanceId'])
            updateDevice(data['value'], TP_PLUGIN_ACTIONS["ToggleOut/Input"]['data']['deviceOption2']['id'], data['instanceId'])
        except Exception as e:
            g_log.info("Update device input/output KeyError: " + str(e))
    elif data['actionId'] == TP_PLUGIN_ACTIONS["AppAudioSwitch"]["id"] and \
        data["listId"] == TP_PLUGIN_ACTIONS["AppAudioSwitch"]["data"]["deviceType"]["id"]:
        try:
            updateDevice(data['value'], TP_PLUGIN_ACTIONS["AppAudioSwitch"]["data"]["devicelist"]["id"], data['instanceId'])
        except Exception as e:
            g_log.info("Update device input/output KeyError: " + str(e))
    
    elif data['actionId'] == TP_PLUGIN_ACTIONS["setDeviceVolume"]["id"] and \
        data["listId"] == TP_PLUGIN_ACTIONS["setDeviceVolume"]["data"]["deviceType"]["id"]:
        try:
            updateDevice(data['value'], TP_PLUGIN_ACTIONS["setDeviceVolume"]["data"]["deviceOption"]["id"], data['instanceId'])
        except Exception as e:
            g_log.info("Update device setDeviceVolume error " + str(e))
    
    # elif data['actionId'] == TP_PLUGIN_CONNECTORS["Windows Audio"]["id"] and \
    #     data["listId"] == (listId := TP_PLUGIN_CONNECTORS["Windows Audio"]["data"]["deviceType"]["id"]):
    #     try:
    #         updateDevice(data['value'], listId, data['instanceId'])
    #     except Exception as e:
    #         g_log.warning("Update device setDeviceVolume error " + str(e))

# Shutdown handler
@TPClient.on(TP.TYPES.onShutdown)
def onShutdown(data):
    g_log.info('Received shutdown event from TP Client.')

# Error handler
# @TPClient.on(TP.TYPES.onError)
# def onError(exc):
#     g_log.error(f'Error in TP Client event handler: {repr(exc)}')

def main():
    global TPClient, g_log

    # Handle CLI arguments
    parser = ArgumentParser()
    parser.add_argument("-d", action='store_true',
                        help="Use debug logging.")
    parser.add_argument("-w", action='store_true',
                        help="Only log warnings and errors.")
    parser.add_argument("-q", action='store_true',
                        help="Disable all logging (quiet).")
    parser.add_argument("-l", metavar="<logfile>",
                        help="Log to this file (default is stdout).")
    parser.add_argument("-s", action='store_true',
                        help="If logging to file, also output to stdout.")

    opts = parser.parse_args()
    del parser

    # set up logging
    if opts.q:
        # no logging at all
        g_log.addHandler(NullHandler())
    else:
        # set up pretty log formatting (similar to TP format)
        fmt = Formatter(
            fmt="{asctime:s}.{msecs:03.0f} [{levelname:.1s}] [{filename:s}:{lineno:d}] {message:s}",
            datefmt="%H:%M:%S", style="{"
        )
        # set the logging level
        if   opts.d: g_log.setLevel(DEBUG)
        elif opts.w: g_log.setLevel(WARNING)
        else:        g_log.setLevel(INFO)


        # set up log destination (file/stdout)
        if opts.l:
            try:
                # note that this will keep appending to any existing log file
                fh = FileHandler(str("log.txt"))
                fh.setFormatter(fmt)
                g_log.addHandler(fh)
            except Exception as e:
                opts.s = True
                g_log.info(f"Error while creating file logger, falling back to stdout. {repr(e)}")
        if not opts.l or opts.s:
            sh = StreamHandler(sys.stdout)
            sh.setFormatter(fmt)
            g_log.addHandler(sh)

    g_log.info(f"Starting {TP_PLUGIN_INFO['name']} v{__version__} on {sys.platform}.")
    ret = 1
    try:
        # Connect to Touch Portal desktop application.
        # If connection succeeds, this method will not return (blocks) until the client is disconnected.
        TPClient.connect()
        g_log.info('TP Client closed.')
    except KeyboardInterrupt:
        g_log.warning("Caught keyboard interrupt, exiting.")
    except Exception:
        # This will catch and report any critical exceptions in the base TPClient code,
        # _not_ exceptions in this plugin's event handlers (use onError(), above, for that).
        from traceback import format_exc
        g_log.error(f"Exception in TP Client:\n{format_exc()}")
        ret = -1
    finally:
        # Make sure TP Client is stopped, this will do nothing if it is already disconnected.
        TPClient.disconnect()

    # TP disconnected, clean up.
    del TPClient

    g_log.info(f"{TP_PLUGIN_INFO['name']} stopped.")
    return ret

if __name__ == "__main__":
    main()
