{ lib, stdenv, fetchzip, pkg-config, hyprland }:

stdenv.mkDerivation {
  pname = "neo-hyprglass";
  version = "0.6.4";
  src = fetchzip {
    url = "https://codeload.github.com/hyprnux/hyprglass/tar.gz/22acd5db6ef73fa34cad2d5ce8b76cf37e9acaa5";
    extension = "tar.gz";
    hash = "sha256-coVoTJyRhn6eKZ8oJXus93p/G1gblgqcQNhNXBhx+G4=";
  };
  nativeBuildInputs = [ pkg-config ];
  buildInputs = [ hyprland ] ++ hyprland.buildInputs;
  enableParallelBuilding = true;
  installPhase = ''
    runHook preInstall
    install -Dm755 hyprglass.so "$out/lib/hyprglass.so"
    mkdir -p "$out/share/neo-hyprglass"
    install -d -m700 "$TMPDIR/neo-hyprglass-runtime"
    XDG_RUNTIME_DIR="$TMPDIR/neo-hyprglass-runtime" ${hyprland}/bin/Hyprland --version-json \
      > "$out/share/neo-hyprglass/compositor.json"
    runHook postInstall
  '';
  passthru = { inherit hyprland; };
  meta = {
    description = "HyprGlass pinned for the Neo Blush Hyprland desktop";
    homepage = "https://github.com/hyprnux/hyprglass";
    license = lib.licenses.bsd3;
    platforms = [ "x86_64-linux" ];
  };
}
