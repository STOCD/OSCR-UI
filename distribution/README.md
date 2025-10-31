# Development Notes

These are currently just development notes, subject to change, easier to have it in one place.

## Windows
- [Currently Testing With Inno Setup](https://jrsoftware.org/isinfo.php)
  - [OSCR-UI.iss](./OSCR-UI.iss)

## Linux


#### System Wide Paths
- /opt/oscr/
  - This is the ideal loation for Linux, include all the assets there.
- /usr/local/bin/oscr -> /opt/bin/oscr/oscr
  - Symlink to the binary
- /usr/share/applications/
  - The `.desktop` entry that registers the application.
- /usr/share/icons/hicolor/128x128/apps/oscr-ui.png
  - Location for the application icon, referred to in the `.desktop` entry.

#### Config Paths
- 1 If `$XDG_CONFIG_HOME` is set, takes priority. Is supposed to be a directory . If a file, fallback to
- 2 `$HOME/.config` if the `.config` folder exists, but do not create it if it does not, fall back to:
- 3 `$HOME/.<filename>` if you can keep the settings in one file (and the dot here is important), if not, fall back to
- 4 ` $HOME/.oscr/<config-file>`

##### .desktop entry template
```
[Desktop Entry]
Type=Application
Name=OSCR-UI
Comment=OSCR combatlog parser for Star Trek Online
Exec=/opt/oscr-ui/oscr-ui
Icon=oscr-ui
Terminal=false
Categories=Utility;
```

#### Debian `.deb` Package Approach


```bash
apt install ./oscr-ui.deb
```
- Unpacks the contents to `/opt/oscr-ui`, `/usr/share/applications/oscr-ui.desktop`, etc
- Registers the package manager metadata with `dpkg` so the system becomes aware which files belong to which package
  - This is the biggest advantage.
- Allows uninstallation by name (apt remove oscr-ui), because it recorded which files it put there.

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
 
There might be equivalent apt commands but I don't remember them off the top of my head because I use primarily Arch. However it might not be necessary from what I've seen with `fpm` and how `.deb` files work? Unsure

