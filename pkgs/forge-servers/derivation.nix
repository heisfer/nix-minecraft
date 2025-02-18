{
  lib,
  stdenvNoCC,
  fetchurl,
  nixosTests,
  jre,
  version,
  url,
  sha256,
  minecraft-server,
  unzip,
}:
stdenvNoCC.mkDerivation {
  pname = "forge";
  inherit version;

  src = fetchurl { inherit url sha256; };

  # preferLocalBuild = true;

  nativeBuildInputs = [
    unzip
  ];
  unpackPhase = ''
    runHook preUnpack
    unzip $src
    runHook postUnpack
  '';

  installPhase = ''
    mkdir -p $out/bin $out/lib/minecraft
    cp -v server.jar $out/lib/minecraft/
    cp -r -v libraries $out/lib/minecraft/


    cat > $out/bin/minecraft-server << EOF
    #!/bin/sh
    exec ${jre}/bin/java \$@ -jar $out/lib/minecraft/server.jar nogui
    EOF

    chmod +x $out/bin/minecraft-server
  '';

  passthru = {
    updateScript = ./update.py;
    # If you plan on running paper without internet, be sure to link this jar
    # to `cache/mojang_{version}.jar`.
    vanillaJar = "${minecraft-server}/lib/minecraft/server.jar";
  };

  meta = with lib; {
    description = "Minecraft mod loader";
    homepage = "https://papermc.io";
    license = licenses.gpl3Only;
    platforms = platforms.unix;
    maintainers = with maintainers; [ heisfer ];
    mainProgram = "minecraft-server";
  };
}
