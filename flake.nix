{
  description = "A poetry flake";
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/8edf06bea5bcbee082df1b7369ff973b91618b8d";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    flake-utils,
    poetry2nix,
    nixpkgs,
  }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication defaultPoetryOverrides;
      in
      {
        formatter = pkgs.alejandra;

        packages = {
          cheatgooglecal = mkPoetryApplication {
            projectDir = self;
            overrides = defaultPoetryOverrides.extend
              (self: super: {
                x-wr-timezone = super.x-wr-timezone.overridePythonAttrs
                (
                  old: {
                    buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
                  }
                );
                recurring-ical-events = super.recurring-ical-events.overridePythonAttrs
                (
                  old: {
                    buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
                  }
                );
              });
          };
          default = self.packages.${system}.cheatgooglecal;
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.cheatgooglecal ];
          packages = [ pkgs.poetry ];
        };
      });
}
