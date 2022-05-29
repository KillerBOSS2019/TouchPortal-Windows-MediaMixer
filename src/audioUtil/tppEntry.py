__version__ = "1.0"

PLUGIN_ID = "com.github.KillerBOSS2019.WinMediaMixer"

TP_PLUGIN_INFO = {
    'sdk': 6,
    'version': int(float(__version__) * 100),
    'name': "TouchPortal Windows Media Mixer",
    'id': PLUGIN_ID,
    'plugin_start_cmd': "%TP_PLUGIN_FOLDER%TouchPortalMediaMixer\\TPAudioMixer.exe",
    'configuration': {
        'colorDark': "#6c6f73",
        'colorLight': "#3d62ad"
    }
}

TP_PLUGIN_SETTINGS = {
    'ignore list': {
        'name': "Audio process ignore list",
        'type': "text",
        'default': "Enter '.exe' name seperated by a comma for more then 1",
        'readOnly': False,
        'value': None
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
        'format': "$[2] Program:$[1]",
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
        'name': 'Volume Mixer: Increase/Decrease process volume',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        'format': "$[2]$[1]Volume to$[3]",
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
                'type': "number",
                'label': "Volume",
                "allowDecimals": False,
                "minValue": 0,
                "maxValue": 100,
                "default": 10
            },
        }
    },
    'ChangeOut/Input': {
        # 'category' is optional, if omitted then this action will be added to all, or the only, category(ies)
        'category': "main",
        'id': PLUGIN_ID + ".act.ChangeAudioOutput",
        'name': 'Volume Mixer: Change Default Audio Devices',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        # 'format' tokens like $[1] will be replaced in the generated JSON with the corresponding data id wrapped with "{$...$}".
        # Numeric token values correspond to the order in which the data items are listed here, while text tokens correspond
        # to the last part of a dotted data ID (the part after the last period; letters, numbers, and underscore allowed).
        'format': "Set Audio $[1] $[2] to $[3]",
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
        'desc': "Audio Device: Get default Output commication devices",
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
        'desc': "Audio Device: Get default input commucation device",
        'default': ""
    },
    'FocusedAPP': {
        'category': "main",
        'id': PLUGIN_ID + ".state.currentFocusedAPP",
        'type': "text",
        'desc': "Volume Mixer: current focused app",
        'default': ""
    },
}