# OSCR-UI

[![PyPI version](https://badge.fury.io/py/OSCR-UI.svg)](https://badge.fury.io/py/OSCR-UI)

User Interface for the OSCR parser. 

# Windows Users

For Windows users we have pre-compiled standalone binaries available on the [Releases](https://github.com/STOCD/OSCR-UI/releases) page.
# Installation

## PyPI

```bash
python3 -m pip install OSCR-UI
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
