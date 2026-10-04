{ lib, pkgs, ... }:

let
  applyAppearance = pkgs.writeShellApplication {
    name = "brave-neo-apply";
    runtimeInputs = [ pkgs.python3 ];
    text = ''
      exec python3 ${./apply.py} --settings ${./appearance.json} "$@"
    '';
  };
  launcher = pkgs.writeShellApplication {
    name = "brave-neo";
    text = ''
      ${applyAppearance}/bin/brave-neo-apply --if-needed --skip-running || true
      exec ${pkgs.brave}/bin/brave "$@"
    '';
  };
  desktopEntry = {
    name = "Brave Web Browser";
    genericName = "Web Browser";
    comment = "Browse with the Neo Blush macOS-inspired appearance";
    exec = "${launcher}/bin/brave-neo %U";
    icon = "brave-browser";
    terminal = false;
    categories = [ "Network" "WebBrowser" ];
    mimeType = [ "text/html" "application/xhtml+xml" "x-scheme-handler/http" "x-scheme-handler/https" ];
    settings.StartupWMClass = "brave-browser";
    actions = {
      new-window = {
        name = "New Window";
        exec = "${launcher}/bin/brave-neo --new-window";
      };
      new-private-window = {
        name = "New Incognito Window";
        exec = "${launcher}/bin/brave-neo --incognito";
      };
    };
  };
in
{
  home.packages = [ applyAppearance launcher ];
  # Cover both desktop IDs shipped by Brave, including URL-handler launches.
  xdg.desktopEntries."brave-browser" = desktopEntry;
  xdg.desktopEntries."com.brave.Browser" = desktopEntry;

  # Merge only appearance preferences; never manage the whole Brave profile.
  # Apply once, and let subsequent adjustments in Brave remain the user's choice.
  home.activation.braveNeoAppearance = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${applyAppearance}/bin/brave-neo-apply --if-needed --skip-running
  '';
}
