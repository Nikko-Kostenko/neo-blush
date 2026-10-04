{ lib, pkgs, ... }:
let
  package = pkgs.callPackage ./package.nix { };
in {
  home.packages = [ package ];
  home.file.".local/bin/neo-dolphin".source = "${package}/bin/neo-dolphin";
  home.activation.neoDolphinStyle = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${package}/bin/neo-dolphin-configure
  '';
}
