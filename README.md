# OSCR-UI

[![PyPI version](https://badge.fury.io/py/OSCR-UI.svg)](https://badge.fury.io/py/OSCR-UI)

User Interface for the OSCR parser. 

# Companion Web Application

The STOCD team provides a companion web application for OSCR located at [oscr.stobuilds.com](https://oscr.stobuilds.com).
This allows users to view and download combat log data without OSCR installed, however uploads
and more detailed analysis of combat logs requires OSCR or a parser that supports
interracting with OSCR's backend such as [CLA](https://github.com/AnotherNathan/STO_CombatLogAnalyzer).

# Windows Users

For Windows users we have an installer available on the [Releases](https://github.com/STOCD/OSCR-UI/releases) page.

# Installation

## PyPI

```bash
python3 -m pip install OSCR-UI
```

#### Externally Managed Python Environments (Arch)
The recommended way is using `pipx` to install from PyPi without `--break-system-packages`, if you don't already have it, you can install it through pacman.
```bash
pacman -Sy python-pipx
pipx install OSCR-UI
```

## Github

```bash
python3 -m pip install git+https://github.com/STOCD/OSCR-UI.git
```

# Running

```bash
oscr
```

# Development

*It is recommended to use a python virtual environment to house this app.*

```bash
# Clone the repository
git clone https://github.com/STOCD/OSCR-UI.git
cd OSCR-UI

# Set up the virtual environment
virtualenv venv

# Windows
.\venv\Scripts\activate

# Linux
source ./venv/bin/activate

# Install OSCR + Requirements.
python3 -m pip install .
```
