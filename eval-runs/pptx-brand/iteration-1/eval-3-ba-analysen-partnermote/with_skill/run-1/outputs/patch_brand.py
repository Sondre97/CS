#!/usr/bin/env python3
"""Patch generert pptx til BDO-temaet (pptx-brand, produksjonsvei B).

- Setter temafargene (clrScheme) til BDO-fasiten fra bdo-design, slik at
  theme-sjekken PASSer og eventuelle schemeClr-referanser arver riktig.
- Setter temafontene (major/minor) til Trebuchet MS.
- Erstatter ev. ikke-godkjente <a:latin>-typefaces i innholdsfiler med Trebuchet MS.

Bruk: python3 patch_brand.py ba2026_partner.pptx
"""
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

BDO_SCHEME = {
    "dk2": "333333", "lt2": "F2F2F2",
    "accent1": "E81A3B", "accent2": "5B6E7F", "accent3": "98002E",
    "accent4": "D67900", "accent5": "009966", "accent6": "008FD2",
    "hlink": "0062B8", "folHlink": "98002E",
}
ALLOWED_FONT = re.compile(r"^(\+m[jn]-(lt|ea|cs)|Trebuchet MS|Bliss.*)$")


def patch(pptx_path: str) -> None:
    src = Path(pptx_path).resolve()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "unpacked"
        with zipfile.ZipFile(src) as zf:
            zf.extractall(root)

        # 1) Temafarger + temafonter
        for theme in sorted(root.glob("ppt/theme/theme*.xml")):
            xml = theme.read_text(encoding="utf-8")
            for slot, val in BDO_SCHEME.items():
                xml = re.sub(
                    rf'(<a:{slot}>\s*<a:srgbClr val=")[0-9A-Fa-f]{{6}}(")',
                    rf"\g<1>{val}\g<2>", xml)
            xml = re.sub(
                r'(<a:(?:majorFont|minorFont)>\s*<a:latin typeface=")[^"]*(")',
                r"\g<1>Trebuchet MS\g<2>", xml)
            theme.write_text(xml, encoding="utf-8")

        # 2) Ikke-godkjente fonter i innholdsfiler -> Trebuchet MS
        content = []
        for pat in ("ppt/slides/slide*.xml", "ppt/slideLayouts/slideLayout*.xml",
                    "ppt/slideMasters/slideMaster*.xml", "ppt/charts/chart*.xml"):
            content += sorted(root.glob(pat))
        replaced = {}
        for f in content:
            xml = f.read_text(encoding="utf-8")

            def sub(m):
                tf = m.group(2)
                if tf and not ALLOWED_FONT.match(tf):
                    replaced[tf] = replaced.get(tf, 0) + 1
                    return m.group(1) + "Trebuchet MS" + m.group(3)
                return m.group(0)

            new = re.sub(r'(<a:latin[^>]*typeface=")([^"]*)(")', sub, xml)
            if new != xml:
                f.write_text(new, encoding="utf-8")

        # 3) Pakk sammen igjen (zip fra INNSIDEN av mappen)
        out = Path(td) / src.name
        subprocess.run(["zip", "-Xqr", str(out), "."], cwd=root, check=True)
        shutil.move(str(out), src)

    print(f"patched {src.name}: tema -> BDO, fonter erstattet: {replaced or 'ingen'}")


if __name__ == "__main__":
    patch(sys.argv[1])
