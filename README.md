# README #

This repository contains a forked blender version 2.76b, with modified version of bullet used for underwater simulation.

Compiled version is in the file `blender.tar.gz`

The compiled version require boost libraries. Theese can be downloaded using ```sudo apt-get install libboost-all-dev```

This repository could by first installing dependencies:
```
cd blender
./build_files/build_environment/install_deps.sh
```
then compiled using:
```
mkdir build & cd build
cmake ..
make install -j4
```

The binary blender file will then be in the build/bin/ folder. You should point the UW Morse install to using this blender version.



For other compilation instructions see: http://wiki.blender.org/index.php/Dev:Doc/Building_Blender/Linux
