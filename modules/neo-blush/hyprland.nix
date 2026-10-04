# Display settings belong to the Neo Blush desktop layer.
{ config, lib, ... }:

let
  cfg = config.neo.hyprland;
  monitorType = lib.types.submodule {
    options = {
      output = lib.mkOption {
        type = lib.types.str;
        description = "Hyprland output name; an empty string matches unspecified displays.";
      };
      mode = lib.mkOption {
        type = lib.types.str;
        default = "preferred";
      };
      position = lib.mkOption {
        type = lib.types.str;
        default = "auto";
      };
      scale = lib.mkOption {
        type = lib.types.str;
        default = "auto";
      };
    };
  };
in
{
  options.neo.hyprland.monitors = lib.mkOption {
    type = lib.types.listOf monitorType;
    default = [ { output = ""; } ];
    description = "Per-machine monitor layout for the shared desktop.";
  };

  config.xdg.configFile."hypr/monitors.lua".text = lib.concatMapStringsSep "\n" (monitor: ''
    hl.monitor({
        output = ${builtins.toJSON monitor.output},
        mode = ${builtins.toJSON monitor.mode},
        position = ${builtins.toJSON monitor.position},
        scale = ${builtins.toJSON monitor.scale},
    })
  '') cfg.monitors;
}
