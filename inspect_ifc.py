#!/usr/bin/env python3
"""
inspect_ifc.py — Standalone IFC diagnostic script for GreenBIM.

Usage:
    python inspect_ifc.py path/to/model.ifc
    python inspect_ifc.py          # prompts for path

No project files are imported or modified.
Requires only ifcopenshell and the Python standard library.
"""

import os
import sys
import collections

try:
    import ifcopenshell
    import ifcopenshell.util.element
except ImportError:
    print("ERROR: ifcopenshell is not installed.")
    print("       Install with:  pip install ifcopenshell")
    sys.exit(1)


# ──────────────────────────────────────────────────────────────
# FORMATTING HELPERS
# ──────────────────────────────────────────────────────────────

WIDTH = 70


def _header(title):
    print()
    print("=" * WIDTH)
    print(f"  {title}")
    print("=" * WIDTH)


def _row(label, value, indent=2):
    pad = " " * indent
    print(f"{pad}{label:<40} {value}")


def _sub(text, indent=2):
    print(f"{' ' * indent}{text}")


# ──────────────────────────────────────────────────────────────
# SECTION 1 — FILE INFO
# ──────────────────────────────────────────────────────────────

def section_file_info(model, filepath):
    _header("1. FILE INFO")

    size_bytes = os.path.getsize(filepath)
    if size_bytes >= 1_048_576:
        size_str = f"{size_bytes / 1_048_576:.2f} MB"
    else:
        size_str = f"{size_bytes / 1024:.1f} KB"

    _row("File path:", filepath)
    _row("File size:", size_str)
    _row("IFC schema:", model.schema)

    # Authoring software from file header
    software = "Unknown"
    try:
        header = model.header
        for attr in ("application", "description"):
            val = getattr(header, attr, None)
            if val:
                software = str(val)
                break
        # Many files store it in header.file_description or
        # header.file_name.preprocessor_version
        fn = getattr(header, "file_name", None)
        if fn:
            pp = getattr(fn, "preprocessor_version", None) or ""
            org = getattr(fn, "organization", None) or ""
            app = str(pp) + " " + str(org)
            if app.strip() and app.strip() != "None None":
                software = app.strip()
    except Exception:
        pass
    _row("Authoring software:", software)

    # Element count by IFC type
    print()
    _sub("Element count by type:")
    type_counts = collections.Counter()
    for entity in model:
        type_counts[entity.is_a()] += 1
    for ifc_type, count in sorted(
        type_counts.items(), key=lambda x: -x[1]
    )[:25]:
        _row(f"  {ifc_type}", count, indent=4)
    total = sum(type_counts.values())
    print()
    _row("  TOTAL entities in file:", total, indent=4)


# ──────────────────────────────────────────────────────────────
# SECTION 2 — MATERIAL ANALYSIS
# ──────────────────────────────────────────────────────────────

def _collect_materials(model):
    """Return list of (material_name, ifc_storage_type, element_id)."""
    records = []
    no_material_ids = []

    target_types = [
        "IfcWall", "IfcWallStandardCase", "IfcSlab",
        "IfcColumn", "IfcBeam", "IfcFooting", "IfcPile",
        "IfcStair", "IfcStairFlight", "IfcRoof",
        "IfcPlate", "IfcMember", "IfcCovering",
        "IfcDoor", "IfcWindow", "IfcRailing",
        "IfcBuildingElementProxy", "IfcCurtainWall",
    ]

    seen_ids = set()
    for ifc_type in target_types:
        try:
            elements = model.by_type(ifc_type)
        except Exception:
            continue
        for elem in elements:
            eid = elem.GlobalId
            if eid in seen_ids:
                continue
            seen_ids.add(eid)

            found = False
            for rel in getattr(elem, "HasAssociations", []):
                if not rel.is_a("IfcRelAssociatesMaterial"):
                    continue
                mat = rel.RelatingMaterial
                names_types = _extract_mat_names_and_type(mat)
                if names_types:
                    found = True
                    for name, storage in names_types:
                        records.append((name, storage, eid))

            if not found:
                # Try type association (Revit pattern)
                for rel in getattr(elem, "IsTypedBy", []):
                    type_obj = rel.RelatingType
                    for trel in getattr(
                        type_obj, "HasAssociations", []
                    ):
                        if not trel.is_a(
                            "IfcRelAssociatesMaterial"
                        ):
                            continue
                        mat = trel.RelatingMaterial
                        names_types = (
                            _extract_mat_names_and_type(mat)
                        )
                        if names_types:
                            found = True
                            for name, storage in names_types:
                                records.append(
                                    (name, storage, eid)
                                )

            if not found:
                no_material_ids.append(eid)

    return records, no_material_ids, len(seen_ids)


