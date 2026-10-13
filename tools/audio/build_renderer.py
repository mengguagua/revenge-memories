#!/usr/bin/env python3
"""Build a temporary NSF-only Game Music Emu renderer with a driver-state hook.
Usage: python3 build_renderer.py /path/to/game-music-emu /private/tmp/fe2-gme
The input source tree is copied; this never patches the original source tree.
"""
import argparse
from pathlib import Path
import shutil
import subprocess

COMMON = "Blip_Buffer Classic_Emu Data_Reader Dual_Resampler Effects_Buffer Fir_Resampler gme Gme_File M3u_Playlist Multi_Buffer Music_Emu"
NSF = "Nes_Apu Nes_Cpu Nes_Fme7_Apu Nes_Namco_Apu Nes_Oscs Nes_Vrc6_Apu Nes_Fds_Apu Nes_Vrc7_Apu Nsf_Emu Ym2413_Emu"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("work", type=Path)
    a = p.parse_args()
    gme = a.work/"gme"
    if not gme.exists():
        shutil.copytree(a.source/"gme", gme)
    source = gme/"Nsf_Emu.cpp"
    text = source.read_text()
    if "fe2_frame_hook" not in text:
        text = text.replace('#include "Nsf_Emu.h"', '''#include "Nsf_Emu.h"
#include <stdio.h>
static FILE *fe2_trace_file = 0;
extern "C" void fe2_set_trace(const char *path) {
    if (fe2_trace_file) fclose(fe2_trace_file);
    fe2_trace_file = path ? fopen(path, "wb") : 0;
}
static void fe2_frame_hook(const unsigned char *ram) {
    if (fe2_trace_file) {
        fwrite(ram + 0xE0, 1, 16, fe2_trace_file);
        fwrite(ram + 0x600, 1, 0xD0, fe2_trace_file);
    }
}''', 1).replace("GME_FRAME_HOOK( this );", "GME_FRAME_HOOK( this );\n                fe2_frame_hook(low_mem);")
        source.write_text(text)
    obj = a.work/"emu2413.o"
    subprocess.run(["clang", "-O2", "-fPIC", "-c", "ext/emu2413.c", "-o", str(obj)], cwd=gme, check=True)
    library = a.work/"libgme.dylib"
    subprocess.run(["clang++", "-std=c++11", "-O2", "-fPIC", "-dynamiclib",
                    "-DBLARGG_LITTLE_ENDIAN=1", "-DGME_TYPE_LIST=gme_nsf_type"] +
                   [f+".cpp" for f in (COMMON+" "+NSF).split()] +
                   [str(obj), "-o", str(library)], cwd=gme, check=True)
    print(library)

if __name__ == "__main__":
    main()
