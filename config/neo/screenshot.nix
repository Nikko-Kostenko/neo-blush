{ pkgs }:

pkgs.writeShellApplication {
  name = "neo-screenshot";
  runtimeInputs = with pkgs; [ coreutils grim slurp wl-clipboard satty libnotify ];
  text = builtins.readFile ./screenshot.sh;
}