def _extract_mat_names_and_type(mat):
    results = []
    try:
        if mat.is_a("IfcMaterial"):
            if mat.Name:
                results.append(
                    (mat.Name.strip(), "IfcMaterial")
                )
        elif mat.is_a("IfcMaterialLayerSet"):
            for layer in mat.MaterialLayers or []:
                if layer.Material and layer.Material.Name:
                    results.append((
                        layer.Material.Name.strip(),
                        "IfcMaterialLayerSet"
                    ))
        elif mat.is_a("IfcMaterialLayerSetUsage"):
            ls = mat.ForLayerSet
            if ls:
                for layer in ls.MaterialLayers or []:
                    if layer.Material and layer.Material.Name:
                        results.append((
                            layer.Material.Name.strip(),
                            "IfcMaterialLayerSetUsage"
                        ))
        elif mat.is_a("IfcMaterialConstituentSet"):
            for c in mat.MaterialConstituents or []:
                if c.Material and c.Material.Name:
                    results.append((
                        c.Material.Name.strip(),
                        "IfcMaterialConstituentSet"
                    ))
        elif mat.is_a("IfcMaterialProfileSet"):
            for p in mat.MaterialProfiles or []:
                if p.Material and p.Material.Name:
                    results.append((
                        p.Material.Name.strip(),
                        "IfcMaterialProfileSet"
                    ))
        elif mat.is_a("IfcMaterialProfileSetUsage"):
            fps = mat.ForProfileSet
            if fps:
                for p in fps.MaterialProfiles or []:
                    if p.Material and p.Material.Name:
                        results.append((
                            p.Material.Name.strip(),
                            "IfcMaterialProfileSetUsage"
                        ))
        elif mat.is_a("IfcMaterialList"):
            for m in mat.Materials or []:
                if m.Name:
                    results.append(
                        (m.Name.strip(), "IfcMaterialList")
                    )
    except Exception:
        pass
    return results


def section_material_analysis(model):
    _header("2. MATERIAL ANALYSIS")

    records, no_mat_ids, total_structural = (
        _collect_materials(model)
    )

    _row("Structural elements scanned:", total_structural)
    _row(
        "Elements with no material found:",
        f"{len(no_mat_ids)}  "
        f"({len(no_mat_ids)/max(total_structural,1)*100:.1f}%)"
    )
    print()

    # Storage type breakdown
    storage_counts = collections.Counter(r[1] for r in records)
    _sub("Material storage methods found:")
    for storage, count in storage_counts.most_common():
        _row(f"  {storage}", count, indent=4)

    # Unique material names
    name_counts = collections.Counter(r[0] for r in records)
    unique_names = sorted(name_counts.keys())
    print()
    _sub(f"All unique material names ({len(unique_names)} total):")
    for name in unique_names:
        _row(f"  {name!r}", f"used {name_counts[name]}×", indent=4)

    # Top 10
    print()
    _sub("Top 10 most-used material names:")
    for name, count in name_counts.most_common(10):
        _row(f"  {name!r}", f"{count}×", indent=4)

    return len(name_counts), len(no_mat_ids), total_structural


# ──────────────────────────────────────────────────────────────
# SECTION 3 — VOLUME ANALYSIS
# ──────────────────────────────────────────────────────────────

