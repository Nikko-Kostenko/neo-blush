{
  config,
  lib,
  pkgs,
  ...
}:
let
  package = pkgs.callPackage ./package.nix { };
  styleMarker = "${config.xdg.stateHome}/neo-files/configured";
  configureStyle = pkgs.writeShellScript "neo-files-style" ''
    set -eu
    ${package}/bin/neo-files-configure
    ${pkgs.coreutils}/bin/mkdir -p ${lib.escapeShellArg "${config.xdg.stateHome}/neo-files"}
    ${pkgs.coreutils}/bin/touch ${lib.escapeShellArg styleMarker}
  '';
in
{
  home.packages = [
    package
    pkgs.tumbler
  ];
  home.file.".local/bin/neo-files".source = "${package}/bin/neo-files";
  xdg.dataFile."dbus-1/services/org.xfce.Xfconf.service".source =
    "${pkgs.xfconf}/share/dbus-1/services/org.xfce.Xfconf.service";
  xdg.dataFile."dbus-1/services/org.xfce.Tumbler.Thumbnailer1.service".source =
    "${pkgs.tumbler}/share/dbus-1/services/org.xfce.Tumbler.Thumbnailer1.service";
  xdg.dataFile."dbus-1/services/org.xfce.Tumbler.Manager1.service".source =
    "${pkgs.tumbler}/share/dbus-1/services/org.xfce.Tumbler.Manager1.service";
  xdg.dataFile."dbus-1/services/org.xfce.Tumbler.Cache1.service".source =
    "${pkgs.tumbler}/share/dbus-1/services/org.xfce.Tumbler.Cache1.service";
  systemd.user.services.xfconfd = {
    Unit.Description = "Xfce file-manager preferences";
    Service = {
      Type = "dbus";
      BusName = "org.xfce.Xfconf";
      ExecStart = "${pkgs.xfconf}/lib/xfce4/xfconf/xfconfd";
    };
  };
  systemd.user.services.tumblerd = {
    Unit.Description = "File thumbnail previews";
    Service = {
      Type = "dbus";
      BusName = "org.freedesktop.thumbnails.Thumbnailer1";
      ExecStart = "${pkgs.tumbler}/lib/tumbler-1/tumblerd";
    };
  };
  # A newly created account may have no user bus during the first rebuild.
  # Finish setup at its first graphical login instead of failing activation.
  systemd.user.services.neo-files-style = {
    Unit = {
      Description = "Initial Neo Blush file-manager setup";
      After = [
        "graphical-session.target"
        "xfconfd.service"
      ];
      Requires = [ "xfconfd.service" ];
      ConditionPathExists = "!${styleMarker}";
    };
    Service = {
      Type = "oneshot";
      ExecStart = "${configureStyle}";
    };
    Install.WantedBy = [ "graphical-session.target" ];
  };
  xdg.mimeApps = {
    enable = true;
    defaultApplications."inode/directory" = [ "thunar.desktop" ];
  };
  home.activation.neoFilesStyle = lib.hm.dag.entryAfter [ "reloadSystemd" ] ''
    if ${pkgs.systemd}/bin/busctl --user --no-pager list >/dev/null 2>&1; then
      run ${pkgs.systemd}/bin/busctl --user call org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus ReloadConfig
      run ${pkgs.systemd}/bin/systemctl --user start xfconfd.service
      run ${configureStyle}
    else
      printf '%s\n' 'File-manager setup will finish at the first graphical login.'
    fi
  '';
}
