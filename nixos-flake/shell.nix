{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.pyqt5
    python312Packages.pygobject3
    gtk4
    mesa
  ];

  shellHook = ''
    export QT_QPA_PLATFORM_PLUGIN_PATH=${pkgs.qt5.qtbase.bin}/lib/qt-${pkgs.qt5.qtbase.version}/plugins/platforms
    export LD_LIBRARY_PATH=${pkgs.mesa}/lib:${pkgs.libglvnd}/lib:$LD_LIBRARY_PATH
  '';
}

