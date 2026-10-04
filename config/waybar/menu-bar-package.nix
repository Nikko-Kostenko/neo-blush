{ waybar }:
waybar.overrideAttrs (old: {
  pname = "neo-waybar";
  patches = (old.patches or [ ]) ++ [ ./patches/tray-menus.patch ];
})
