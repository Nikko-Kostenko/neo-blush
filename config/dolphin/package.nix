{ lib, symlinkJoin, runCommand, makeWrapper, python3, qt6Packages, kdePackages, whitesur-kde }:
let
  theme = runCommand "neo-dolphin-theme-1.0" { nativeBuildInputs = [ python3 ]; } ''
    mkdir -p "$out/NeoBlushDolphin"
    python ${./build-theme.py} ${whitesur-kde}/share/Kvantum/WhiteSur "$out/NeoBlushDolphin"
    cp ${./qt6ct.conf} "$out/qt6ct.conf"
    cp ${./dolphinui.rc} "$out/dolphinui.rc"
    cp ${./neo-dolphin.qss} "$out/neo-dolphin.qss"
    cp ${./configure.py} "$out/configure.py"
  '';
  assetPython = python3.withPackages (ps: [ ps.fonttools ]);
in symlinkJoin {
  name = "neo-dolphin-1.0";
  paths = [ kdePackages.dolphin ];
  nativeBuildInputs = [ makeWrapper ];
  postBuild = ''
    rm "$out/bin/dolphin"
    makeWrapper ${kdePackages.dolphin}/bin/dolphin "$out/bin/dolphin" \
      --set QT_QPA_PLATFORMTHEME qt6ct \
      --set QT_STYLE_OVERRIDE kvantum \
      --prefix QT_PLUGIN_PATH : "${qt6Packages.qtstyleplugin-kvantum}/lib/qt-6/plugins:${qt6Packages.qt6ct}/lib/qt-6/plugins" \
      --prefix XDG_DATA_DIRS : "${kdePackages.breeze-icons}/share"
    ln -s dolphin "$out/bin/neo-dolphin"
    makeWrapper ${assetPython}/bin/python3 "$out/bin/neo-dolphin-configure" \
      --add-flags "${theme}/configure.py ${theme}"
    ln -s ${theme} "$out/share/neo-dolphin"
    rm "$out/share/applications/org.kde.dolphin.desktop"
    cp ${kdePackages.dolphin}/share/applications/org.kde.dolphin.desktop "$out/share/applications/org.kde.dolphin.desktop"
    chmod u+w "$out/share/applications/org.kde.dolphin.desktop"
    substituteInPlace "$out/share/applications/org.kde.dolphin.desktop" \
      --replace-fail "Exec=dolphin" "Exec=$out/bin/dolphin"
  '';
  meta = kdePackages.dolphin.meta // {
    description = "Dolphin with the Neo Blush Finder-inspired Qt style";
    mainProgram = "dolphin";
  };
}
