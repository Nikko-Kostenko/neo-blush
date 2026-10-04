{ pkgs }:
let
  gtkTheme = pkgs.runCommand "vivaldi-neo-gtk" { } ''
    mkdir -p "$out/share/themes/NeoBlushBrowser/gtk-3.0"
    cp ${./gtk.css} "$out/share/themes/NeoBlushBrowser/gtk-3.0/gtk.css"
  '';
  fontConfig = pkgs.writeText "vivaldi-neo-fonts.conf" ''
    <?xml version="1.0"?>
    <!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
    <fontconfig>
      <include ignore_missing="yes">/etc/fonts/fonts.conf</include>
      <match target="pattern">
        <test name="family" qual="any"><string>sans-serif</string></test>
        <edit name="family" mode="prepend_first" binding="strong">
          <string>SF Pro Text</string>
        </edit>
      </match>
    </fontconfig>
  '';
  browser = pkgs.vivaldi.overrideAttrs (old: {
    # Include UI CSS in each immutable browser build. No runtime JS injection or
    # experimental flags are needed; upstream's native controls remain intact.
    postInstall = (old.postInstall or "") + ''
      install -m644 ${./neo-blush.css} "$out/opt/vivaldi/resources/vivaldi/neo-blush.css"
      ui_entry="$out/opt/vivaldi/resources/vivaldi/window.html"
      if [ ! -f "$ui_entry" ]; then
        ui_entry="$out/opt/vivaldi/resources/vivaldi/browser.html"
      fi
      substituteInPlace "$ui_entry" \
        --replace-fail '</head>' '<link rel="stylesheet" href="neo-blush.css" /></head>'
    '';
  });
  apply = pkgs.writeShellApplication {
    name = "vivaldi-neo-apply";
    runtimeInputs = [ pkgs.python3 ];
    text = ''
      exec python3 ${./apply.py} \
        --resources ${browser}/opt/vivaldi/resources/vivaldi \
        --theme ${./theme.json} --symbols ${./symbols.json} "$@"
    '';
  };
  launcher = pkgs.writeShellApplication {
    name = "vivaldi-neo";
    text = ''
      ${apply}/bin/vivaldi-neo-apply --if-needed --skip-running
      export GTK_THEME=NeoBlushBrowser:light
      export FONTCONFIG_FILE=${fontConfig}
      export XDG_DATA_DIRS="${gtkTheme}/share:''${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
      if [[ -n "''${HYPRLAND_INSTANCE_SIGNATURE:-}" ]] && command -v hyprctl >/dev/null; then
        hyprctl eval 'hl.config({decoration = {blur = {popups = true, popups_ignorealpha = 0.05}}})' >/dev/null || true
      fi
      exec ${browser}/bin/vivaldi "$@"
    '';
  };
  desktop = pkgs.makeDesktopItem {
    name = "vivaldi-neo";
    desktopName = "Vivaldi · Neo Blush";
    genericName = "Web Browser";
    comment = "Pink glass browser with SF Pro and Apple symbols";
    exec = "${launcher}/bin/vivaldi-neo %U";
    icon = "vivaldi";
    categories = [ "Network" "WebBrowser" ];
    mimeTypes = [ "text/html" "application/xhtml+xml" "x-scheme-handler/http" "x-scheme-handler/https" ];
    startupWMClass = "vivaldi-stable";
  };
  package = pkgs.symlinkJoin {
    name = "vivaldi-neo-${browser.version}";
    paths = [ launcher apply browser ];
    postBuild = ''
      rm "$out/bin/vivaldi"
      ln -s ${launcher}/bin/vivaldi-neo "$out/bin/vivaldi"
      rm -f "$out/share/applications/vivaldi.desktop" "$out/share/applications/vivaldi-stable.desktop"
      ln -s ${desktop}/share/applications/vivaldi-neo.desktop "$out/share/applications/vivaldi-neo.desktop"
    '';
    meta = browser.meta // { mainProgram = "vivaldi-neo"; };
  };
in
{ inherit browser apply launcher package; }
