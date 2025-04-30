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
    ranger
    vscode
    code-cursor
    obsidian
    fish
    epiphany
    timeshift
    lutris
    telegram-desktop
    pinta
    lbreakout2
    wineWowPackages.stable
    ocs-url
    kdePackages.qtstyleplugin-kvantum

    #kdePackages
    #sddm-sugar-dark
    #kdePackages.calligra
    #kdePackages.sddm-kcm
    kdePackages.yakuake
    #kdePackages.audiotube
    #kdePackages.palapeli
    #kdePackages.plasmatube
    #kdePackages.kdenlive
    #crow-translate
    #blender



    #Openbox
    obconf          # GUI-шка для конфигурации
    openbox-menu           # Менюха, как в 2005-ом
    plank           # Док, чисто для шика
    picom           # Тени, прозрачность — must-have
    polybar         # Статусная панель уровня «хакер в метро»
    rofi            # Умный launcher, удобный и кастомизируемый
    feh
    tint2
    skippy-xd
    xfce.mousepad
    kitty
    pcmanfm
    openbox
  ];

  home.shellAliases = {
    ll = "ls -alF";
    rebuild = "sudo nixos-rebuild switch --flake ~/nixos-flake";
  };
}

