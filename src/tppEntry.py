__version__ = 131

PLUGIN_ID = "com.github.KillerBOSS2019.WinMediaMixer"

TP_PLUGIN_INFO = {
    'sdk': 6,
    'version': __version__,
    'name': "TouchPortal Windows Media Mixer",
    'id': PLUGIN_ID,
    'plugin_start_cmd': "%TP_PLUGIN_FOLDER%TouchPortalMediaMixer\\TPAudioMixer.exe",
    'configuration': {
        'colorDark': "#6c6f73",
        'colorLight': "#3d62ad"
    },
    'doc': {
        "description": "This is an example plugin for Touch Portal. It demonstrates the basics of how to create a plugin, and how to communicate with Touch Portal.",
        "repository": "KillerBOSS2019:TouchPortal-Windows-MediaMixer",
        "Install": "1. Download .tpp file\n2. in TouchPortal gui click gear icon and select 'Import Plugin'\n3. Select the .tpp file\n4. Click 'Import'",
    }
}

TP_PLUGIN_SETTINGS = {
    'ignore list': {
        'name': "Audio process ignore list",
        'type': "text",
        'default': "Enter '.exe' name seperated by a comma for more then 1",
        'readOnly': False,
        'value': None,
        "doc": "A list of processes to ignore when searching for audio processes. This is useful if you have a process that is not an audio process, but is still playing audio. You can add the name of the process to this list and Touch Portal will ignore it when searching for audio processes."
    },
}

TP_PLUGIN_CATEGORIES = {
    "main": {
        'id': PLUGIN_ID + ".main",
        'name' : "Author: KillerBOSS",
        'imagepath' : "%TP_PLUGIN_FOLDER%TouchPortalMediaMixer\\icon-24.png"
    }
}

TP_PLUGIN_CONNECTORS = {
    "APP control": {
        "id": PLUGIN_ID + ".connector.APPcontrol",
        "name": "Volume Mixer: APP Volume slider",
        "format": "Control volume for $[1]",
        "label": "control app Volume",
        "data": {
            "appchoice": {
                "id": PLUGIN_ID + ".connector.APPcontrol.data.slidercontrol",
                "type": "choice",
                "label": "APP choice list for APP control slider",
                "default": "",
                "valueChoices": []
            }
        }
    }
}

