# uScope

This folder contains the source to the uScope ('micro-scope'), a real-time serial data scope for micropython boards.

## How to use

Run the packaged .exe or from source (see *getting started*). Select the COM port on which data is being sent (this should be different from the REPL port) and click connect.  
Use the 'Save' button to make exports, or right-click on a plot to make a singular export.

If the applications starts to lag or even crash after conneting, try increasing the render frames value to slow down graph rendering.

## PyQt 5

The GUI is made in PyQt5 (https://build-system.fman.io/pyqt5-tutorial). Development is done from a virtual environment.
This environment is not committed to the repository.

## Getting started

* In the root of this directory, run `python3 -m venv venv` to create a virtual environment called 'venv'.
* In a terminal, activate this environment by running `source venv/Scripts/activiate` (Linux), `source venv/Scripts/activiate.bat`
(Windows CMD) or `venv/Scripts/Activate.ps1` (Windows PowerShell). The latter is recommended for Windows.

You should now see "(venv) $" at the start of your command line.

* Prepare the environment by running `pip install --upgrade pip` followed by `pip install -r requirements.txt`.
* Now run the program: `python3 main.py`.

You can also easily set up an IDE like Pycharm to use this virtual environment.

This virtual environment allows you to install packages and change settings without affecting your
global installation.

## Building Executable

Install the pyinstaller module first: `python -m pip install pyinstaller`.  
Generate an executable by running `pyinstaller main.spec` from inside the virtual environment. The `main.spec` file is used for configuration. The executable can be found in `dist/*`.