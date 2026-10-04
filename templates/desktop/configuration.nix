{
  networking.hostName = "my-pc";
  networking.networkmanager.enable = true;
  nix.settings.experimental-features = [
    "nix-command"
    "flakes"
  ];
  nixpkgs.config.allowUnfree = true;

  users.users.alice = {
    isNormalUser = true;
    extraGroups = [
      "wheel"
      "networkmanager"
    ];
  };

  # Copy your existing bootloader settings. These assume UEFI/systemd-boot.
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  time.timeZone = "Europe/London"; # Set your own timezone.
  # Preserve the version from your original NixOS installation.
  system.stateVersion = "26.05";
}
