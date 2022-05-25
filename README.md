# Biomechatronics Scope

[![CodeFactor](https://www.codefactor.io/repository/bitbucket/ctw-bw/uscope/badge)](https://www.codefactor.io/repository/bitbucket/ctw-bw/uscope)

This is a fork from [**uScope**](../../../uscope).

The Biomechatronics Scope is used to visualize EMG signals and a neural-muscular model.

Use in combination with the Biomechatronics MCU firmware: https://github.com/RobertoRoos/Biomechatronics-MCU  
The firmware is made for the K64F.

## User Code

Use the `model/` directory for the user code of students.  
See [model/README.md](model/README.md). 

## How to use

Run the packaged .exe or from source (see *getting started*). Select the COM port on which data is being sent (this should be different from the REPL port) and click connect.  
Use the 'Save' button to make exports, or right-click on a plot to make a singular export.

## PyQt 5

The GUI is made in PyQt5 (https://build-system.fman.io/pyqt5-tutorial). Development is done from a virtual environment.
This environment is not committed to the repository.

## Getting started

* In the root of this directory, run `python -m venv venv` to create a virtual environment called 'venv'.
* In a terminal, activate this environment by running `source venv/bin/activiate` (Linux), `source venv/Scripts/activiate.bat`
(Windows CMD) or `venv/Scripts/Activate.ps1` (Windows PowerShell). The latter is recommended for Windows.

You should now see "(venv) $" at the start of your command line.  
With Windows Powershell you might get an error about the script not being allowed. You need to change the execution policy, see for example: https://www.stanleyulili.com/powershell/solution-to-running-scripts-is-disabled-on-this-system-error-on-powershell/

* Prepare the environment by running `pip install -r requirements.txt`.
* Now run the program: `python main.py`.

You can also easily set up an IDE like Pycharm to use this virtual environment.

This virtual environment allows you to install packages and change settings without affecting your global installation.

## Building Executable

Install the pyinstaller module first: `python -m pip install pyinstaller`.  
Generate an executable by running `pyinstaller main.spec` from inside the virtual environment. The `main.spec` file is used for configuration. The executable can be found in `dist/*`.