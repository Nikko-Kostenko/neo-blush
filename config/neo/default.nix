{ pkgs, ... }:

let
  screenshot = import ./screenshot.nix { inherit pkgs; };
  wallpaper = pkgs.writeShellApplication {
    name = "neo-wallpaper";
    runtimeInputs = with pkgs; [ curl coreutils hyprpaper ];
    text = builtins.readFile ./wallpaper.sh;
  };
  session = pkgs.writeShellApplication {
    name = "neo-session";
    runtimeInputs = with pkgs; [ rofi systemd hyprland hyprlock ];
    text = builtins.readFile ./session.sh;
  };
in
{
  home.packages = [ wallpaper session screenshot ];
  xdg.configFile."rofi".source = ../rofi;
}
