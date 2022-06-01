import os

"""
                Versioning system (https://semver.org/)

MAJOR version when you make incompatible API changes,
MINOR version when you add functionality in a backwards compatible manner, and
PATCH version when you make backwards compatible bug fixes.

"This just a guide that helps you with your plugin version System. feel free to follow it or not."
"""
versionMajor = 1
versionMinor = 1
versionPatch = 1

"""
This will convert version from above into TP version eg
if Major 1, Minor 0, and Patch 0 output would be 10000 and if you change Minor to 1 it would be 1100 etc..
"""
__version__ = versionMajor * 10000 + versionMinor * 100 + versionPatch

"""
PLUGIN_MAIN: This let tppbuild to know where is your main python located so then It will know which file to compile
PLUGIN_EXE_NAME: This tells what you want your plugin to be named. as a note tppbuild will use this format `pluginname + "_v" + version + "_" + os_name + ".tpp"`
                 IF this is empty It will use main py name
PLUGIN_EXE_ICON: This should be a path to a .ico file that's used for the compiled exe icon (IF Leaved empty It will use default pyinstaller icon)
"""
PLUGIN_MAIN = r"TPAudioMixer.py"
PLUGIN_EXE_NAME = "TPAudioMixer"
PLUGIN_EXE_ICON = r"icon.ico"


"""
PLUGIN_ENTRY: This can be either path to entry.tp or path to a python file that contains infomation about entry.
Note if you pass in a entry.tp tppbuild will automatically validate the json. but if you pass in python file it will
build entry.tp & validate it for you.
"""
PLUGIN_ENTRY = r"tppEntry.py"
PLUGIN_ROOT = "TouchPortalMediaMixer" # This is the root folder name that's inside of .tpp
PLUGIN_ICON = r"icon-24.png" # This should be a path that goes to a icon that's for entry.tp
OUTPUT_PATH = r"./output" # This tells tppbuild where you want finished build tpp to be saved at. Default ./ meaning current dir build script


"""
If you have any required file that your plugin needs put it in here. In a list
"""
FileRequired = []


"""
This is args thats used by Pyinstaller. NOT RECOMMENDED TO MODIFY THIS. unless you know what your doing.
"""
Pyinstaller_arg = [
    f'{PLUGIN_MAIN}',
    f'--name={PLUGIN_EXE_NAME if PLUGIN_EXE_NAME != "" else os.path.basename(PLUGIN_MAIN)[:os.path.basename(PLUGIN_MAIN).find(".py")]}',
    '--onefile',
    f'--distpath=./',
    "--clean"
]
if PLUGIN_EXE_ICON and os.path.isfile(PLUGIN_EXE_ICON): # This just checks if it can find the exe icon. if not It won't use it. Please double check the path
    Pyinstaller_arg.append(f"--icon={PLUGIN_EXE_ICON}")