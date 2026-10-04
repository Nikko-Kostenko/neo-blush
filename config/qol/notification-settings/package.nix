{
  lib,
  stdenvNoCC,
  python3,
  makeWrapper,
  wrapGAppsHook3,
  gobject-introspection,
  gtk3,
  adwaita-icon-theme,
}:
let
  python = python3.withPackages (ps: [ ps.pygobject3 ]);
in
stdenvNoCC.mkDerivation {
  pname = "neo-notification-settings";
  version = "1.0.0";
  src = lib.cleanSourceWith {
    src = ./.;
    filter = path: type: lib.cleanSourceFilter path type && baseNameOf path != "__pycache__";
  };
  nativeBuildInputs = [
    makeWrapper
    wrapGAppsHook3
    gobject-introspection
  ];
  buildInputs = [
    gtk3
    adwaita-icon-theme
  ];
  dontBuild = true;
  doCheck = true;
  checkPhase = ''
    runHook preCheck
    PYTHONDONTWRITEBYTECODE=1 ${python}/bin/python3 -m unittest -v test_policy
    runHook postCheck
  '';
  installPhase = ''
    runHook preInstall
    mkdir -p "$out/bin" "$out/share/neo-notification-settings"
    cp main.py policy.py monitor.py style.css "$out/share/neo-notification-settings/"
    makeWrapper ${python}/bin/python3 "$out/bin/neo-notification-settings" \
      --add-flags "$out/share/neo-notification-settings/main.py" \
      --prefix XDG_DATA_DIRS : "${adwaita-icon-theme}/share"
    runHook postInstall
  '';
  meta = {
    description = "Interactive per-application notification preferences for Neo Blush";
    mainProgram = "neo-notification-settings";
    platforms = lib.platforms.linux;
  };
}
