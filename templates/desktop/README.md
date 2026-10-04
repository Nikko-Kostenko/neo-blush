# Your Neo Blush desktop

1. Set your hostname in `flake.nix` and `configuration.nix`, your architecture
   in `flake.nix`, and your username in both files (the example uses `alice`).
2. Generate hardware configuration on the target machine:
   `sudo nixos-generate-config --show-hardware-config > hardware-configuration.nix`.
3. Copy your existing bootloader and extra hardware settings into
   `configuration.nix`. Preserve your original NixOS and Home Manager state versions.
4. Set your timezone. Customize displays in `neo-blush-home.nix` and the optional
   login photo in `neo-blush.nix`.
5. Run `nix flake check --no-build "path:$PWD"`, then
   `sudo nixos-rebuild test --flake "path:$PWD#my-pc"`.
6. Once the setup works, run
   `sudo nixos-rebuild switch --flake "path:$PWD#my-pc"` and log into Hyprland.

Use your chosen hostname in place of `my-pc`. Set a password for a new account
with `sudo passwd <username>`. The bootloader example assumes UEFI/systemd-boot.
When installing from live media, generate hardware with the correct `--root /mnt`.

Commit your configuration and `flake.lock` to keep it reproducible. Update the
shared theme with `nix flake update neo`, then validate and rebuild.
