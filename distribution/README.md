# Development Notes

These are currently reflecting the state of the app, but are subject ot change.

## Windows
- [Currently Testing With Inno Setup](https://jrsoftware.org/isinfo.php)
  - [OSCR-UI.iss](./OSCR-UI.iss)

## Linux

#### System Wide Paths
- /opt/oscr-ui/
  - This is the ideal loation for Linux, all assets are located here.
- /usr/bin/oscr-ui -> /opt/oscr-ui/OSCR-UI
  - shell script to execute the binary from a PATH location
- /usr/share/applications/oscr-ui.desktop
  - The `.desktop` entry that registers the application.
- /usr/share/icons/hicolor/256x256/apps/oscr-ui.png
  - Location for the application icon, referred to in the `.desktop` entry.

#### Config Paths
1. If `$XDG_CONFIG_HOME` is set, takes priority. Is supposed to be a directory. Don't use if it is a file. Don't create it if it doesn't exist.
2. `$HOME/.config` if the `.config` folder exists, but do not create it if it does not.
3. [`$HOME/.<filename>` if you can keep the settings in one file (and the dot here is important)] -> not used, because OSCR-UI requires a folder
4. ` $HOME/.oscr/<config-file>`

##### .desktop entry template
```
[Desktop Entry]
Type=Application
Name=OSCR-UI
Comment=OSCR combatlog parser for Star Trek Online
Exec=/opt/oscr-ui/OSCR-UI
Icon=/usr/share/icons/hicolor/256x256/apps/oscr-ui.png
Terminal=false
Categories=Utility;Scanning;GameTool;DataVisualization;
StartupWMClass=Open Source Combatlog Reader
```

#### Debian `.deb` Package Approach


```bash
apt install -f ./oscr-ui.deb
```
- Unpacks the contents to `/opt/oscr-ui`, `/usr/share/applications/oscr-ui.desktop`, etc
- Automatically registers the package manager metadata with `dpkg` so the system becomes aware which files belong to which package
  - This is the biggest advantage.
- Allows uninstallation by name (apt remove oscr-ui), because it recorded which files it put there.
  - Does not remove settings.
- uses `-f` flag to install dependencies

To check whether it was installed correctly: `apt list --installed oscr-ui`

Use `dpkg -L oscr-ui` to list registered files for OSCR-UI.

For `.deb`, `fpm` is the simplest route that could be integrated into GitHub workflows as well:

```
fpm -s dir -t deb -n oscr-ui -v v2025.9.14.1 \
    --description "Star Trek Online Combat Log Parser" \
    --license "GPL-3.0" \
    --url "https://github.com/STOCD/OSCR-UI.git" \
    /opt/oscr-ui=/opt/oscr-ui \
    /usr/local/bin/oscr-ui=/usr/local/bin/oscr-ui \
    /usr/share/applications/oscr-ui.desktop=/usr/share/applications/oscr-ui.desktop \
    /usr/share/icons/hicolor/128x128/apps/oscr-ui.png=/usr/share/icons/hicolor/128x128/apps/oscr-ui.png
```

FPM hadles metadata and compression, and spits out a `.deb` file ready to install with `apt` or `dpkg`


#### Arch `PKGBUILD` File Structure
###### Note: to public to AUR we need a PKGBUILD that builds from source, I will be working on two separate PKGBUILD files, prioritizing one that can be installed first from the repository pointing to static assets.

On Arch there is similar tools, but there is no standard format like `.deb`, rather it's usually jusst a compressed archive `oscr-ui.pkg.tar.ztbuilt` by a `PKGBUILD` script, which can then be fed into `pacman`/`paru`/`yay`/`dpkg`

##### PKGBUILD Template
*The following template is a draft and not actually used or completed.*
```
pkgname=oscr-ui
pkgver=2025.9.14.1
pkgrel=1
pkgdesc="Star Trek Online Combat Log Parser"
arch=('x86_64')
license=('MIT')
depends=('python')
provides=('oscr-ui')

# This is an AUR convention; packages often have a `-git` version which pulls the latest commit and builds from there, rather than from a published release. You choose one or the other.
conflicts=('oscr-ui-git') 

source=("oscr-ui-${pkgver}.tar.gz")

sha256sums=('SKIP') # Not necessary but I recommend we include checksums, and this script will have to be larger if we subnit to AUR for safety reasons. 

package() {
    install -Dm755 "dist/oscr-ui" "$pkgdir/opt/oscr-ui/oscr-ui"
    install -Dm644 "assets/icon.png" "$pkgdir/usr/share/icons/hicolor/128x128/apps/oscr-ui.png"
    install -Dm644 "oscr-ui.desktop" "$pkgdir/usr/share/applications/oscr-ui.desktop"
    ln -s /opt/oscr-ui/oscr-ui "$pkgdir/usr/local/bin/oscr-ui"
}
```

Is a minimal PKGBUILD file.  Then you run `makepkg -si` from the repository's directory, that contains the `PKGBUILD` file and that spits out the `oscr-ui-v2025.9.14.1.pkg.tar.zt` file, which can then be installed via pacman: 

```
sudo pacman -U /path/to/oscr-ui-1.0.0-1-x86_64.pkg.tar.zst
```

And `pacman -Qs oscr-ui` to confirm that it is registered, just as a sanity check.

For debugging `pacman -Ql oscr-ui` lists where everything registers under that package is located (the assets and `.desktop` files, to ensure the `PKGBUILD` file was defined properly)

