{ pkgs }:

let
  hyprglass = pkgs.callPackage ../../config/hyprglass/launcher.nix { };
in
{
  neo-screenshot = import ../../config/neo/screenshot.nix { inherit pkgs; };
  neo-notification-settings = pkgs.callPackage ../../config/qol/notification-settings/package.nix { };
  vivaldi-neo = (import ../../config/vivaldi/package.nix { inherit pkgs; }).package;
  vivaldi-neo-asset-tools = pkgs.python3.withPackages (ps: [ ps.fonttools ]);
  neo-files = pkgs.callPackage ../../config/files/package.nix { };
  neo-dolphin = pkgs.callPackage ../../config/dolphin/package.nix { };
  neo-control-center = pkgs.callPackage ../../config/waybar/control-center/package.nix { };
  neo-dynamic-island = pkgs.callPackage ../../config/waybar/dynamic-island/package.nix { };
  neo-waybar = pkgs.callPackage ../../config/waybar/menu-bar-package.nix { };
  neo-python = pkgs.python3;
}
// pkgs.lib.optionalAttrs (pkgs.lib.meta.availableOn pkgs.stdenv.hostPlatform hyprglass.plugin) {
  neo-hyprglass = hyprglass;
}
