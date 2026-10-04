{ writeShellApplication, hyprland, jq, coreutils, callPackage }:
let
  plugin = callPackage ./package.nix { inherit hyprland; };
in writeShellApplication {
  name = "neo-hyprglass";
  runtimeInputs = [ hyprland jq coreutils ];
  text = ''
    export NEO_HYPRGLASS_PACKAGE=${plugin}
    export NEO_HYPRGLASS_PRESET=${./preset.lua}
    ${builtins.readFile ./launcher.sh}
  '';
  passthru = { inherit plugin; };
}
