{
  # Preserve your existing Home Manager state version.
  home.stateVersion = "26.05";
  programs.bash.enable = true;
  programs.git.enable = true;

  # Optional personal preferences, stored in your own configuration.
  # programs.git.settings.user = { name = "Alice"; email = "alice@example.com"; };
}
