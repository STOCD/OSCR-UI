{ nixpkgs ? import <nixpkgs> {} }:

nixpkgs.mkShell {
  nativeBuildInputs = with nixpkgs; [
    nixpkgs.python311
    nixpkgs.python311Packages.pyside6
    nixpkgs.qt6.full
  ];
}
