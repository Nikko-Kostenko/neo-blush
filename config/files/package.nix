{ lib, stdenv, pkg-config, gtk3, symlinkJoin, runCommand, makeWrapper, python3, thunar, xfconf, tumbler, adwaita-icon-theme, kdePackages }:
let
  settingsModule = runCommand "neo-files-gtk-settings" {
    nativeBuildInputs = [ stdenv.cc pkg-config ];
    buildInputs = [ gtk3 ];
  } ''
    mkdir -p "$out/lib"
    cc -shared -fPIC -O2 ${./settings.c} -o "$out/lib/neo-files-settings.so" $(pkg-config --cflags --libs gtk+-3.0)
  '';
  theme = runCommand "neo-files-theme-1.0" { } ''
    mkdir -p "$out/share/themes/NeoBlushFiles/gtk-3.0"
    cp ${./gtk.css} "$out/share/themes/NeoBlushFiles/gtk-3.0/gtk.css"
    mkdir -p "$out/share/neo-files"
    cp ${./configure.py} "$out/share/neo-files/configure.py"
  '';
  assetPython = python3.withPackages (ps: [ ps.fonttools ]);
in symlinkJoin {
  name = "neo-files-1.0";
  paths = [ thunar theme ];
  nativeBuildInputs = [ makeWrapper ];
  postBuild = ''
    rm "$out/bin/thunar"
    makeWrapper ${thunar}/bin/thunar "$out/bin/thunar" \
      --set GTK_THEME NeoBlushFiles \
      --prefix GTK_MODULES : "${settingsModule}/lib/neo-files-settings.so" \
      --prefix XDG_DATA_DIRS : "${theme}/share:${adwaita-icon-theme}/share:${kdePackages.breeze-icons}/share"
    ln -s thunar "$out/bin/neo-files"
    makeWrapper ${assetPython}/bin/python3 "$out/bin/neo-files-configure" \
      --add-flags "${theme}/share/neo-files/configure.py" \
      --set NEO_FILES_XFCONF "${xfconf}/bin/xfconf-query"
    mkdir -p "$out/share/neo-files"
    ln -s ${xfconf}/share/systemd/user/xfconfd.service "$out/share/neo-files/xfconfd.service"
    ln -s ${xfconf}/share/dbus-1/services/org.xfce.Xfconf.service "$out/share/neo-files/org.xfce.Xfconf.service"
    ln -s ${tumbler}/share/systemd/user/tumblerd.service "$out/share/neo-files/tumblerd.service"
    for service in ${tumbler}/share/dbus-1/services/*.service; do
      ln -s "$service" "$out/share/neo-files/$(basename "$service")"
    done
    rm "$out/share/applications/thunar.desktop"
    cp ${thunar}/share/applications/thunar.desktop "$out/share/applications/thunar.desktop"
    chmod u+w "$out/share/applications/thunar.desktop"
    substituteInPlace "$out/share/applications/thunar.desktop" \
      --replace-fail "Exec=thunar" "Exec=$out/bin/thunar" \
      --replace-fail "Name=Thunar File Manager" "Name=Files"
  '';
  meta = thunar.meta // {
    description = "Native Thunar with the Neo Blush glass theme";
    mainProgram = "neo-files";
  };
}
