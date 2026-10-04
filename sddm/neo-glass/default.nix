{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.neo.sddm;
  statusPlugin = pkgs.stdenv.mkDerivation {
    pname = "sddm-neo-status";
    version = "1.0.0";
    src = ./status;
    nativeBuildInputs = [ pkgs.kdePackages.qmake ];
    buildInputs = with pkgs.kdePackages; [
      qtbase
      qtdeclarative
    ];
    dontWrapQtApps = true;
    installPhase = ''
      runHook preInstall
      mkdir -p "$out/lib/qt-6/qml/NeoStatus"
      cp libneostatus.so qmldir plugins.qmltypes "$out/lib/qt-6/qml/NeoStatus/"
      runHook postInstall
    '';
  };
  theme =
    pkgs.runCommand "sddm-neo-glass"
      {
        nativeBuildInputs = [ pkgs.kdePackages.qtdeclarative ];
      }
      ''
        cp -R ${./theme} theme
        cp -R ${./tests} tests
        chmod -R u+w theme
        export QT_QPA_PLATFORM=offscreen
        export QT_QUICK_BACKEND=software
        export QML_IMPORT_PATH=${statusPlugin}/lib/qt-6/qml:${pkgs.kdePackages.qtdeclarative}/lib/qt-6/qml
        export QT_PLUGIN_PATH=${pkgs.kdePackages.qtbase}/lib/qt-6/plugins:${pkgs.kdePackages.qtsvg}/lib/qt-6/plugins
        export XDG_RUNTIME_DIR="$TMPDIR/runtime"
        export XDG_CACHE_HOME="$TMPDIR/cache"
        mkdir -m 700 "$XDG_RUNTIME_DIR"
        # SDDM supplies config, sddm, and the user/session models at runtime.
        qmllint -I ${statusPlugin}/lib/qt-6/qml -I ${pkgs.kdePackages.qtdeclarative}/lib/qt-6/qml --unqualified disable -W 0 theme/*.qml
        qmltestrunner -input tests -o -,txt

        ${lib.optionalString (cfg.avatar != null) ''
          cp ${lib.escapeShellArg "${cfg.avatar}"} theme/assets/avatar.jpg
          substituteInPlace theme/theme.conf \
            --replace-fail 'avatar=' 'avatar=assets/avatar.jpg'
        ''}
        substituteInPlace theme/theme.conf \
          --replace-fail 'avatarUser=' ${lib.escapeShellArg "avatarUser=${cfg.avatarUser}"}

        mkdir -p "$out/share/sddm/themes/neo-glass"
        cp -R theme/. "$out/share/sddm/themes/neo-glass/"
      '';
in
{
  options.neo.sddm = {
    avatar = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      description = "Optional login-screen photo; no personal photo is included by default.";
    };
    avatarUser = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Account that should display the configured login-screen photo.";
    };
  };

  config = {
    services.displayManager.sddm = {
      enable = true;
      theme = "neo-glass";
      package = pkgs.kdePackages.sddm;
      wayland.enable = true;
      extraPackages = [
        statusPlugin
      ]
      ++ (with pkgs.kdePackages; [
        qtdeclarative
        qtsvg
      ]);
      # Qt caches QML by URL and modification time. Nix normalizes timestamps,
      # so the stable /run/current-system path can reuse an older layout's cache.
      # A store path changes with the theme contents and gives each version its own cache.
      settings.Theme.ThemeDir = "${theme}/share/sddm/themes";
    };

    environment.systemPackages = [ theme ];
    # Load the new greeter on the next display-manager start without ending the desktop session.
    systemd.services.display-manager.restartIfChanged = false;
    # SDDM runs as its own user and cannot use Home Manager's font configuration.
    fonts.packages = [ pkgs.inter ];
  };
}
