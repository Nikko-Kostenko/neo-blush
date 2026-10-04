{ lib, pkgs, ... }:
let
  clipboard = pkgs.writeShellApplication {
    name = "neo-clipboard";
    runtimeInputs = with pkgs; [ cliphist wl-clipboard rofi ];
    text = builtins.readFile ./clipboard.sh;
  };
  hyprctl = "${pkgs.hyprland}/bin/hyprctl";
  loginctl = "${pkgs.systemd}/bin/loginctl";
  brightnessctl = "${pkgs.brightnessctl}/bin/brightnessctl";
in {
  home.packages = [ clipboard ] ++ (with pkgs; [
    wl-clipboard
    libnotify
    satty
    loupe
    kdePackages.okular
    kdePackages.ark
    keepassxc
    pika-backup
    easyeffects
    btop
  ]);

  # These stable entry points also avoid older imperative Nix-profile helpers.
  home.file.".local/bin/neo-clipboard".source = "${clipboard}/bin/neo-clipboard";
  home.file.".local/bin/neo-screenshot".source =
    "${import ../neo/screenshot.nix { inherit pkgs; }}/bin/neo-screenshot";

  services.cliphist = {
    enable = true;
    allowImages = true;
    extraOptions = [ "-max-items" "200" ];
    systemdTargets = [ "graphical-session.target" ];
  };
  # Separate text and image watchers with the pinned wl-clipboard 2.3.0.
  systemd.user.services.cliphist.Service.ExecStart = lib.mkForce
    "${pkgs.wl-clipboard}/bin/wl-paste --type text --watch ${pkgs.cliphist}/bin/cliphist -max-items 200 store";

  services.swaync = {
    enable = true;
    settings = builtins.fromJSON (builtins.readFile ./notifications.json);
    style = ./notifications.css;
  };

  services.hypridle = {
    enable = true;
    settings = {
      general = {
        lock_cmd = "${pkgs.procps}/bin/pidof hyprlock || ${pkgs.hyprlock}/bin/hyprlock --no-fade-in";
        before_sleep_cmd = "${loginctl} lock-session";
        after_sleep_cmd = "${hyprctl} dispatch 'hl.dsp.dpms({ action = \"enable\" })'";
        inhibit_sleep = 3;
        ignore_dbus_inhibit = false;
        ignore_systemd_inhibit = false;
        ignore_wayland_inhibit = false;
      };
      listener = [
        {
          timeout = 150;
          on-timeout = "${brightnessctl} --class=backlight --save set 10%";
          on-resume = "${brightnessctl} --class=backlight --restore";
        }
        { timeout = 300; on-timeout = "${loginctl} lock-session"; }
        {
          timeout = 330;
          on-timeout = "${hyprctl} dispatch 'hl.dsp.dpms({ action = \"disable\" })'";
          on-resume = "${hyprctl} dispatch 'hl.dsp.dpms({ action = \"enable\" })'";
        }
        { timeout = 1800; on-timeout = "${pkgs.systemd}/bin/systemctl suspend"; }
      ];
    };
  };

  services.hyprsunset = {
    enable = true;
    settings.profile = [
      { time = "07:00"; identity = true; }
      { time = "20:00"; temperature = 4500; }
    ];
  };

  # Backup destinations and audio presets will be selected in their applications.
  xdg.configFile."satty/config.toml".text = ''
    [general]
    copy-command = "${pkgs.wl-clipboard}/bin/wl-copy --type image/png"
    initial-tool = "arrow"
    early-exit = true
    save-after-copy = true
    actions-on-enter = ["save-to-clipboard"]
  '';

  xdg.mimeApps = {
    enable = true;
    defaultApplications = {
      "application/pdf" = [ "org.kde.okular.desktop" ];
      "image/png" = [ "org.gnome.Loupe.desktop" ];
      "image/jpeg" = [ "org.gnome.Loupe.desktop" ];
      "image/webp" = [ "org.gnome.Loupe.desktop" ];
      "image/gif" = [ "org.gnome.Loupe.desktop" ];
      "image/tiff" = [ "org.gnome.Loupe.desktop" ];
      "application/zip" = [ "org.kde.ark.desktop" ];
      "application/x-7z-compressed" = [ "org.kde.ark.desktop" ];
      "application/x-tar" = [ "org.kde.ark.desktop" ];
      "application/gzip" = [ "org.kde.ark.desktop" ];
      "application/x-bzip-compressed-tar" = [ "org.kde.ark.desktop" ];
      "application/x-xz-compressed-tar" = [ "org.kde.ark.desktop" ];
    };
  };

  systemd.user.startServices = "sd-switch";
}
