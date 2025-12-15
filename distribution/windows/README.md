# Build and Packaging instructions for Windows
## Building
To build the app, first activate your virtual environment and install all dependencies.

While in the base directory of the project, run ```pyinstaller --noconfirm --clean --onedir --name OSCR-UI main.py --add-data assets:assets --add-data locales:locales --windowed --icon assets/oscr_icon_small.ico``` to build the app.

While in the base directory of the project, run ```iscc distribution\OSCR-UI.iss``` to package the app with [Inno Setup Installer](https://jrsoftware.org/isinfo.php). If the command `iscc` is not available, add the install location of the `iscc` executable to PATH or provide the full path to the executable.

The resulting installer will be placed into the `dist\OSCR-UI\` folder.
