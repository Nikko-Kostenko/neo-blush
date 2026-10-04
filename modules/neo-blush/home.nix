{ lib, pkgs, ... }:

{
  imports = [
    ./hyprland.nix
    ../../config/waybar
    ../../config/neo
    ../../config/brave
    ../../config/vivaldi
    ../../config/hyprglass
    ../../config/dolphin
    ../../config/files
    ../../config/qol
  ];

  home.pointerCursor = {
    enable = true;
    package = pkgs.whitesur-cursors;
    name = "WhiteSur-cursors";
    size = 24;
    gtk.enable = true;
    x11.enable = true;
    dotIcons.enable = false; # ~/.icons already points at ~/.local/share/icons.
  };
  gtk.enable = true;
  programs.fastfetch.enable = lib.mkDefault true;
  home.sessionVariables = {
    XCURSOR_THEME = "WhiteSur-cursors";
    XCURSOR_SIZE = "24";
  };
  home.file.".local/lib/hyprland/plugins/dynamic-cursors.so".source =
    "${pkgs.hyprlandPlugins.hypr-dynamic-cursors}/lib/libhypr-dynamic-cursors.so";

  xdg.configFile = {
    "fastfetch/config.jsonc".source = ../../config/fastfetch/config.jsonc;
    "fastfetch/nixos-trans.txt".source = ../../config/fastfetch/nixos-trans.txt;
  };
  xdg.dataFile."TelegramDesktop/Neo-Blush.tdesktop-theme".source =
    ../../config/telegram/Neo-Blush.tdesktop-theme;

  # wayland.windowManager.hyprland.systemd.enable = false;
  home.packages = [ pkgs.telegram-desktop ];

  home.file = {
    ".config/hypr" = {
      source = ../../config/hypr;
      recursive = true; # Allow Home Manager to add idle/night-light configuration.
    };
    ".config/kitty".source = ../../config/kitty;
  };

}
