{
  config,
  lib,
  pkgs,
  ...
}:
let
  launcher = pkgs.callPackage ./launcher.nix { };
in
{
  options.neo.hyprglass.enable = (lib.mkEnableOption "the optional HyprGlass plugin") // {
    default = lib.meta.availableOn pkgs.stdenv.hostPlatform launcher.plugin;
  };

  config = lib.mkIf config.neo.hyprglass.enable {
    home.packages = [ launcher ];
    home.file.".local/bin/neo-hyprglass".source = "${launcher}/bin/neo-hyprglass";
    home.file.".local/share/neo-hyprglass/preset.lua".source = ./preset.lua;
    systemd.user.services.neo-control-center.Service.ExecStartPost =
      "-${launcher}/bin/neo-hyprglass apply";
  };
}
