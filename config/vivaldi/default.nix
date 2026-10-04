{ lib, pkgs, ... }:
let
  neo = import ./package.nix { inherit pkgs; };
in
{
  home.packages = [ neo.package ];
  home.activation.vivaldiNeoAppearance = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${neo.apply}/bin/vivaldi-neo-apply --if-needed --skip-running
  '';
}
