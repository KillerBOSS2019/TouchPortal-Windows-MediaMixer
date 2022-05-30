versionMajor = 1
versionMinor = 1
versionPatch = 0

__version__ = str(versionMajor * 1000 + versionMinor * 100 + versionPatch)

PLUGIN_MAIN = r"TPAudioMixer.py"
PLUGIN_EXE_NAME = "TPAudioMixer"

PLUGIN_ENTRY = r"tppEntry.py"
PLUGIN_ROOT = "TouchPortalMediaMixer"

PLUGIN_ICON = "icon-24.png"

FileRequired = []

Pyinstaller_arg = [
    f'{PLUGIN_MAIN}',
    f'--name={PLUGIN_EXE_NAME}',
    '--onefile',
    f'--distpath=./',
    f'--icon=icon.ico'
]