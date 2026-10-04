{ lib, stdenvNoCC, python3, makeWrapper, wrapGAppsHook3,
  gobject-introspection, gtk3, gtk-layer-shell, adwaita-icon-theme, adwaita-icon-theme-legacy,
  networkmanager, networkmanagerapplet, bluez, blueman, brightnessctl,
  wireplumber, playerctl, pavucontrol, systemd, coreutils, hyprland }:

let
  python = python3.withPackages (ps: [ ps.pygobject3 ps.pycairo ]);
in stdenvNoCC.mkDerivation {
  pname = "neo-control-center";
  version = "1.3.1";
  src = lib.cleanSource ./.;
  nativeBuildInputs = [ makeWrapper wrapGAppsHook3 gobject-introspection ];
  buildInputs = [ gtk3 gtk-layer-shell adwaita-icon-theme adwaita-icon-theme-legacy ];
  dontBuild = true;
  passthru = { inherit python; };
  installPhase = ''
    runHook preInstall
    mkdir -p "$out/share/neo-control-center" "$out/bin"
    cp main.py backend.py style.css "$out/share/neo-control-center/"
    cp -r icons "$out/share/neo-control-center/"
    cp -r tests "$out/share/neo-control-center/"
    makeWrapper ${python}/bin/python3 "$out/bin/neo-control-center-run" \
        --add-flags "$out/share/neo-control-center/main.py" \
        --prefix XDG_DATA_DIRS : "${adwaita-icon-theme}/share:${adwaita-icon-theme-legacy}/share" \
        --prefix PATH : ${lib.makeBinPath [
          networkmanager networkmanagerapplet bluez blueman brightnessctl
          wireplumber playerctl pavucontrol systemd coreutils hyprland
        ]}
    # Toggle the resident panel over D-Bus without importing GTK again.
    cat > "$out/bin/neo-control-center" <<EOF
    #!${stdenvNoCC.shell}
    if [ "\$#" -eq 1 ] && { [ "\$1" = --dismiss ] || [ "\$1" = --escape ]; }; then
      action=dismiss
      if [ "\$1" = --escape ]; then action=escape; fi
      exec ${systemd}/bin/busctl --user --auto-start=no --timeout=1 \\
        call local.neo.ControlCenter /local/neo/ControlCenter \\
        org.freedesktop.Application ActivateAction 'sava{sv}' "\$action" 0 0
    fi
    if [ "\$#" -eq 0 ] && ${systemd}/bin/busctl --user --auto-start=no --timeout=1 \\
      call local.neo.ControlCenter /local/neo/ControlCenter \\
      org.freedesktop.Application Activate 'a{sv}' 0 >/dev/null 2>&1; then
      exit 0
    fi
    exec "$out/bin/neo-control-center-run" "\$@"
    EOF
    chmod +x "$out/bin/neo-control-center"
    mkdir -p "$out/share/systemd/user"
    cat > "$out/share/systemd/user/neo-control-center.service" <<EOF
    [Unit]
    Description=Native Neo Blush Control Center
    PartOf=graphical-session.target
    After=graphical-session.target
    [Service]
    ExecStartPre=${hyprland}/bin/hyprctl eval 'hl.layer_rule({ name = "control-center-native", match = { namespace = "^neo-control-center$" }, blur = true, blur_popups = true, ignore_alpha = 0.2, no_anim = true })'
    ExecStart=$out/bin/neo-control-center --daemon
    Restart=on-failure
    [Install]
    WantedBy=graphical-session.target
    EOF
    runHook postInstall
  '';
  meta.mainProgram = "neo-control-center";
}
