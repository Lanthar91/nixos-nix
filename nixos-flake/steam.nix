{ config, pkgs, ... }:
{
  programs.steam = {
    enable = true;
    remotePlay.openFirewall = true; # Open ports in the firewall for Steam Remote Play
    dedicatedServer.openFirewall = true; # Open ports in the firewall for Source Dedicated Server
    localNetworkGameTransfers.openFirewall = true; # Open ports in the firewall for Steam Local Network Game Transfers
  }; # Эта точка с запятой разделяет programs.steam от следующего возможного атрибута на этом уровне

  # Здесь могут быть другие настройки вашего configuration.nix или home.nix ...
  # Например:
  # services.nginx.enable = true;

} # Эта фигурная скобка закрывает весь конфигурационный блок. Точка с запятой здесь не нужна.
