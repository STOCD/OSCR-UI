# Maintainer: PsychedelicShayna <Eternal0000FF@protonmail.com>
pkgname=oscr-ui
pkgver=9.14.2
pkgrel=1
pkgdesc="OSCR-UI Open Source Combat Reader for Star Trek Online"
arch=('x86_64')
url="https://github.com/STOCD/OSCR-UI/"
license=('GPL-3.0')

# runtime deps are usually bundled by PyInstaller. Add here only if your app
# depends on system libs at runtime (e.g. qt libraries if you didn't bundle them).

depends=()
makedepends=('pyinstaller') # only if you plan to build from source in the PKGBUILD
source=()
sha256sums=('SKIP') # local package: skip checksum checks

# No build() step because we use an already-built PyInstaller tree in dist/OSCR-UI.
# Makepkg’s $srcdir points to the directory where you run makepkg (repo root).
#

build() {
  cd "${srcdir}"
  python -m venv .venv
  . .venv/bin/activate

  pip install --upgrade pip setuptools wheel
  pip install -e .

  pip install "pyinstaller==6.10.0"

  pyinstaller --noconfirm --clean --onedir --name OSCR-UI main.py \
    --add-data assets:assets --add-data locales:locales --windowed \
    -- icon assets/oscr_icon_small.png

  deactivate
}

package() {
  # where we will place files inside the package image
  install -d "${pkgdir}/opt/oscr-ui"
  install -d "${pkgdir}/usr/bin"
  install -d "${pkgdir}/usr/share/applications"
  install -d "${pkgdir}/usr/share/icons/hicolor/128x128/apps"

  # Copy PyInstaller one-dir output into /opt/oscr-ui
  if [ -d "${srcdir}/dist/OSCR-UI" ]; then
    cp -a "${srcdir}/dist/OSCR-UI/." "${pkgdir}/opt/oscr-ui/"
  else
    echo "ERROR: dist/OSCR-UI not found. Build the PyInstaller artifact first." >&2
    return 1
  fi

  # Ensure main binary is executable (PyInstaller normally does this)
  if [ -f "${pkgdir}/opt/oscr-ui/oscr-ui" ]; then
    chmod 755 "${pkgdir}/opt/oscr-ui/oscr-ui"
  fi

  # Wrapper launcher (placed in /usr/bin so users can run `oscr-ui`)
  cat > "${pkgdir}/usr/bin/oscr-ui" <<'EOF'
#!/bin/sh
exec /opt/oscr-ui/oscr-ui "$@"
EOF
  chmod 755 "${pkgdir}/usr/bin/oscr-ui"

  # .desktop file: prefer repo desktop/oscr-ui.desktop if present,
  # otherwise write a simple one that points to /usr/bin/oscr-ui
  if [ -f "${srcdir}/desktop/oscr-ui.desktop" ]; then
    install -Dm644 "${srcdir}/desktop/oscr-ui.desktop" "${pkgdir}/usr/share/applications/oscr-ui.desktop"
  else
    cat > "${pkgdir}/usr/share/applications/oscr-ui.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=OSCR-UI
Comment=STO combat log parser
Exec=/usr/bin/oscr-ui
Icon=oscr-ui
Terminal=false
Categories=Utility;Development;
EOF
  fi

  # Icon: try a few likely locations inside repo's assets/
  if [ -f "${srcdir}/assets/oscr_icon.png" ]; then
    install -Dm644 "${srcdir}/assets/oscr_icon.png" "${pkgdir}/usr/share/icons/hicolor/128x128/apps/oscr-ui.png"
  elif [ -f "${srcdir}/assets/oscr_icon_128.png" ]; then
    install -Dm644 "${srcdir}/assets/oscr_icon_128.png" "${pkgdir}/usr/share/icons/hicolor/128x128/apps/oscr-ui.png"
  elif [ -f "${srcdir}/assets/oscr_icon_small.png" ]; then
    install -Dm644 "${srcdir}/assets/oscr_icon_small.png" "${pkgdir}/usr/share/icons/hicolor/128x128/apps/oscr-ui.png"
  else
    # no icon found; not fatal — desktop environments will show a generic icon
    echo "Warning: no icon found in assets/ (optional)."
  fi
}
