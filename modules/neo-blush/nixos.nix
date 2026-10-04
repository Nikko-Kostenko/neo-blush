# The optional Neo Blush desktop and its system services.
{ lib, pkgs, ... }:

{
  imports = [
    ../../sddm/neo-glass
    ../../config/qol/system.nix
  ];

  services.udisks2.enable = true;
  services.gvfs.enable = true;
  services.devmon.enable = true;
  hardware.bluetooth.enable = lib.mkDefault true;

  programs.hyprland = {
    enable = true;
    xwayland.enable = true;
  };
  programs.hyprlock.enable = true;

  services.xserver.xkb = {
    layout = lib.mkDefault "us";
    variant = lib.mkDefault "";
  };

  environment.systemPackages = with pkgs; [
    waybar
    kitty
    rofi
    brave
    hyprpaper
    uwsm
    hyprpolkitagent
  ];
}
