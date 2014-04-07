Shatter
=======

Python based "VOIP" with optional Skype integration

Building
========

``python build.py`` will build a windows executable and compress it into a .zip file.
Useful when you need others to join the debugging and you can't bother with guiding them to install Python and set up environment variables ;)

Usage
=====

As of now, the main file is called ``gui.py``, simply run it via ``python gui.py`` and you should be prompted with a login-window. 

Requirements
============

* Python2+ ([Pref 3+](https://www.python.org/downloads/release/python-340/))
* [Pyglet](https://pyglet.googlecode.com/files/pyglet-1.2alpha1.zip) (code.google.com)
* [PyAudio](http://people.csail.mit.edu/hubert/pyaudio/#downloads)


TODO's
======
(There's always todos....)

* Replace the threaded sound-output to work in a single-threaded manner
* Re-use ``main()`` instead of using a second GUI class (``chatWindow()``)
* Better socket transfer, the initial code was quick and dirty and was based on every packet being ``4096`` bytes which is fine, but create troubles when sending over files and what not. Until a protocol strategy is set up however this is the way the data will be transferred.
* Create more unicorns.. This project really needs more of those..
