{
  description = "My Neo Blush NixOS desktop";

  inputs = {
    neo.url = "github:Nikko-Kostenko/neo-blush";
    nixpkgs.follows = "neo/stableBranch";
    home-manager.follows = "neo/home-manager";
  };

  outputs =
    {
      nixpkgs,
      home-manager,
      neo,
      ...
    }:
    {
      nixosConfigurations.my-pc = nixpkgs.lib.nixosSystem {
        modules = [
          ./configuration.nix
          ./hardware-configuration.nix
          ./neo-blush.nix
          neo.nixosModules.default
          home-manager.nixosModules.home-manager
          {
            nixpkgs.hostPlatform = "x86_64-linux"; # Or "aarch64-linux".
            home-manager = {
              useGlobalPkgs = true;
              useUserPackages = true;
              backupFileExtension = "backup";
              users.alice.imports = [
                neo.homeManagerModules.default
                ./home.nix
                ./neo-blush-home.nix
              ];
            };
          }
        ];
      };
    };
}
