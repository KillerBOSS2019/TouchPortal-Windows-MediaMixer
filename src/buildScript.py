import importlib
import os
import sys
from zipfile import (ZipFile, ZIP_DEFLATED)
import PyInstaller.__main__
from argparse import ArgumentParser
from glob import glob
from shutil import rmtree
from TouchPortalAPI import sdk_tools
from typing import Union, TextIO
import json

def getInfoFromBuildScript(script:Union[str, TextIO]):
    script_str = ""
    if hasattr(script, "read"):
        script_str = script.read()
    elif not script.endswith(".py"):
        script_str = script

    try:
        if script_str:
            # load from a string
            spec = importlib.util.spec_from_loader("buildScript", loader=None)
            buildScript = importlib.util.module_from_spec(spec)
            setattr(buildScript, "__file__", os.path.join(os.getcwd(), "build.py"))
            exec(script_str, buildScript.__dict__)
        else:
            # load directly from a file path
            spec = importlib.util.spec_from_file_location("buildScript", script)
            buildScript = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(buildScript)
        # print(plugin.TP_PLUGIN_INFO)
    except Exception as e:
        input_name = "input stream" if script_str else script
        raise ImportError(f"ERROR while trying to import plugin code from '{input_name}': {repr(e)}")
    return buildScript

EXE_SFX = ".exe" if sys.platform == "win32" else ""

OS_WIN = 1
OS_MAC = 2

def build_clean():
	print("Cleaning up...")
	files = glob("*.spec")
	files.extend(["build", "__pycache__", "entry.tp"])
	for file in files:
		if os.path.exists(file):
			print("removing: " + file)
			if os.path.isfile(file):
				os.remove(file)
			elif os.path.isdir(file):
				rmtree(file)
	print("")

def build_tpp(zip_name, tpp_pack_list):
	print("Creating archive: " + zip_name)
	with ZipFile(zip_name, "w", ZIP_DEFLATED) as zf:
		for src, dest in tpp_pack_list.items():
			zf.write(src, dest + os.path.basename(src))
	print("")

def zip_dir(zf, path, base_path="./", recurse=True):
	relroot = os.path.abspath(os.path.join(path, os.pardir))
	for root, _, files in os.walk(path):
		zf.write(os.path.join(root, "."))
		for file in files:
			src = os.path.join(root, file)
			if os.path.isfile(src):
				dst = os.path.join(base_path, os.path.relpath(root, relroot), file)
				zf.write(src, dst)
			elif recurse and os.path.isdir(src):
				zip_dir(zf, src, base_path)

def build_distro(opsys, version, pluginname, packingList):
	os_name = "Windows" if opsys == OS_WIN else "MacOS"
	zip_name = pluginname + "_v" + version + "_" + os_name + ".tpp"
	print("Creating archive: "+ zip_name)
	with ZipFile(zip_name, "w", ZIP_DEFLATED) as zf:
		for src, dest in packingList.items():
			if os.path.isdir(src):
				zip_dir(zf, src, dest)
			elif os.path.isfile(src):
				zf.write(src, dest + os.path.basename(src))
	print("")

def build_clean():
	print("Cleaning up...")
	files = glob("./*.spec")
	files.extend(glob("./*.exe"))
	files.extend(["./build", "__pycache__"])
	for file in files:
		if os.path.exists(file):
			print("removing: " + file)
			if os.path.isfile(file):
				os.remove(file)
			elif os.path.isdir(file):
				rmtree(file)
	print("")

def main():
	if sys.platform == "win32":
		opsys = OS_WIN
	elif sys.platform == "darwin":
		opsys = OS_MAC
	else:
		return "Unsupported OS: " + sys.platform

	parser = ArgumentParser(description="buildScript automatically compile into exe, entry and package them into importable tpp file")

	parser.add_argument(
		"--target", metavar='<target>', required=True, nargs="*", type=str,
		help='target is target to a build file that contains some infomations about the plugin.' +
		'Using given infomation about the plugin, It will automatically build entry.tp (if given file is .py) and it will build the distro' +
		'based on what system your using.'
	)

	opts = parser.parse_args()
	del parser

	buildfile = getInfoFromBuildScript(opts.target[0])

	TPP_PACK_LIST = []


	__version__ = ""
	if "PLUGIN_ENTRY" and "PLUGIN_MAIN" and "PLUGIN_ROOT" and "Pyinstaller_arg" and "PLUGIN_EXE_NAME" and "PLUGIN_ICON" and "ENTRY_ICONPATH" and "FileRequired" in dir(buildfile):
		PLUGIN_ENTRY = buildfile.PLUGIN_ENTRY
		PLUGIN_MAIN = buildfile.PLUGIN_MAIN
		PLUGIN_ROOT = buildfile.PLUGIN_ROOT
		PLUGIN_EXE_NAME = buildfile.PLUGIN_EXE_NAME
		Pyinstaller_arg = buildfile.Pyinstaller_arg

		if "__version__" in dir(buildfile):
			__version__ = buildfile.__version__

		print(f"Building {PLUGIN_ROOT} v{__version__} target(s) on {sys.platform}\n")

		print(f"Compile {PLUGIN_MAIN} for {sys.platform}")

		PI_RUN = [PLUGIN_MAIN]
		PI_RUN.extend(Pyinstaller_arg)

		PyInstaller.__main__.run(PI_RUN)


		for file in buildfile.FileRequired:
			TPP_PACK_LIST[file.split("/")[-1]] = file.split("/")[0:-1]

		if PLUGIN_ENTRY.endswith(".py"):
			print("Generating entry.tp from " , PLUGIN_ENTRY)
			print(f"Generating entry.tp")
			generatedJson = sdk_tools.generateDefinitionFromScript(PLUGIN_ENTRY)
			with open("entry.tp", "w", encoding="utf-8") as f:
				json.dump(generatedJson, f, indent=4)

		TPP_PACK_LIST = {
			PLUGIN_MAIN.split(".py")[0] + EXE_SFX : PLUGIN_ROOT + "/",
			"entry.tp" if PLUGIN_ENTRY.endswith(".py") else PLUGIN_ENTRY: PLUGIN_ROOT + "/",
			buildfile.PLUGIN_ICON.split("/")[-1] : PLUGIN_ROOT + "/" if len(buildfile.PLUGIN_ICON.split("/")) == 1 else "".join(buildfile.PLUGIN_ICON.split("/")[0:-1])
		}
		
		build_distro(opsys, __version__, PLUGIN_EXE_NAME, TPP_PACK_LIST)

		build_clean()

	return 0

if __name__ == "__main__":
	sys.exit(main())