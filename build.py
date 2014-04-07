import sys, os, zipfile, shutil
from cx_Freeze import setup, Executable

os.remove('shatter.zip')

def zipdir(path, zip):
	for root, dirs, files in os.walk(path):
		for file in files:
			zip.write(os.path.join(root, file))

exe = Executable(
	script="gui.py",
	base="Win32GUI",
	targetName="Shatter.exe")
setup(
	name="Shatter.exe",
	version="0.1",
	author="Anton Hvornum",
	description="Copyright 2014-",
	executables=[exe],
	scripts=[],
	options={'build_exe' : {
							'include_msvcr' : True,
							'include_files' : ['./data/',],
							"packages" : ["pyglet", "pyglet.gl", "pyaudio", "os"],
							"excludes" : ["tkinter"],
							'compressed' : True,
							'copy_dependent_files' : True,
							'create_shared_zip' : True,
							'include_in_shared_zip' : True,
							'optimize' : 2
							}}
	)

os.rename('./build/exe.win32-3.3', './build/shatter')
zipf = zipfile.ZipFile('shatter.zip', 'w')
os.chdir('./build/')
zipdir('shatter/', zipf)
zipf.close()
os.chdir('../')
shutil.rmtree('./build')