def section_volume_analysis(model):
    _header("3. VOLUME ANALYSIS")

    target_types = [
        "IfcWall", "IfcWallStandardCase", "IfcSlab",
        "IfcColumn", "IfcBeam", "IfcFooting", "IfcPile",
        "IfcStair", "IfcStairFlight", "IfcRoof",
        "IfcPlate", "IfcMember",
    ]

    n_qty_volume = 0
    n_base_qty   = 0
    n_pset_vol   = 0
    n_zero       = 0
    total        = 0
    samples      = []   # (eid, name, volume, source)
    seen_ids     = set()

    _PSET_VOL_KEYS = {"volume", "vol", "tilavuus", "netvolume",
                      "grossvolume"}

    for ifc_type in target_types:
        try:
            elements = model.by_type(ifc_type)
        except Exception:
            continue
        for elem in elements:
            eid = elem.GlobalId
            if eid in seen_ids:
                continue
            seen_ids.add(eid)
            total += 1

            elem_name = getattr(elem, "Name", "") or ""
            found_vol = None
            source    = None

            # IfcQuantityVolume
            for definition in getattr(elem, "IsDefinedBy", []):
                if definition.is_a("IfcRelDefinesByQuantities"):
                    qset = definition.RelatingQuantity
                    qset_name = (
                        getattr(qset, "Name", "") or ""
                    ).lower()
                    for qty in getattr(
                        qset, "Quantities", []
                    ) or []:
                        if qty.is_a("IfcQuantityVolume"):
                            v = qty.VolumeValue
                            if v and float(v) > 0:
                                n_qty_volume += 1
                                if "base" in qset_name:
                                    n_base_qty += 1
                                found_vol = round(float(v), 4)
                                source = (
                                    f"IfcQuantityVolume "
                                    f"(pset: {qset.Name!r})"
                                )
                                break
                    if found_vol:
                        break

            # Property set volume
            if not found_vol:
                for definition in getattr(
                    elem, "IsDefinedBy", []
                ):
                    if definition.is_a(
                        "IfcRelDefinesByProperties"
                    ):
                        pset = (
                            definition.RelatingPropertyDefinition
                        )
                        for prop in getattr(
                            pset, "HasProperties", []
                        ):
                            pname = (
                                prop.Name.lower()
                                if prop.Name else ""
                            )
                            if any(
                                k in pname
                                for k in _PSET_VOL_KEYS
                            ):
                                if hasattr(prop, "NominalValue") \
                                        and prop.NominalValue:
                                    try:
                                        v = float(
                                            prop.NominalValue
                                            .wrappedValue
                                        )
                                        if v > 0:
                                            n_pset_vol += 1
                                            found_vol = round(
                                                v, 4
                                            )
                                            source = (
                                                f"Property "
                                                f"(pset: "
                                                f"{pset.Name!r}, "
                                                f"prop: "
                                                f"{prop.Name!r})"
                                            )
                                            break
                                    except Exception:
                                        pass
                        if found_vol:
                            break

            if not found_vol:
                n_zero += 1
                source = "None"

            if len(samples) < 5:
                samples.append((
                    eid, elem_name,
                    found_vol or 0.0, source or "None",
                    ifc_type
                ))

    _row("Structural elements scanned:", total)
    _row(
        "Have IfcQuantityVolume:",
        f"{n_qty_volume}  "
        f"({n_qty_volume/max(total,1)*100:.1f}%)"
    )
    _row(
        "Have BaseQuantities:",
        f"{n_base_qty}  "
        f"({n_base_qty/max(total,1)*100:.1f}%)"
    )
    _row(
        "Have property-set volume:",
        f"{n_pset_vol}  "
        f"({n_pset_vol/max(total,1)*100:.1f}%)"
    )
    _row(
        "Have NO volume data:",
        f"{n_zero}  "
        f"({n_zero/max(total,1)*100:.1f}%)"
    )
    print()
    _sub("Sample elements (first 5 scanned):")
    for eid, ename, vol, src, etype in samples:
        print()
        _row("  GlobalId:", eid, indent=4)
        _row("  Name:", ename or "(none)", indent=4)
        _row("  IFC type:", etype, indent=4)
        _row("  Volume m³:", vol, indent=4)
        _row("  Source:", src, indent=4)

    return n_qty_volume, n_zero, total


# ──────────────────────────────────────────────────────────────
# SECTION 4 — STOREY ANALYSIS
# ──────────────────────────────────────────────────────────────

