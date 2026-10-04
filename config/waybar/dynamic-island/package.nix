{ lib, stdenvNoCC, python3, makeWrapper, glib, playerctl, wireplumber, pulseaudio }:
let
  python = python3.withPackages (ps: [ ps.pygobject3 ]);
in stdenvNoCC.mkDerivation {
  pname = "neo-dynamic-island";
  version = "1.0.0";
  src = lib.cleanSource ./.;
  nativeBuildInputs = [ makeWrapper ];
  dontBuild = true;
  installPhase = ''
    mkdir -p "$out/share/neo-dynamic-island" "$out/bin"
    cp main.py model.py "$out/share/neo-dynamic-island/"
    cp -r tests "$out/share/neo-dynamic-island/"
    makeWrapper ${python}/bin/python3 "$out/bin/neo-dynamic-island" \
      --add-flags "$out/share/neo-dynamic-island/main.py" \
      --prefix GI_TYPELIB_PATH : "${glib.out}/lib/girepository-1.0" \
      --prefix PATH : ${lib.makeBinPath [ playerctl wireplumber pulseaudio ]}
  '';
  doInstallCheck = true;
  installCheckPhase = ''
    "$out/bin/neo-dynamic-island" --self-test
  '';
  meta.mainProgram = "neo-dynamic-island";
}
