{ pkgs, ... }: {
  channel = "stable-23.11";
  packages = [
    pkgs.python3
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv
  ];
  idx = {
    extensions = [
      "ms-python.python"
    ];
    workspace = {
      onCreate = {
        setup-venv = "python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt";
      };
    };
  };
}