def section_storey_analysis(model):
    _header("4. STOREY ANALYSIS")

    storeys = {}
    try:
        for storey in model.by_type("IfcBuildingStorey"):
            name = (getattr(storey, "Name", None) or "").strip()
            elev = getattr(storey, "Elevation", None)
            elev_str = (
                f"  elev={round(float(elev),2)} m"
                if elev is not None else ""
            )
            key = name or f"(unnamed storey{elev_str})"
            storeys[key] = 0
    except Exception:
        pass

    _row("Building storeys found:", len(storeys))
    if not storeys:
        _sub("  No IfcBuildingStorey entities found.")
    else:
        for s in storeys:
            _sub(f"  {s}")

    # Count elements per storey
    target_types = [
        "IfcWall", "IfcWallStandardCase", "IfcSlab",
        "IfcColumn", "IfcBeam", "IfcFooting", "IfcPile",
        "IfcStair", "IfcStairFlight", "IfcRoof",
        "IfcPlate", "IfcMember", "IfcCovering",
        "IfcDoor", "IfcWindow", "IfcRailing",
        "IfcBuildingElementProxy", "IfcCurtainWall",
    ]

    storey_elem_count = collections.defaultdict(int)
    no_storey = 0
    total = 0
    seen_ids = set()

    for ifc_type in target_types:
        try:
            elements = model.by_type(ifc_type)
        except Exception:
            continue
        for elem in elements:
            eid = elem.GlobalId
            if eid in seen_ids:
                continue
            seen_ids.add(eid)
            total += 1

            assigned = False
            for rel in getattr(
                elem, "ContainedInStructure", []
            ):
                container = rel.RelatingStructure
                if container.is_a("IfcBuildingStorey"):
                    sname = (
                        getattr(container, "Name", "")
                        or ""
                    ).strip()
                    storey_elem_count[
                        sname or "(unnamed)"
                    ] += 1
                    assigned = True
                    break
            if not assigned:
                no_storey += 1

    print()
    _sub("Element count per storey:")
    for sname, count in sorted(
        storey_elem_count.items(),
        key=lambda x: -x[1]
    ):
        _row(f"  {sname}", count, indent=4)

    print()
    _row(
        "Elements with no storey assignment:",
        f"{no_storey}  "
        f"({no_storey/max(total,1)*100:.1f}%)"
    )

    return len(storeys), no_storey, total


# ──────────────────────────────────────────────────────────────
# SECTION 5 — PROPERTY SET ANALYSIS
# ──────────────────────────────────────────────────────────────

def section_pset_analysis(model):
    _header("5. PROPERTY SET ANALYSIS")

    _MAT_KEYWORDS  = {"material", "materiaali", "aine",
                      "substance", "finish", "pinta", "werkstoff"}
    _VOL_KEYWORDS  = {"volume", "vol", "tilavuus", "netvolume",
                      "grossvolume"}

    all_psets      = collections.Counter()
    mat_psets      = set()
    vol_psets      = set()

    for rel in model.by_type("IfcRelDefinesByProperties"):
        try:
            pset = rel.RelatingPropertyDefinition
            pset_name = getattr(pset, "Name", "") or ""
            all_psets[pset_name] += 1
            for prop in getattr(pset, "HasProperties", []):
                pname = (
                    prop.Name.lower() if prop.Name else ""
                )
                if any(k in pname for k in _MAT_KEYWORDS):
                    mat_psets.add(pset_name)
                if any(k in pname for k in _VOL_KEYWORDS):
                    vol_psets.add(pset_name)
        except Exception:
            continue

    for rel in model.by_type("IfcRelDefinesByQuantities"):
        try:
            qset = rel.RelatingQuantity
            qset_name = getattr(qset, "Name", "") or ""
            all_psets[qset_name] += 1
            for qty in getattr(qset, "Quantities", []) or []:
                if qty.is_a("IfcQuantityVolume"):
                    vol_psets.add(qset_name)
        except Exception:
            continue

    _row("Unique property / quantity set names:", len(all_psets))
    print()
    _sub("All pset names (sorted by usage):")
    for name, count in all_psets.most_common():
        _row(f"  {name!r}", f"{count} elements", indent=4)

    print()
    _sub("Psets containing material information:")
    if mat_psets:
        for name in sorted(mat_psets):
            _sub(f"    {name!r}")
    else:
        _sub("    (none detected)")

    print()
    _sub("Psets / quantity sets containing volume information:")
    if vol_psets:
        for name in sorted(vol_psets):
            _sub(f"    {name!r}")
    else:
        _sub("    (none detected)")

    return len(all_psets), len(mat_psets), len(vol_psets)


# ──────────────────────────────────────────────────────────────
# SECTION 6 — GREENBIM SUITABILITY SCORE
# ──────────────────────────────────────────────────────────────

