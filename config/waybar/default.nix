{ config, lib, pkgs, ... }:

let
  controlCenter = pkgs.callPackage ./control-center/package.nix { };
  dynamicIsland = pkgs.callPackage ./dynamic-island/package.nix { };
  menuBar = pkgs.callPackage ./menu-bar-package.nix { };
  barSettings = builtins.fromJSON (builtins.readFile ./config.json);
in
{
  programs.waybar = {
    enable = true;
    package = menuBar;
    # Hyprland already starts Waybar; avoid a second instance from systemd.
    systemd.enable = false;
    settings = [ (barSettings // {
      "custom/control" = barSettings."custom/control" // {
        "on-click-release" = "${config.home.homeDirectory}/.local/bin/neo-control-center";
      };
      "custom/island" = barSettings."custom/island" // {
        exec = "${dynamicIsland}/bin/neo-dynamic-island";
        "on-click-release" = "${dynamicIsland}/bin/neo-dynamic-island --action toggle";
        "on-click-right-release" = "${dynamicIsland}/bin/neo-dynamic-island --action controls";
        "on-scroll-up" = "${dynamicIsland}/bin/neo-dynamic-island --action louder";
        "on-scroll-down" = "${dynamicIsland}/bin/neo-dynamic-island --action quieter";
      };
      tray = barSettings.tray // {
        icons = lib.mapAttrs (_: value: builtins.replaceStrings [ "~/" ]
          [ "${config.home.homeDirectory}/" ] value) barSettings.tray.icons;
      };
    }) ];
    style = builtins.readFile ./style.css;
  };

  xdg.configFile."waybar/menus".source = ./menus;
  xdg.configFile."waybar/assets".source = ./assets;
  home.file.".local/bin/neo-control-center".source = "${controlCenter}/bin/neo-control-center";

  systemd.user.services.neo-control-center = {
    Unit = {
      Description = "Native Neo Blush Control Center";
      PartOf = [ "graphical-session.target" ];
      After = [ "graphical-session.target" ];
    };
    Service = {
      ExecStartPre = ''${pkgs.hyprland}/bin/hyprctl eval 'hl.layer_rule({ name = "control-center-native", match = { namespace = "^neo-control-center$" }, blur = true, blur_popups = true, ignore_alpha = 0.2, no_anim = true })' '';
      ExecStart = "${controlCenter}/bin/neo-control-center --daemon";
      Restart = "on-failure";
    };
    Install.WantedBy = [ "graphical-session.target" ];
  };

  fonts.fontconfig.enable = true;
  home.packages = [ controlCenter dynamicIsland ] ++ (with pkgs; [
    nunito
    inter
    nerd-fonts.jetbrains-mono
    brightnessctl
    pavucontrol
    networkmanagerapplet
    rofi
    blueman
    playerctl
  ]);
}
