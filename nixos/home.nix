{ config, pkgs, ... }:

{
  home.stateVersion = "23.11"; # Актуальная версия для home-manager
programs.git = {
    enable = true;
    userName = "lanthar91";
    userEmail = "elkhan.aliyev.91@gmail.com";
};


  home.packages = with pkgs; [
    neofetch
    vscode
    obsidian
    fish
    pinta
    wineWowPackages.stable
    ocs-url
    kdePackages.qtstyleplugin-kvantum
    xdotool
    skippy-xd
  ];

  home.shellAliases = {
    ll = "ls -alF";
    rebuild = "sudo nixos-rebuild switch --flake ~/.config/nixos/flake.nix";
  };
}
