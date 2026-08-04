#!/usr/bin/env python3
"""Gi det genererte dekket BDO-temaet: riktige temafarger + Trebuchet MS som temafont.

pptxgenjs skriver Office-standardtemaet. Alle farger/fonter i dekket er satt
eksplisitt (path B), men med BDO-temaet paa plass arver ogsaa eventuelle
temareferanser riktige verdier, og fargevelgeren i PowerPoint viser BDO-paletten.
"""
import re
import sys

THEME = "unpacked/ppt/theme/theme1.xml"

COLORS = {
    "dk2": "333333", "lt2": "F2F2F2",
    "accent1": "E81A3B", "accent2": "5B6E7F", "accent3": "98002E",
    "accent4": "D67900", "accent5": "009966", "accent6": "008FD2",
    "hlink": "0062B8", "folHlink": "98002E",
}

xml = open(THEME, encoding="utf-8").read()
for slot, val in COLORS.items():
    xml, n = re.subn(
        rf'(<a:{slot}>\s*<a:srgbClr val=")[0-9A-Fa-f]{{6}}(")',
        rf"\g<1>{val}\g<2>", xml)
    if n != 1:
        print(f"ADVARSEL: {slot}: {n} treff (ventet 1)")
for tag in ("majorFont", "minorFont"):
    xml, n = re.subn(
        rf'(<a:{tag}>\s*<a:latin typeface=")[^"]*(")',
        r"\g<1>Trebuchet MS\g<2>", xml)
    if n != 1:
        print(f"ADVARSEL: {tag}: {n} treff (ventet 1)")

open(THEME, "w", encoding="utf-8").write(xml)
print("theme1.xml patchet til BDO-tema")
