"""Small, read-only Office Open XML extractor; formulas are *not* evaluated.

No macros run. Only named sheets and cached/literal values are read. The importers
consume the explicit columns of the known source workbooks, not computed totals.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def read_sheets(path: str | Path, wanted: set[str]) -> dict[str, list[dict[str, str]]]:
    result = {}
    with zipfile.ZipFile(path) as z:
        # Resist malformed archives with very large XML entries.
        for member in z.infolist():
            if member.filename.endswith(".xml") and member.file_size > 80_000_000:
                raise ValueError("Hoja XML demasiado grande")
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        paths = {el.attrib["Id"]: el.attrib["Target"] for el in rels}
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            strings = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(el.itertext()) for el in strings]
        for sheet in workbook.find(MAIN + "sheets"):
            name = sheet.attrib["name"]
            if name not in wanted:
                continue
            rid = sheet.attrib[REL + "id"]
            target = paths[rid].lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            root = ET.fromstring(z.read(target))
            output = []
            for row in root.findall(".//" + MAIN + "sheetData/" + MAIN + "row"):
                cells = {}
                for cell in row.findall(MAIN + "c"):
                    address = cell.attrib["r"]
                    column = re.match(r"[A-Z]+", address).group(0)
                    val = cell.find(MAIN + "v")
                    if cell.attrib.get("t") == "inlineStr":
                        node = cell.find(MAIN + "is")
                        value = "".join(node.itertext()) if node is not None else ""
                    elif val is not None and val.text is not None:
                        value = shared[int(val.text)] if cell.attrib.get("t") == "s" else val.text
                    else:
                        continue  # no cached result; do not evaluate formulas
                    cells[column] = value.strip() if value else ""
                if cells:
                    output.append(cells)
            result[name] = output
    missing = wanted - result.keys()
    if missing:
        raise ValueError("No están las hojas requeridas: " + ", ".join(sorted(missing)))
    return result


def list_sheet_names(path: str | Path) -> set[str]:
    """Return workbook sheet names without loading any sheet's XML payload."""
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets = workbook.find(MAIN + "sheets")
        if sheets is None:
            raise ValueError("No se encontraron hojas de cálculo")
        return {sheet.attrib["name"] for sheet in sheets}