TP_PLUGIN_ACTIONS = {
    'AppMute': {
        # 'category' is optional, if omitted then this action will be added to all, or the only, category(ies)
        'category': "main",
        'id': PLUGIN_ID + ".act.Mute/Unmute",
        'name': 'Volume Mixer: Mute/Unmute process volume',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        # 'format' tokens like $[1] will be replaced in the generated JSON with the corresponding data id wrapped with "{$...$}".
        # Numeric token values correspond to the order in which the data items are listed here, while text tokens correspond
        # to the last part of a dotted data ID (the part after the last period; letters, numbers, and underscore allowed).
        'format': "$[1]$[2]app",
        "doc": "Mute/Unmute process volume",
        'data': {
            'appChoice': {
                'id': PLUGIN_ID + ".act.Mute/Unmute.data.process",
                # "text" is the default type and could be omitted here
                'type': "choice",
                'label': "process list",
                'default': "",
                "valueChoices": []
                
            },
            'OptionList': {
                'id': PLUGIN_ID + ".act.Mute/Unmute.data.choice",
                'type': "choice",
                'label': "Option choice",
                'default': "Toggle",
                "valueChoices": [
                    "Mute",
                    "Unmute",
                    "Toggle"
                ]
            },
        }
    },
    'Inc/DecrVol': {
        # 'category' is optional, if omitted then this action will be added to all, or the only, category(ies)
        'category': "main",
        'id': PLUGIN_ID + ".act.Inc/DecrVol",
        'name': 'Adjust App Volume',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        'format': "$[2]$[1]volume$[3]",
        "doc": "Increase/Decrease process volume",
        "hasHoldFunctionality": True,
        'data': {
            'AppChoice': {
                'id': PLUGIN_ID + ".act.Inc/DecrVol.data.process",
                # "text" is the default type and could be omitted here
                'type': "choice",
                'label': "process list",
                'default': "",
                "valueChoices": []
                
            },
            'OptionList': {
                'id': PLUGIN_ID + ".act.Inc/DecrVol.data.choice",
                'type': "choice",
                'label': "Option choice",
                'default': "Increase",
                "valueChoices": [
                    "Increase",
                    "Decrease",
                    "Set"
                ]
            },
            'Volume': {
                'id': PLUGIN_ID + ".act.Inc/DecrVol.data.Volume",
                'type': "text",
                'label': "Volume",
                "default": "10"
            },
        }
    },
    'ChangeOut/Input': {
        # 'category' is optional, if omitted then this action will be added to all, or the only, category(ies)
        'category': "main",
        'id': PLUGIN_ID + ".act.ChangeAudioOutput",
        'name': 'Audio Output/Input Device Switcher',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        # 'format' tokens like $[1] will be replaced in the generated JSON with the corresponding data id wrapped with "{$...$}".
        # Numeric token values correspond to the order in which the data items are listed here, while text tokens correspond
        # to the last part of a dotted data ID (the part after the last period; letters, numbers, and underscore allowed).
        'format': "Change audio device$[1]$[2]$[3]",
        "doc": "Change Default Audio Devices",
        'data': {
            'optionSel': {
                'id': PLUGIN_ID + ".act.ChangeAudioOutput.choice",
                # "text" is the default type and could be omitted here
                'type': "choice",
                'label': "process list",
                'default': "Pick One",
                "valueChoices": [
                    "Output",
                    "Input"
                ]
                
            },
            'deviceOption': {
                'id': PLUGIN_ID + ".act.ChangeAudioOutput.data.device",
                'type': "choice",
                'label': "Device choice list",
                'default': "",
                "valueChoices": []
            },
            'setType': {
                'id': PLUGIN_ID + ".act.ChangeAudioOutput.setType",
                # "text" is the default type and could be omitted here
                'type': "choice",
                'label': "Set audio device type",
                'default': "Default",
                "valueChoices": [
                    "Default",
                    "Communications"
                ]
                
            },
        }
    },
    'AppAudioSwitch': {
        # 'category' is optional, if omitted then this action will be added to all, or the only, category(ies)
        'category': "main",
        'id': PLUGIN_ID + ".act.appAudioSwitch",
        'name': 'Individual App Audio Device switcher',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        'format': "Set$[1]$[3]device to$[2]",
        "doc": "Change indivdual app output/input devices.",
        'data': {
            'AppChoice': {
                'id': PLUGIN_ID + ".act.appAudioSwitch.data.process",
                'type': "choice",
                'label': "process list",
                'default': "",
                "valueChoices": []
                
            },
            'devicelist': {
                'id': PLUGIN_ID + ".act.appAudioSwitch.data.devices",
                'type': "choice",
                'label': "Device choice list",
                'default': "",
                "valueChoices": []
            },
            'deviceType': {
                'id': PLUGIN_ID + ".act.ChangeAudioOutput.deviceType",
                'type': "choice",
                'label': "device type",
                'default': "Pick One",
                "valueChoices": [
                    "Output",
                    "Input"
                ]
            },
        }
    }
}

TP_PLUGIN_STATES = {
    'outputDevice': {
        # 'category' is optional, if omitted then this state will be added to all, or the only, category(ies)
        'category': "main",
        'id': PLUGIN_ID + ".state.CurrentOutputDevice",
        # "text" is the default type and could be omitted here
        'type': "text",
        'desc': "Audio Device: Get default Output devices",
        # we can conveniently use a value here which we already defined above
        'default': ""
    },
    'outputcommicationDevice': {
        # 'category' is optional, if omitted then this state will be added to all, or the only, category(ies)
        'category': "main",
        'id': PLUGIN_ID + ".state.CurrentOutputCommicationDevice",
        # "text" is the default type and could be omitted here
        'type': "text",
        'desc': "Audio Device: Get default Output Communications devices",
        # we can conveniently use a value here which we already defined above
        'default': ""
    },
    'inputDevice': {
        'category': "main",
        'id': PLUGIN_ID + ".state.CurrentInputDevice",
        'type': "text",
        'desc': "Audio Device: Get default input device",
        'default': ""
    },
    'inputDeviceCommication': {
        'category': "main",
        'id': PLUGIN_ID + ".state.CurrentInputCommucationDevice",
        'type': "text",
        'desc': "Audio Device: Get default input Communications device",
        'default': ""
    },
    'FocusedAPP': {
        'category': "main",
        'id': PLUGIN_ID + ".state.currentFocusedAPP",
        'type': "text",
        'desc': "Volume Mixer: current focused app",
        'default': ""
    },
    'master volume': {
        'category': "main",
        'id': PLUGIN_ID + ".state.currentMasterVolume",
        'type': "text",
        'desc': "Volume Mixer: Get Current Master volume",
        'default': "0"
    }
}