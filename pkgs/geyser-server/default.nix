{
  lib,
  fetchurl,
  stdenvNoCC,
  jre_headless,
}:
stdenvNoCC.mkDerivation {
  pname = "geyser";
  version = "2.6.1-786";
  src = fetchurl {
    url = "https://download.geysermc.org/v2/projects/geyser/versions/2.6.1/builds/786/downloads/standalone";
    sha256 = "d2d42a174b82be6a2c1d6387757b79e0f890a462507479bf05cd56db638e0dae";
  };

  preferLocalBuild = true;

  installPhase = ''
    mkdir -p $out/bin $out/lib/minecraft
    cp -v $src $out/lib/minecraft/server.jar
    cat > $out/bin/geyser << EOF
    #!/bin/sh
    exec ${jre_headless}/bin/java \$@ -jar $out/lib/minecraft/server.jar nogui
    EOF
    chmod +x $out/bin/geyser
  '';

  dontUnpack = true;

  meta = with lib; {
    description = "Java and Bedrock bridge";
    homepage = "https://geysermc.org/";
    license = licenses.mit;
    platforms = platforms.unix;
    maintainers = with maintainers; [ heisfer ];
    mainProgram = "geyser";
  };

}