def section_suitability_score(
    n_unique_mats, n_no_mat, total_structural,
    n_qty_vol,     n_zero_vol, total_vol,
    n_storeys,     n_no_storey, total_storey,
    n_psets,       n_mat_psets, n_vol_psets,
):
    _header("6. GREENBIM SUITABILITY SCORE")

    # ── Materials (0-40) ─────────────────────────────────────
    mat_pct = (
        (total_structural - n_no_mat)
        / max(total_structural, 1) * 100
    )
    mat_score = round(mat_pct / 100 * 40)

    # ── Volumes (0-30) ────────────────────────────────────────
    vol_pct = (
        (total_vol - n_zero_vol)
        / max(total_vol, 1) * 100
    )
    vol_score = round(vol_pct / 100 * 30)

    # ── Storeys (0-15) ────────────────────────────────────────
    storey_pct = (
        (total_storey - n_no_storey)
        / max(total_storey, 1) * 100
    )
    storey_score = round(storey_pct / 100 * 15)

    # ── Property sets (0-15) ─────────────────────────────────
    # Up to 5 pts for having any psets,
    # +5 for mat psets, +5 for vol psets
    pset_score = 0
    if n_psets > 0:
        pset_score += 5
    if n_mat_psets > 0:
        pset_score += 5
    if n_vol_psets > 0:
        pset_score += 5

    total_score = mat_score + vol_score + storey_score + pset_score

    print()
    _row("Materials found:",
         f"{mat_score:3d} / 40  "
         f"({mat_pct:.1f}% elements matched)")
    _row("Volumes found:",
         f"{vol_score:3d} / 30  "
         f"({vol_pct:.1f}% elements with volume)")
    _row("Storeys found:",
         f"{storey_score:3d} / 15  "
         f"({storey_pct:.1f}% elements assigned)")
    _row("Property sets found:",
         f"{pset_score:3d} / 15  "
         f"({n_psets} psets, "
         f"{n_mat_psets} with material, "
         f"{n_vol_psets} with volume)")
    print()
    print("-" * WIDTH)
    _row("TOTAL SCORE:", f"{total_score} / 100")
    print("-" * WIDTH)

    print()
    if total_score >= 80:
        verdict = (
            f"  ✔  EXCELLENT ({total_score}/100) — "
            f"Ready for GreenBIM assessment."
        )
    elif total_score >= 60:
        verdict = (
            f"  ~  GOOD ({total_score}/100) — "
            f"Minor preparation needed."
        )
    elif total_score >= 40:
        verdict = (
            f"  !  FAIR ({total_score}/100) — "
            f"Material names need improvement."
        )
    else:
        verdict = (
            f"  ✗  POOR ({total_score}/100) — "
            f"Significant preparation needed."
        )
    print(verdict)

    print()
    print("  What to improve:")
    if mat_score < 32:
        print("  - Assign standard material names in your BIM "
              "authoring tool")
        print("    (e.g. Rudus C25/30, Paroc Extra, SSAB S355)")
    if vol_score < 24:
        print("  - Enable 'Export base quantities' in IFC export "
              "settings")
    if storey_score < 12:
        print("  - Ensure elements are contained in "
              "IfcBuildingStorey")
    if pset_score < 10:
        print("  - Export property sets in IFC export settings")
    if total_score >= 80:
        print("  - None — this file is well prepared!")


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) >= 2:
        filepath = sys.argv[1]
    else:
        filepath = input("Enter path to IFC file: ").strip()

    filepath = os.path.expanduser(filepath)

    if not os.path.isfile(filepath):
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    print()
    print("=" * WIDTH)
    print("  GreenBIM IFC DIAGNOSTIC REPORT")
    print(f"  {os.path.basename(filepath)}")
    print("=" * WIDTH)

    print("\nOpening IFC file…")
    try:
        model = ifcopenshell.open(filepath)
    except Exception as exc:
        print(f"ERROR: Could not open IFC file: {exc}")
        sys.exit(1)
    print("File loaded.")

    section_file_info(model, filepath)

    n_unique_mats, n_no_mat, total_structural = (
        section_material_analysis(model)
    )
    n_qty_vol, n_zero_vol, total_vol = (
        section_volume_analysis(model)
    )
    n_storeys, n_no_storey, total_storey = (
        section_storey_analysis(model)
    )
    n_psets, n_mat_psets, n_vol_psets = (
        section_pset_analysis(model)
    )
    section_suitability_score(
        n_unique_mats, n_no_mat, total_structural,
        n_qty_vol,     n_zero_vol, total_vol,
        n_storeys,     n_no_storey, total_storey,
        n_psets,       n_mat_psets, n_vol_psets,
    )

    print()
    print("=" * WIDTH)
    print("  END OF REPORT")
    print("=" * WIDTH)
    print()


if __name__ == "__main__":
    main()
