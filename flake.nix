{
  description = "Neo Blush: a reusable pink glass Hyprland desktop for NixOS";

  inputs = {
    stableBranch.url = "github:nixos/nixpkgs/nixos-26.05";
    home-manager = {
      url = "github:nix-community/home-manager/release-26.05";
      inputs.nixpkgs.follows = "stableBranch";
    };
  };

  outputs =
    { self, stableBranch, ... }:
    let
      inherit (stableBranch) lib;
      forAllSystems = lib.genAttrs [
        "x86_64-linux"
        "aarch64-linux"
      ];
      pkgsFor =
        system:
        import stableBranch {
          inherit system;
          config.allowUnfree = true;
        };
    in
    {
      nixosModules = {
        neo-blush = ./modules/neo-blush/nixos.nix;
        default = self.nixosModules.neo-blush;
      };
      homeManagerModules = {
        neo-blush = ./modules/neo-blush/home.nix;
        default = self.homeManagerModules.neo-blush;
      };
      templates = {
        desktop = {
          path = ./templates/desktop;
          description = "Neo Blush with your own NixOS account and hardware";
        };
        default = self.templates.desktop;
        neo-blush = self.templates.desktop;
      };
      packages = forAllSystems (
        system: import ./modules/neo-blush/packages.nix { pkgs = pkgsFor system; }
      );
      formatter = forAllSystems (system: (pkgsFor system).nixfmt);
    };
}
