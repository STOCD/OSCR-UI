#!/bin/sh
set -e
if [ ! -d  distribution ]
then
  echo "[Error] Start this script from the base folder of the application."
  exit
fi
if [ ! -d dist ] || [ ! -d "dist/OSCR-UI" ]
then
  echo "[Error] Build the app before attempting to package it."
  exit
fi

echo "[Info]  Creating .deb Package..."
PKGDIR="dist/deb-pkg"
PKGNAME="oscr-ui"

echo "[Info]  Creating temporary folder for packaging \"${PKGDIR}/\"."
mkdir -p "${PKGDIR}"

echo "[Info]  Cleaning \"${PKGDIR}/\" folder."
rm -rf "${PKGDIR}"/*

echo "[Info]  Copying base structure."
cp -r "distribution/DEBIAN" "${PKGDIR}"
echo "[Info]  Copying copyright information."
mkdir -p "${PKGDIR}/usr/share/doc/${PKGNAME}"
cp "distribution/debian/copyright" "${PKGDIR}/usr/share/doc/${PKGNAME}/copyright"
echo "[Info]  Copying changelog."
cp "distribution/debian/changelog" "${PKGDIR}/usr/share/doc/${PKGNAME}/changelog"
gzip -9 "${PKGDIR}/usr/share/doc/${PKGNAME}/changelog"

echo "[Info]  Copying app."
mkdir -p "${PKGDIR}/opt/${PKGNAME}"
cp -r "dist/OSCR-UI"/* "${PKGDIR}/opt/${PKGNAME}/"

echo "[Info]  Linking app binary."
mkdir -p "${PKGDIR}/usr/bin"
LAUNCHCOMMAND="\"/opt/${PKGNAME}/OSCR-UI\" \"\$@\""
cat > "${PKGDIR}/usr/bin/${PKGNAME}" <<EOF
#!/bin/sh
exec $LAUNCHCOMMAND
EOF

echo "[Info]  Copying app icon."
mkdir -p "${PKGDIR}/usr/share/icons/hicolor/256x256/apps"
cp "assets/oscr_icon_small.png" "${PKGDIR}/usr/share/icons/hicolor/256x256/apps/oscr-ui.png"

echo "[Info]  Copying desktop file."
mkdir -p "${PKGDIR}/usr/share/applications"
cp "distribution/oscr-ui.desktop" "${PKGDIR}/usr/share/applications/oscr-ui.desktop"

echo "[Info]  Building .deb package."
dpkg-deb -b "${PKGDIR}"
mv "${PKGDIR}.deb" "dist/${PKGNAME}.deb"

echo "[Info]  Done."
