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
from pycaw.constants import AudioSessionState
from pycaw.magic import MagicManager, MagicSession
from pycaw.pycaw import EDataFlow, ERole
from audioUtil import audioSwitch

from audioUtil.audioController import (getMasterVolume, muteAndUnMute,
                                       setMasterVolume, volumeChanger, AudioController)
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
        print("Creating states")
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
                print(f"{self.app_name} not active")
                TPClient.stateUpdate(PLUGIN_ID + f".createState.{self.app_name}.active","False")
    
            elif new_state == AudioSessionState.Active:
                """Session Active"""
                print(f"{self.app_name} is an Active Session")
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
                f"{TP_PLUGIN_CONNECTORS['APP control']['id']}|{TP_PLUGIN_CONNECTORS['APP control']['data']['appchoice']['id']}={self.app_name}",
                round(new_volume*100))
            
            """Checking for Current App If Its Active, Adjust it also"""
            if (activeWindow := getActiveExecutablePath()) != "":
                TPClient.connectorUpdate(
                    f"{TP_PLUGIN_CONNECTORS['APP control']['id']}|{TP_PLUGIN_CONNECTORS['APP control']['data']['appchoice']['id']}=Current app",
                    int(new_volume*100) if os.path.basename(activeWindow) == self.app_name else 0)

    def update_mute(self, muted):
        """ when mute state is changed by user or through other app """
        
        if self.app_name not in audio_ignore_list:
            isDeleted = audioStateManager(self.app_name)

            if not isDeleted:
                TPClient.stateUpdate(PLUGIN_ID + f".createState.{self.app_name}.muteState", "Muted" if muted else "Un-muted")

def updateDevice(options):
    deviceList = [device.FriendlyName for device in audioSwitch.MyAudioUtilities.getAllDevices(options)]
    TPClient.choiceUpdate(TP_PLUGIN_ACTIONS["ChangeOut/Input"]['data']['deviceOption']['id'], deviceList)
    g_log.debug(f'updating {options} {deviceList}')


def getActiveExecutablePath():
    hWnd = windll.user32.GetForegroundWindow()
    if hWnd == 0:
        return None # Note that this function doesn't use GetLastError().
    else:
        _, pid = win32process.GetWindowThreadProcessId(hWnd)
        return psutil.Process(pid).exe()

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
        
        
        
def stateUpdate():
    counter = 0
    while running:
        sleep(0.1)
        counter += 1

        if counter%2 == 0:
            """
            Update every 2 seconds
            """
            TPClient.stateUpdate(TP_PLUGIN_STATES['FocusedAPP']['id'], pygetwindow.getActiveWindowTitle())

            TPClient.connectorUpdate(
                    f"{TP_PLUGIN_CONNECTORS['APP control']['id']}|{TP_PLUGIN_CONNECTORS['APP control']['data']['appchoice']['id']}=Master Volume",
                    getMasterVolume())

            activeWindow = getActiveExecutablePath()
            if activeWindow != "" and activeWindow != None and (current_app_volume := AudioController(os.path.basename(activeWindow)).process_volume()):
                TPClient.connectorUpdate(
                        f"{TP_PLUGIN_CONNECTORS['APP control']['id']}|{TP_PLUGIN_CONNECTORS['APP control']['data']['appchoice']['id']}=Current app",
                        int(current_app_volume*100.0))
            else:
                TPClient.connectorUpdate(
                        f"{TP_PLUGIN_CONNECTORS['APP control']['id']}|{TP_PLUGIN_CONNECTORS['APP control']['data']['appchoice']['id']}=Current app",
                        0)

            # TPClient.stateUpdate(TP_PLUGIN_STATES["outputDevice"]["id"], getDevicebydata(EDataFlow.eRender.value, ERole.eMultimedia.value))
            # TPClient.stateUpdate(TP_PLUGIN_STATES["outputcommicationDevice"]["id"], getDevicebydata(EDataFlow.eRender.value, ERole.eCommunications.value))

            # TPClient.stateUpdate(TP_PLUGIN_STATES["inputDevice"]["id"], getDevicebydata(EDataFlow.eCapture.value, ERole.eMultimedia.value))
            # TPClient.stateUpdate(TP_PLUGIN_STATES["inputDeviceCommication"]["id"], getDevicebydata(EDataFlow.eCapture.value, ERole.eCommunications.value))
            
            # g_log.info(str(getMasterVolume()))
        if counter >= 40: counter = 0; # clear ram because It could build really large number

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
        g_log.info(e)

    

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
        if action_data[0]['value'] == "Current app":
            activeWindow = getActiveExecutablePath()
            if activeWindow != "":
                volumeChanger(os.path.basename(activeWindow), action_data[1]['value'], action_data[2]['value'])
        else:
            volumeChanger(action_data[0]['value'], action_data[1]['value'], action_data[2]['value'])
    elif actionid == TP_PLUGIN_ACTIONS["ChangeOut/Input"]["id"] and action_data[0]['value'] != "Pick One": 
        for device in audioSwitch.MyAudioUtilities.getAllDevices(action_data[0]['value']):
            if device.FriendlyName == action_data[1]['value']:
                audioSwitch.switchOutput(device.id, dataMapper[action_data[2]['value']])

    else:
        g_log.warning("Got unknown action ID: " + actionid)

@TPClient.on(TP.TYPES.onHold_down)
def heldingButton(data):
    g_log.debug(f"heldingButton: {data}")
    while True:
        if TPClient.isActionBeingHeld(TP_PLUGIN_ACTIONS['Inc/DecrVol']['id']):
            volumeChanger(data['data'][0]['value'], data['data'][1]['value'], data['data'][2]['value'])
            sleep(0.05)
        else:
            break
    g_log.debug(f"Not helding button {data}")

@TPClient.on(TP.TYPES.onConnectorChange)
def connectors(data):
    g_log.debug(f"connector Change: {data}")
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
                g_log.debug(f"Exception in other app volume change Error: ", exc_info=e)

@TPClient.on(TP.TYPES.onListChange)
def onListChange(data):
    g_log.debug(f"onlistChange: {data}")
    if data['actionId'] == TP_PLUGIN_ACTIONS["ChangeOut/Input"]['id'] and data['listId'] == TP_PLUGIN_ACTIONS["ChangeOut/Input"]["data"]["optionSel"]["id"]:
        try:
            updateDevice(data['value'])
        except Exception as e:
            g_log.warning("Update device input/output KeyError", exc_info=e)

# Shutdown handler
@TPClient.on(TP.TYPES.onShutdown)
def onShutdown(data):
    g_log.info('Received shutdown event from TP Client.')

# Error handler
@TPClient.on(TP.TYPES.onError)
def onError(exc):
    g_log.error(f'Error in TP Client event handler: {repr(exc)}')

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
                print(f"Error while creating file logger, falling back to stdout. {repr(e)}")
        if not opts.l or opts.s:
            sh = StreamHandler(sys.stdout)
            sh.setFormatter(fmt)
            g_log.addHandler(sh)

    g_log.info(f"Starting {TP_PLUGIN_INFO['name']} v{__version__} on {sys.platform}.")

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
    sys.exit(main())
