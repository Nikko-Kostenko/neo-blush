{ ... }:
{
  # Receiving files requires LocalSend's TCP/UDP port as well as the app.
  programs.localsend = {
    enable = true;
    openFirewall = true;
  };
}
