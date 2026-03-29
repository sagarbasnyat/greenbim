import ifcopenshell
import ifcopenshell.util.element
import pandas as pd
import re
from difflib import get_close_matches

# Populated by parse_ifc(); accessed by app.py after each parse.
# Tuple of (area_m2: float | None, method: str | None)
DETECTED_FLOOR_AREA = (None, None)

# ─────────────────────────────────────────────────────────────
# ELEMENT TYPES TO EXTRACT
# ─────────────────────────────────────────────────────────────
TARGET_TYPES = [
    "IfcWall", "IfcWallStandardCase", "IfcSlab",
    "IfcColumn", "IfcBeam", "IfcFooting", "IfcPile",
    "IfcStair", "IfcStairFlight", "IfcRoof",
    "IfcPlate", "IfcMember", "IfcCovering",
    "IfcDoor", "IfcWindow", "IfcRailing",
    "IfcBuildingElementProxy", "IfcFlowSegment",
    "IfcFlowFitting", "IfcFlowTerminal",
    "IfcFurnishingElement", "IfcCurtainWall"
]

# ─────────────────────────────────────────────────────────────
# MATERIAL NORMALISATION MAP
# Finnish + International + Regex patterns
# ─────────────────────────────────────────────────────────────
MATERIAL_NORMALISE = {
    # Concrete
    "betoni": "Concrete",
    "beton": "Concrete",
    "concrete": "Concrete",
    "teräsbetoni": "Reinforced concrete",
    "reinforced concrete": "Reinforced concrete",
    "raudoitettu betoni": "Reinforced concrete",
    "precast": "Precast concrete",
    "elementtibetoni": "Precast concrete",
    "ontelolaatta": "Precast concrete hollow core slab",
    "hollow core": "Precast concrete hollow core slab",
    "valmisbetoni": "Ready-mix concrete, C25/30, GWP.REF",
    "ready-mix": "Ready-mix concrete, C25/30, GWP.REF",
    "ready mix": "Ready-mix concrete, C25/30, GWP.REF",
    "paikallavalettu": "Ready-mix concrete, C25/30, GWP.REF",
    "in-situ": "Ready-mix concrete, C25/30, GWP.REF",
    "in situ": "Ready-mix concrete, C25/30, GWP.REF",

    # Finnish concrete grades
    "k20": "Ready-mix concrete, C25/30, GWP.REF",
    "k25": "Ready-mix concrete, C25/30, GWP.REF",
    "k30": "Ready-mix concrete, C25/30, GWP.REF",
    "k35": "Ready-mix concrete, C25/30, GWP.REF",
    "k40": "Ready-mix concrete, C25/30, GWP.REF",
    "c16": "Ready-mix concrete, C25/30, GWP.REF",
    "c20": "Ready-mix concrete, C25/30, GWP.REF",
    "c25": "Ready-mix concrete, C25/30, GWP.REF",
    "c30": "Ready-mix concrete, C25/30, GWP.REF",
    "c35": "Ready-mix concrete, C25/30, GWP.REF",
    "c40": "Ready-mix concrete, C25/30, GWP.REF",
    "c45": "Ready-mix concrete, C25/30, GWP.REF",

    # Timber
    "puu": "Sawn timber",
    "wood": "Sawn timber",
    "timber": "Sawn timber",
    "sahatavara": "Sawn timber",
    "sawn timber": "Sawn timber",
    "softwood": "Sawn timber",
    "hardwood": "Sawn timber",
    "liimapuu": "GLT, Glued laminated timber",
    "glulam": "GLT, Glued laminated timber",
    "glt": "GLT, Glued laminated timber",
    "glued laminated": "GLT, Glued laminated timber",
    "clt": "CLT, Cross laminated timber",
    "cross laminated": "CLT, Cross laminated timber",
    "ristikkoklt": "CLT, Cross laminated timber",
    "lvl": "LVL, laminated veneer lumber for beams, posts, and panels",
    "kerto": "LVL, laminated veneer lumber for beams, posts, and panels",
    "viilupuu": "LVL, laminated veneer lumber for beams, posts, and panels",
    "laminated veneer": "LVL, laminated veneer lumber for beams, posts, and panels",
    "plywood": "Plywood, spruce, uncoated",
    "vaneri": "Plywood, spruce, uncoated",
    "osb": "OSB panel",
    "lastulevyy": "Chipboard",
    "chipboard": "Chipboard",
    "mdf": "Fibreboard, medium density, mdf",
    "fibreboard": "Fibreboard, medium density, mdf",

    # Steel
    "teräs": "Steel",
    "steel": "Steel",
    "metalli": "Steel",
    "metal": "Steel",
    "structural steel": "Steel",
    "rakenneteras": "Steel",
    "s235": "Steel",
    "s275": "Steel",
    "s355": "Steel",
    "s420": "Steel",
    "stainless": "Stainless steel",
    "rostfri": "Stainless steel",
    "aluminium": "Aluminium (general primary)",
    "aluminum": "Aluminium",
    "alumiini": "Aluminium",
    "copper": "Copper",
    "kupari": "Copper",
    "zinc": "Zinc",
    "sinkki": "Zinc",

    # Masonry
    "tiili": "Brick",
    "brick": "Brick",
    "harkko": "Concrete block",
    "concrete block": "Concrete block",
    "masonry": "Masonry",
    "muuraus": "Masonry",
    "kalkkihiekkatiili": "Calcium silicate unit",
    "calcium silicate": "Calcium silicate unit",

    # Insulation
    "mineraalivilla": "Mineral wool insulation",
    "mineral wool": "Mineral wool insulation",
    "glasswool": "Glass wool insulation",
    "glass wool": "Glass wool insulation",
    "lasivilla": "Glass wool insulation",
    "rock wool": "Rock wool insulation",
    "kivivilla": "Rock wool insulation",
    "eristys": "Mineral wool insulation",
    "insulation": "Mineral wool insulation",
    "eps": "EPS insulation",
    "expanded polystyrene": "EPS insulation",
    "xps": "XPS insulation",
    "extruded polystyrene": "XPS insulation",
    "polyuretaani": "Polyurethane insulation",
    "polyurethane": "Polyurethane insulation",
    "pur": "Polyurethane insulation",
    "styrox": "EPS insulation",
    "styrofoam": "EPS insulation",
    "cellulose": "Cellulose insulation, loose-fill",
    "selluloosa": "Cellulose insulation, loose-fill",

    # Gypsum
    "kipsilevy": "Gypsum plasterboard, interiors",
    "gypsum": "Gypsum plasterboard, interiors",
    "plasterboard": "Gypsum plasterboard, interiors",
    "drywall": "Gypsum plasterboard, interiors",
    "gkb": "Gypsum plasterboard, interiors",
    "gyproc": "Gypsum plasterboard, interiors",
    "kipsi": "Gypsum plasterboard, interiors",

    # Stone and aggregate
    "graniitti": "Stone (granite)",
    "granite": "Stone (granite)",
    "sora": "Gravel and sand",
    "gravel": "Gravel and sand",
    "hiekka": "Gravel and sand",
    "sand": "Gravel and sand",
    "kiviaines": "Gravel and sand",
    "aggregate": "Gravel and sand",
    "crushed stone": "Gravel and sand",
    "murske": "Gravel and sand",
    "limestone": "Stone (limestone)",
    "kalkkikivi": "Stone (limestone)",

    # Glass
    "lasi": "Glass",
    "glass": "Glass",
    "glazing": "Glass",

    # Bitumen and waterproofing
    "bitumi": "Bitumen",
    "bitumen": "Bitumen",
    "asphalt": "Bitumen",
    "asfaltti": "Bitumen",
    "vedeneristys": "Waterproofing membrane",
    "waterproofing": "Waterproofing membrane",

    # Paint and finishes
    "maali": "Paint",
    "paint": "Paint",
    "coating": "Paint",
    "pinnoite": "Paint",
    "render": "Render",
    "rappaus": "Render",
    "plaster": "Render",
    "tasoite": "Render",

    # Flooring
    "parquet": "Flooring, parquet",
    "parketti": "Flooring, parquet",
    "ceramic": "Ceramic tiles",
    "keramiikka": "Ceramic tiles",
    "tile": "Ceramic tiles",
    "laatta": "Ceramic tiles",
    "vinyl": "Vinyl flooring",
    "linoleum": "Linoleum flooring",
    "carpet": "Carpet",
    "matto": "Carpet",

    # ── German concrete ───────────────────────────────────────
    "leichtbeton": "Ready-mix concrete, C25/30, GWP.REF",
    "stahlbeton": "Reinforced concrete",
    "normalbeton": "Ready-mix concrete, C25/30, GWP.REF",
    "spannbeton": "Ready-mix concrete, C25/30, GWP.REF",
    "ortbeton": "Ready-mix concrete, C25/30, GWP.REF",
    "fertigteil": "Precast concrete",
    "betonfertigteil": "Precast concrete",

    # ── German timber ─────────────────────────────────────────
    "holz": "Sawn timber",
    "fichte": "Sawn timber",
    "kiefer": "Sawn timber",
    "buche": "Sawn timber",
    "nadelholz": "Sawn timber",
    "brettschichtholz": "GLT, Glued laminated timber",
    "brettsperrholz": "CLT, Cross laminated timber",
    "furnierschichtholz": "LVL, laminated veneer lumber for beams, posts, and panels",
    "sperrholz": "Plywood, spruce, uncoated",

    # ── German steel ──────────────────────────────────────────
    "stahl": "Steel",
    "baustahl": "Steel",
    "edelstahl": "Stainless steel",

    # ── German insulation ─────────────────────────────────────
    "mineralwolle": "Mineral wool insulation",
    "glaswolle": "Glass wool insulation",
    "steinwolle": "Rock wool insulation",
    "daemmung": "Mineral wool insulation",
    "daemmstoff": "Mineral wool insulation",
    "waermedaemmung": "Mineral wool insulation",
    "polystyrol": "EPS insulation",
    "polyurethan": "Polyurethane insulation",

    # ── German masonry ────────────────────────────────────────
    "ziegel": "Brick",
    "mauerziegel": "Brick",
    "kalksandstein": "Calcium silicate unit",
    "porenbeton": "Concrete block",
    "mauerwerk": "Masonry",

    # ── German gypsum ─────────────────────────────────────────
    "gipskarton": "Gypsum plasterboard, interiors",
    "gipskartonplatte": "Gypsum plasterboard, interiors",
    "gips": "Gypsum plasterboard, interiors",
    "trockenbau": "Gypsum plasterboard, interiors",

    # ── German glass and other ────────────────────────────────
    "glas": "Glass",
    "verglasung": "Glass",
    "glasscheibe": "Glass",
    "solid": "Ready-mix concrete, C25/30, GWP.REF",
    "estrich": "Ready-mix concrete, C25/30, GWP.REF",
    "putz": "Render",
    "aussenputz": "Render",
    "innenputz": "Render",

    # ── Swedish concrete ──────────────────────────────────────
    "betong": "Ready-mix concrete, C25/30, GWP.REF",
    "armerad betong": "Ready-mix concrete, C25/30, GWP.REF",
    "prefabbetong": "Precast concrete",
    "platsgjuten betong": "Ready-mix concrete, C25/30, GWP.REF",

    # ── Swedish timber ────────────────────────────────────────
    "tra": "Sawn timber",
    "trä": "Sawn timber",
    "limtra": "GLT, Glued laminated timber",
    "korslimt tra": "CLT, Cross laminated timber",
    "fanerskiva": "Plywood, spruce, uncoated",
    "spånskiva": "Chipboard",

    # ── Swedish steel ─────────────────────────────────────────
    "stal": "Steel",
    "stål": "Steel",

    # ── Swedish insulation ────────────────────────────────────
    "isolering": "Mineral wool insulation",
    "mineralull": "Mineral wool insulation",
    "glasull": "Glass wool insulation",
    "stenull": "Rock wool insulation",
    "cellplast": "EPS insulation",

    # ── Swedish masonry ───────────────────────────────────────
    "tegel": "Brick",
    "lättbetong": "Concrete block",
    "kalksandsten": "Calcium silicate unit",

    # ── Swedish gypsum ────────────────────────────────────────
    "gipsskiva": "Gypsum plasterboard, interiors",

    # ── Norwegian concrete ────────────────────────────────────
    "armert betong": "Ready-mix concrete, C25/30, GWP.REF",

    # ── Norwegian timber ──────────────────────────────────────
    "tre": "Sawn timber",
    "limtre": "GLT, Glued laminated timber",
    "krysslimt tre": "CLT, Cross laminated timber",
    "kryssfiner": "Plywood, spruce, uncoated",

    # ── Norwegian insulation ──────────────────────────────────
    "isolasjon": "Mineral wool insulation",
    "glassull": "Glass wool insulation",
    "steinull": "Rock wool insulation",
    "ekspandert polystyren": "EPS insulation",

    # ── Norwegian masonry ─────────────────────────────────────
    "tegl": "Brick",
    "lettbetong": "Concrete block",
}

# ─────────────────────────────────────────────────────────────
# REGEX PATTERNS FOR FINNISH AND INTERNATIONAL MATERIAL CODES
# ─────────────────────────────────────────────────────────────
REGEX_PATTERNS = [
    # Finnish concrete grades K20 to K60
    (r'\bk[2-6]\d\b', "Ready-mix concrete, C25/30, GWP.REF"),
    # European concrete grades C16/20 to C50/60
    (r'\bc[1-5]\d[/\-]\d{2}\b', "Ready-mix concrete, C25/30, GWP.REF"),
    # Steel grades S235 S275 S355 S420 S460
    (r'\bs[23456]\d{2}\b', "Steel"),
    # Finnish concrete element grades
    (r'\bby\s?\d+\b', "Ready-mix concrete, C25/30, GWP.REF"),
    # Timber grades T14 T18 T24 C14 C18 C24
    (r'\b[tc][1-3]\d\b', "Sawn timber"),
    # GLT grades GL24 GL28 GL30 GL32
    (r'\bgl[2-3]\d[ch]?\b', "GLT, Glued laminated timber"),
    # LVL grades
    (r'\blvl\s?\d+\b', "LVL, laminated veneer lumber for beams, posts, and panels"),
    # Insulation thickness like 100mm 150mm 200mm mineral wool
    (r'\b(villa|wool|erist)\w*\s*\d+\s*mm\b', "Mineral wool insulation"),
    # EPS XPS with thickness
    (r'\beps\s*\d+\b', "EPS insulation"),
    (r'\bxps\s*\d+\b', "XPS insulation"),
]


def apply_regex_patterns(name):
    name_lower = name.lower().strip()
    for pattern, result in REGEX_PATTERNS:
        if re.search(pattern, name_lower):
            return result
    return None


def fuzzy_match_material(raw_name):
    name_lower = raw_name.lower().strip()
    keys = list(MATERIAL_NORMALISE.keys())
    matches = get_close_matches(
        name_lower, keys, n=1, cutoff=0.72
    )
    if matches:
        return raw_name
    return None


# ─────────────────────────────────────────────────────────────
# CONFIDENCE SCORING
# ─────────────────────────────────────────────────────────────
def get_confidence(source):
    scores = {
        "direct_association": "High",
        "type_association": "High",
        "layer_set": "High",
        "constituent_set": "High",
        "profile_set": "High",
        "property_set": "Medium",
        "regex_match": "Medium",
        "fuzzy_match": "Medium",
        "object_type": "Low",
        "element_name": "Low",
        "unknown": "None"
    }
    return scores.get(source, "Low")


# ─────────────────────────────────────────────────────────────
# CORE MATERIAL EXTRACTION FROM IFC MATERIAL OBJECT
# ─────────────────────────────────────────────────────────────
def extract_names_from_material_object(mat):
    names = []
    try:
        if mat.is_a("IfcMaterial"):
            if mat.Name:
                names.append(mat.Name.strip())

        elif mat.is_a("IfcMaterialLayerSet"):
            for layer in mat.MaterialLayers or []:
                if layer.Material and layer.Material.Name:
                    names.append(layer.Material.Name.strip())

        elif mat.is_a("IfcMaterialLayerSetUsage"):
            ls = mat.ForLayerSet
            if ls:
                for layer in ls.MaterialLayers or []:
                    if layer.Material and layer.Material.Name:
                        names.append(
                            layer.Material.Name.strip()
                        )

        elif mat.is_a("IfcMaterialConstituentSet"):
            for c in mat.MaterialConstituents or []:
                if c.Material and c.Material.Name:
                    names.append(c.Material.Name.strip())

        elif mat.is_a("IfcMaterialProfileSet"):
            for p in mat.MaterialProfiles or []:
                if p.Material and p.Material.Name:
                    names.append(p.Material.Name.strip())

        elif mat.is_a("IfcMaterialProfileSetUsage"):
            fps = mat.ForProfileSet
            if fps:
                for p in fps.MaterialProfiles or []:
                    if p.Material and p.Material.Name:
                        names.append(p.Material.Name.strip())

        elif mat.is_a("IfcMaterialLayer"):
            if mat.Material and mat.Material.Name:
                names.append(mat.Material.Name.strip())

        elif mat.is_a("IfcMaterialList"):
            for m in mat.Materials or []:
                if m.Name:
                    names.append(m.Name.strip())

    except Exception:
        pass
    return names


def clean_material_name(name):
    if not name:
        return name
    import re
    # Strip trailing space + 4 or more digits
    # Examples:
    # "Stahlbeton 2747937872" → "Stahlbeton"
    # "Aluminium 131198" → "Aluminium"
    # "Kalksandstein 2816491304" → "Kalksandstein"
    cleaned = re.sub(r'\s+\d{6,}$', '', name.strip())
    # Strip trailing space + digits + letter codes
    cleaned = re.sub(r'\s+\d+[A-Z]*$', '', cleaned.strip())
    return cleaned.strip()


# ─────────────────────────────────────────────────────────────
# FULL MATERIAL EXTRACTION — ALL METHODS + TYPE LOOKUP
# ─────────────────────────────────────────────────────────────
def extract_material_name(element):
    names = []
    source = "unknown"

    # ── METHOD 1: Direct instance material association ────────
    try:
        for rel in getattr(element, "HasAssociations", []):
            if rel.is_a("IfcRelAssociatesMaterial"):
                found = extract_names_from_material_object(
                    rel.RelatingMaterial
                )
                if found:
                    names.extend(
                        clean_material_name(n) for n in found
                    )
                    source = "direct_association"
    except Exception:
        pass

    # ── METHOD 2: TYPE association (critical for Revit) ───────
    # Revit assigns materials to the TYPE not the instance
    if not names:
        try:
            for rel in getattr(element, "IsTypedBy", []):
                type_obj = rel.RelatingType
                for type_rel in getattr(
                    type_obj, "HasAssociations", []
                ):
                    if type_rel.is_a(
                        "IfcRelAssociatesMaterial"
                    ):
                        found = extract_names_from_material_object(
                            type_rel.RelatingMaterial
                        )
                        if found:
                            names.extend(
                                clean_material_name(n)
                                for n in found
                            )
                            source = "type_association"
        except Exception:
            pass

    # ── METHOD 3: Element name — priority for proxies ─────────
    # Moved up because architects name proxies descriptively
    if not names:
        try:
            elem_name = getattr(element, "Name", None)
            if elem_name and elem_name.strip():
                name_lower = elem_name.lower().strip()
                # Check if name contains a material keyword
                for keyword in MATERIAL_NORMALISE.keys():
                    if keyword in name_lower:
                        names.append(
                            clean_material_name(elem_name)
                        )
                        source = "element_name"
                        break
                # Also try regex
                if not names:
                    regex_result = apply_regex_patterns(
                        elem_name
                    )
                    if regex_result:
                        names.append(
                            clean_material_name(elem_name)
                        )
                        source = "element_name"
        except Exception:
            pass

    # ── METHOD 4: ObjectType ──────────────────────────────────
    if not names:
        try:
            obj_type = getattr(element, "ObjectType", None)
            if obj_type and obj_type.strip():
                name_lower = obj_type.lower().strip()
                for keyword in MATERIAL_NORMALISE.keys():
                    if keyword in name_lower:
                        names.append(
                            clean_material_name(obj_type)
                        )
                        source = "object_type"
                        break
        except Exception:
            pass

    # ── METHOD 5: Property sets ───────────────────────────────
    if not names:
        try:
            for definition in getattr(
                element, "IsDefinedBy", []
            ):
                if definition.is_a(
                    "IfcRelDefinesByProperties"
                ):
                    pset = (
                        definition.RelatingPropertyDefinition
                    )
                    if hasattr(pset, "HasProperties"):
                        for prop in pset.HasProperties:
                            pname = (
                                prop.Name.lower()
                                if prop.Name else ""
                            )
                            if any(
                                k in pname for k in [
                                    "material", "materiaali",
                                    "aine", "substance",
                                    "finish", "pinta"
                                ]
                            ):
                                if hasattr(
                                    prop, "NominalValue"
                                ) and prop.NominalValue:
                                    val = str(
                                        prop.NominalValue
                                        .wrappedValue
                                    ).strip()
                                    if val and len(val) > 1:
                                        names.append(
                                            clean_material_name(val)
                                        )
                                        source = "property_set"
        except Exception:
            pass

    # ── METHOD 6: Type property sets ─────────────────────────
    if not names:
        try:
            for rel in getattr(element, "IsTypedBy", []):
                type_obj = rel.RelatingType
                type_name = getattr(
                    type_obj, "Name", None
                )
                if type_name and type_name.strip():
                    for keyword in MATERIAL_NORMALISE.keys():
                        if keyword in type_name.lower():
                            names.append(
                                clean_material_name(type_name)
                            )
                            source = "object_type"
                            break
        except Exception:
            pass

    # ── METHOD 7: Regex on any collected name ─────────────────
    if not names:
        try:
            all_text = []
            elem_name = getattr(element, "Name", "") or ""
            obj_type = getattr(
                element, "ObjectType", ""
            ) or ""
            description = (
                getattr(element, "Description", "") or ""
            )
            all_text = [elem_name, obj_type, description]

            for text in all_text:
                if text.strip():
                    result = apply_regex_patterns(text)
                    if result:
                        names.append(
                            clean_material_name(text)
                        )
                        source = "regex_match"
                        break
        except Exception:
            pass

    # ── METHOD 8: Fuzzy match on element name ─────────────────
    if not names:
        try:
            elem_name = getattr(element, "Name", "") or ""
            if elem_name.strip():
                fuzzy = fuzzy_match_material(elem_name)
                if fuzzy:
                    names.append(
                        clean_material_name(fuzzy)
                    )
                    source = "fuzzy_match"
        except Exception:
            pass

    # ── FILTER AND RETURN BEST RESULT ─────────────────────────
    bad_names = {
        "", "none", "null", "undefined", "unknown",
        "default", "material", "standard", "<unnamed>",
        "unnamed", "unset", "-", "n/a", "not defined",
        "not set", "by category", "generic",
        "<by category>", "radial gradient fill",
        "gradient fill",

    }
    filtered = [
        n for n in names
        if n
        and n.lower().strip() not in bad_names
        and len(n.strip()) > 1
        and not n.lower().strip().startswith("generic -")
    ]

    if filtered:
        best = max(filtered, key=len)
        return best, source

    return "Unknown", "unknown"


# ─────────────────────────────────────────────────────────────
# VOLUME EXTRACTION — fast property methods first,
# geometry only as last resort for structural types.
# Returns (volume_m3: float, method: str)
# ─────────────────────────────────────────────────────────────

# Element types eligible for the slow geometry fallback.
# Doors, windows, furniture, flow elements etc. are excluded.
_GEOMETRY_ELIGIBLE = {
    "IfcWall", "IfcWallStandardCase",
    "IfcSlab", "IfcColumn", "IfcBeam", "IfcFooting",
}

_GEOM_TIMEOUT_S = 3  # seconds before giving up on one element


def _mesh_volume(verts, faces):
    """Signed tetrahedron formula on a triangulated mesh."""
    total = 0.0
    for i in range(0, len(faces), 3):
        i0, i1, i2 = faces[i], faces[i + 1], faces[i + 2]
        ax, ay, az = verts[i0*3], verts[i0*3+1], verts[i0*3+2]
        bx, by, bz = verts[i1*3], verts[i1*3+1], verts[i1*3+2]
        cx, cy, cz = verts[i2*3], verts[i2*3+1], verts[i2*3+2]
        total += (
            ax * (by * cz - bz * cy) -
            ay * (bx * cz - bz * cx) +
            az * (bx * cy - by * cx)
        ) / 6.0
    return abs(total)


def _geometry_volume(element, model):  # noqa: ARG001  model unused; kept for ThreadPoolExecutor signature
    """Run create_shape and return volume, or None on failure."""
    import ifcopenshell.geom
    settings = ifcopenshell.geom.settings()
    shape = ifcopenshell.geom.create_shape(settings, element)
    geom = shape.geometry
    verts = geom.verts
    faces = geom.faces
    if verts and faces and len(faces) >= 3:
        vol = _mesh_volume(verts, faces)
        if vol > 1e-9:
            return round(vol, 4)
    return None


def correct_volume_units(volume, element_type):
    if volume <= 0:
        return volume

    # Thresholds above which a value is almost certainly in dm³
    # and must be divided by 1000 to get m³.
    dm3_threshold = {
        "IfcSlab": 50,
        "IfcWall": 30,
        "IfcWallStandardCase": 30,
        "IfcColumn": 5,
        "IfcBeam": 5,
        "IfcFooting": 50,
        "IfcRoof": 50,
    }

    threshold = dm3_threshold.get(element_type, 20)

    if volume > threshold:
        return round(volume / 1000, 4)
    return volume


def _extract_volume_raw(element, model=None):
    """Return (volume_m3, method_label).

    Fast methods are tried first on every element:
      1. quantity  — IfcQuantityVolume in any quantity set
      2. pset      — named volume property in property sets
      3. dims      — area × thickness/height from quantities
      4. util_pset — ifcopenshell.util.element.get_psets scan

    Geometry (create_shape) is only attempted when:
      - all fast methods returned nothing, AND
      - the element type is in _GEOMETRY_ELIGIBLE, AND
      - model is provided
    A 3-second per-element timeout protects against hangs.
    """

    # ── METHOD 1: IfcQuantityVolume (any quantity set) ────────
    try:
        for definition in getattr(
            element, "IsDefinedBy", []
        ):
            if definition.is_a(
                "IfcRelDefinesByQuantities"
            ):
                qset = definition.RelatingQuantity
                for qty in getattr(
                    qset, "Quantities", []
                ) or []:
                    if qty.is_a("IfcQuantityVolume"):
                        v = qty.VolumeValue
                        if v and float(v) > 0:
                            return round(float(v), 4), "quantity"
    except Exception:
        pass

    # ── METHOD 2: Property set volume values ──────────────────
    try:
        for definition in getattr(
            element, "IsDefinedBy", []
        ):
            if definition.is_a(
                "IfcRelDefinesByProperties"
            ):
                pset = (
                    definition.RelatingPropertyDefinition
                )
                if hasattr(pset, "HasProperties"):
                    for prop in pset.HasProperties:
                        pname = (
                            prop.Name.lower()
                            if prop.Name else ""
                        )
                        if any(
                            k in pname for k in [
                                "volume", "tilavuus",
                                "vol", "netvolume",
                                "grossvolume"
                            ]
                        ):
                            if hasattr(
                                prop, "NominalValue"
                            ) and prop.NominalValue:
                                try:
                                    v = float(
                                        prop.NominalValue
                                        .wrappedValue
                                    )
                                    if v > 0:
                                        return round(v, 4), "pset"
                                except Exception:
                                    pass
    except Exception:
        pass

    # ── METHOD 3: Dimensional estimation ──────────────────────
    try:
        dims = {}
        for definition in getattr(
            element, "IsDefinedBy", []
        ):
            if definition.is_a(
                "IfcRelDefinesByQuantities"
            ):
                qset = definition.RelatingQuantity
                for qty in getattr(
                    qset, "Quantities", []
                ) or []:
                    qname = (
                        qty.Name.lower()
                        if qty.Name else ""
                    )
                    if qty.is_a("IfcQuantityLength"):
                        if any(
                            k in qname for k in [
                                "length", "pituus"
                            ]
                        ):
                            dims["length"] = float(
                                qty.LengthValue
                            )
                        elif any(
                            k in qname for k in [
                                "width", "leveys"
                            ]
                        ):
                            dims["width"] = float(
                                qty.LengthValue
                            )
                        elif any(
                            k in qname for k in [
                                "height", "korkeus",
                                "depth", "syvyys"
                            ]
                        ):
                            dims["height"] = float(
                                qty.LengthValue
                            )
                        elif any(
                            k in qname for k in [
                                "thickness", "paksuus"
                            ]
                        ):
                            dims["thickness"] = float(
                                qty.LengthValue
                            )
                    elif qty.is_a("IfcQuantityArea"):
                        if any(
                            k in qname for k in [
                                "area", "pinta", "net"
                            ]
                        ):
                            dims["area"] = float(
                                qty.AreaValue
                            )

        if "area" in dims and "thickness" in dims:
            v = dims["area"] * dims["thickness"]
            if v > 0:
                return round(v, 4), "dims"
        if "area" in dims and "height" in dims:
            v = dims["area"] * dims["height"]
            if v > 0:
                return round(v, 4), "dims"
        if all(
            k in dims for k in [
                "length", "width", "height"
            ]
        ):
            v = (
                dims["length"] *
                dims["width"] *
                dims["height"]
            )
            if v > 0:
                return round(v, 4), "dims"
        if all(
            k in dims for k in [
                "length", "width", "thickness"
            ]
        ):
            v = (
                dims["length"] *
                dims["width"] *
                dims["thickness"]
            )
            if v > 0:
                return round(v, 4), "dims"
    except Exception:
        pass

    # ── METHOD 4: ifcopenshell utility pset scan ──────────────
    try:
        psets = ifcopenshell.util.element.get_psets(element)
        for pset_props in psets.values():
            for prop_name, prop_val in pset_props.items():
                if isinstance(prop_val, (int, float)):
                    if any(
                        k in prop_name.lower() for k in [
                            "volume", "vol", "tilavuus"
                        ]
                    ):
                        if float(prop_val) > 0:
                            return round(
                                float(prop_val), 4
                            ), "util_pset"
    except Exception:
        pass

    # ── METHOD 5: Geometry — last resort, structural only ─────
    # Skipped for doors, windows, furniture, flow elements etc.
    # A ThreadPoolExecutor enforces the per-element timeout so
    # this never blocks the main thread for more than 3 seconds.
    if model is not None and element.is_a() in _GEOMETRY_ELIGIBLE:
        try:
            from concurrent.futures import (
                ThreadPoolExecutor, TimeoutError as FuturesTimeout
            )
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    _geometry_volume, element, model
                )
                vol = future.result(timeout=_GEOM_TIMEOUT_S)
            if vol is not None:
                return vol, "geometry"
        except (FuturesTimeout, Exception):
            pass

    return 0.0, "none"


def extract_volume(element, model=None):
    """Return (volume_m3, method_label) with unit correction applied."""
    volume, method = _extract_volume_raw(element, model)
    volume = correct_volume_units(volume, element.is_a())
    return volume, method


def _correct_volume_units(volume):
    """Return (corrected_volume, was_corrected).

    A single IFC element volume > 500 m³ is almost certainly
    exported in non-standard units:
      - 500 < v < 500 000  → divide by 100  (dm³ → m³)
      - v >= 500 000       → divide by 1 000 000  (mm³ → m³)
    """
    if volume <= 0 or volume <= 500:
        return volume, False
    if volume < 500_000:
        return round(volume / 100, 4), True
    return round(volume / 1_000_000, 4), True


# ─────────────────────────────────────────────────────────────
# STOREY EXTRACTION
# ─────────────────────────────────────────────────────────────
def extract_storey(element):
    try:
        for rel in getattr(
            element, "ContainedInStructure", []
        ):
            container = rel.RelatingStructure
            if container.is_a("IfcBuildingStorey"):
                name = getattr(container, "Name", None)
                if name and name.strip():
                    return name.strip()
                elev = getattr(
                    container, "Elevation", None
                )
                if elev is not None:
                    return f"Level {round(float(elev), 1)}m"
                return "Storey"
            elif container.is_a("IfcBuilding"):
                return "Building level"
            elif container.is_a("IfcSite"):
                return "Site level"
    except Exception:
        pass

    # Walk decomposition tree
    try:
        def find_storey(elem, depth=0):
            if depth > 8:
                return None
            for rel in getattr(elem, "Decomposes", []):
                parent = rel.RelatingObject
                if parent.is_a("IfcBuildingStorey"):
                    name = getattr(parent, "Name", None)
                    return (
                        name.strip()
                        if name else "Storey"
                    )
                result = find_storey(parent, depth + 1)
                if result:
                    return result
            return None
        result = find_storey(element)
        if result:
            return result
    except Exception:
        pass

    return "Unknown"


# ─────────────────────────────────────────────────────────────
# ELEMENT TYPE CLEANER
# ─────────────────────────────────────────────────────────────
def clean_element_type(ifc_type):
    type_map = {
        "IfcWall": "Wall",
        "IfcWallStandardCase": "Wall",
        "IfcSlab": "Slab",
        "IfcColumn": "Column",
        "IfcBeam": "Beam",
        "IfcFooting": "Footing",
        "IfcPile": "Pile",
        "IfcStair": "Stair",
        "IfcStairFlight": "Stair flight",
        "IfcRoof": "Roof",
        "IfcPlate": "Plate",
        "IfcMember": "Member",
        "IfcCovering": "Covering",
        "IfcDoor": "Door",
        "IfcWindow": "Window",
        "IfcRailing": "Railing",
        "IfcBuildingElementProxy": "Building element",
        "IfcFlowSegment": "Flow segment",
        "IfcFlowFitting": "Flow fitting",
        "IfcFlowTerminal": "Flow terminal",
        "IfcFurnishingElement": "Furnishing",
        "IfcCurtainWall": "Curtain wall",
    }
    return type_map.get(
        ifc_type, ifc_type.replace("Ifc", "")
    )


# ─────────────────────────────────────────────────────────────
# FLOOR AREA DETECTION
# Tries 4 progressively looser methods and returns the first
# result that yields a plausible value (> 0 m²).
# Returns (area_m2: float, method: str) or (None, None).
# ─────────────────────────────────────────────────────────────
_AREA_KEYS = [
    "GrossFloorArea", "NetFloorArea",
    "TotalFloorArea", "FloorArea", "Area",
]


def _pset_area(entity):
    """Return the first positive area value found in any pset."""
    try:
        psets = ifcopenshell.util.element.get_psets(entity)
        for props in psets.values():
            for key in _AREA_KEYS:
                val = props.get(key)
                if isinstance(val, (int, float)) and float(val) > 0:
                    return float(val)
    except Exception:
        pass
    return None


def _qset_area(entity):
    """Return the first positive IfcQuantityArea from quantity sets."""
    try:
        for rel in getattr(entity, "IsDefinedBy", []):
            if not rel.is_a("IfcRelDefinesByQuantities"):
                continue
            for qty in getattr(
                rel.RelatingQuantity, "Quantities", []
            ) or []:
                if qty.is_a("IfcQuantityArea"):
                    v = float(qty.AreaValue)
                    if v > 0:
                        return v
    except Exception:
        pass
    return None


def get_building_floor_area(model):
    """Detect gross floor area from the IFC model.

    Returns (area_m2: float, method: str) or (None, None).
    """
    # ── Method 1: IfcBuilding property sets ──────────────────
    try:
        for building in model.by_type("IfcBuilding"):
            area = _pset_area(building)
            if area:
                return round(area, 1), "IfcBuilding property set"
    except Exception:
        pass

    # ── Method 2: Sum IfcBuildingStorey areas ─────────────────
    try:
        total = 0.0
        for storey in model.by_type("IfcBuildingStorey"):
            area = _pset_area(storey)
            if area:
                total += area
        if total > 0:
            return round(total, 1), "Sum of building storey areas"
    except Exception:
        pass

    # ── Method 3: Sum IfcSpace areas ─────────────────────────
    try:
        total = 0.0
        for space in model.by_type("IfcSpace"):
            area = _pset_area(space)
            if area:
                total += area
        if total > 0:
            return round(total, 1), "Sum of IfcSpace net floor areas"
    except Exception:
        pass

    # ── Method 4: Sum ground-floor IfcSlab areas ──────────────
    try:
        _GROUND_HINTS = {
            "ground", "gr", "gf", "00", "0 ", " 0",
            "erdgeschoss", "erd", "1st", "kelleri",
            "pohjakerros", "1. kerros",
        }
        total = 0.0
        for slab in model.by_type("IfcSlab"):
            storey_name = ""
            for rel in getattr(
                slab, "ContainedInStructure", []
            ):
                container = rel.RelatingStructure
                if container.is_a("IfcBuildingStorey"):
                    storey_name = (
                        getattr(container, "Name", "") or ""
                    ).lower()
                    break
            is_ground = any(
                h in storey_name for h in _GROUND_HINTS
            ) or storey_name == ""
            if not is_ground:
                continue
            area = _pset_area(slab) or _qset_area(slab)
            if area:
                total += area
        if total > 0:
            return round(total, 1), "Sum of ground-floor slab areas"
    except Exception:
        pass

    return None, None


# ─────────────────────────────────────────────────────────────
# MAIN PARSER
# ─────────────────────────────────────────────────────────────
def parse_ifc(filepath):
    global DETECTED_FLOOR_AREA
    model = ifcopenshell.open(filepath)
    DETECTED_FLOOR_AREA = get_building_floor_area(model)
    rows = []
    seen_ids = set()

    for ifc_type in TARGET_TYPES:
        try:
            elements = model.by_type(ifc_type)
        except Exception:
            continue

        for element in elements:
            try:
                elem_id = element.GlobalId
                if elem_id in seen_ids:
                    continue
                seen_ids.add(elem_id)

                material, mat_source = (
                    extract_material_name(element)
                )
                volume, vol_method = extract_volume(
                    element, model
                )
                volume, vol_corrected = _correct_volume_units(
                    volume
                )
                storey = extract_storey(element)
                elem_type = clean_element_type(
                    element.is_a()
                )
                name = (
                    getattr(element, "Name", "") or ""
                )
                description = (
                    getattr(
                        element, "Description", ""
                    ) or ""
                )
                confidence = get_confidence(mat_source)

                rows.append({
                    "element_id": elem_id,
                    "element_type": elem_type,
                    "name": name.strip(),
                    "description": description.strip(),
                    "material": material,
                    "volume_m3": volume,
                    "volume_method": vol_method,
                    "volume_unit_corrected": vol_corrected,
                    "storey": storey,
                    "ifc_type": element.is_a(),
                    "material_source": mat_source,
                    "confidence": confidence
                })

            except Exception:
                continue

    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame(columns=[
            "element_id", "element_type", "name",
            "description", "material", "volume_m3",
            "volume_method", "volume_unit_corrected",
            "storey", "ifc_type", "material_source",
            "confidence"
        ])

    return df.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────
# SUMMARY HELPER
# ─────────────────────────────────────────────────────────────
def get_summary(df):
    if df.empty:
        return {
            "total_elements": 0,
            "unique_materials": 0,
            "missing_material": 0,
            "missing_volume": 0,
            "missing_storey": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "element_types": []
        }
    return {
        "total_elements": len(df),
        "unique_materials": df[
            df["material"] != "Unknown"
        ]["material"].nunique(),
        "missing_material": int(
            (df["material"] == "Unknown").sum()
        ),
        "missing_volume": int(
            (df["volume_m3"] == 0).sum()
        ),
        "missing_storey": int(
            (df["storey"] == "Unknown").sum()
        ),
        "high_confidence": int(
            (df.get("confidence", "") == "High").sum()
        ) if "confidence" in df.columns else 0,
        "medium_confidence": int(
            (df.get("confidence", "") == "Medium").sum()
        ) if "confidence" in df.columns else 0,
        "low_confidence": int(
            (df.get("confidence", "") == "Low").sum()
        ) if "confidence" in df.columns else 0,
        "element_types": (
            df["element_type"].unique().tolist()
        )
    }


# ─────────────────────────────────────────────────────────────
# IFC QUALITY REPORT
# ─────────────────────────────────────────────────────────────
def _detect_software(df):
    """Heuristic: guess authoring software from name/type patterns."""
    elem_names_lower = df["name"].fillna("").str.lower()

    # Revit: "basic wall", "generic -", object-type strings,
    #        or material_source via property_set only
    revit_signals = (
        elem_names_lower.str.contains(
            r"basic wall|basic roof|generic -|curtain wall",
            regex=True
        ).sum()
    )
    # Archicad: composite names with "/" or "AC_" prefix,
    #           or names like "Wall-001", "Slab-001"
    archicad_signals = (
        elem_names_lower.str.contains(
            r"\bac_|\barchicad\b|wall-\d+|slab-\d+|beam-\d+",
            regex=True
        ).sum()
    )
    # Tekla: uppercase profile names like "HEA200", "IPE300",
    #        or names matching "COLUMN\d" / "BEAM\d"
    tekla_signals = (
        elem_names_lower.str.contains(
            r"\b(hea|heb|ipe|chs|rhs|shs)\d+\b|"
            r"\bbeam\d|\bcolumn\d|\btekla\b",
            regex=True
        ).sum()
    )

    scores = {
        "Revit": int(revit_signals),
        "Archicad": int(archicad_signals),
        "Tekla Structures": int(tekla_signals),
    }
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "Unknown"
    return best


def get_quality_report(df):
    """Return a quality-report dict for the parsed IFC dataframe.

    Quality score (0-100):
      -2 per missing material   (cap  40)
      -1 per missing volume     (cap  20)
      -1 per missing storey     (cap  10)
      -20 if >50 % elements unmatched
      -10 if no quantity data at all
    """
    if df is None or df.empty:
        return {
            "quality_score": 0,
            "total_elements": 0,
            "matched_materials": {"count": 0, "pct": 0},
            "missing_materials": {"count": 0, "pct": 0},
            "missing_volumes": {"count": 0, "pct": 0},
            "missing_storeys": {"count": 0, "pct": 0},
            "defaulted_elements": 0,
            "element_type_breakdown": {},
            "top_issues": ["No elements found in the IFC file"],
            "software_hint": "Unknown",
        }

    total = len(df)

    missing_mat_mask  = df["material"] == "Unknown"
    missing_vol_mask  = df["volume_m3"] == 0
    missing_stor_mask = df["storey"] == "Unknown"

    n_missing_mat  = int(missing_mat_mask.sum())
    n_missing_vol  = int(missing_vol_mask.sum())
    n_missing_stor = int(missing_stor_mask.sum())
    n_matched      = total - n_missing_mat

    # defaulted_elements: present only after carbon calc;
    # ifc_df won't have match_status, so guard with get
    n_defaulted = int(
        (df.get("match_status", pd.Series(dtype=str))
         == "defaulted_by_type").sum()
    )

    pct = lambda n: round(n / total * 100, 1) if total > 0 else 0.0

    # ── quality score ────────────────────────────────────────
    score = 100
    score -= min(n_missing_mat * 2,  40)
    score -= min(n_missing_vol * 1,  20)
    score -= min(n_missing_stor * 1, 10)
    if total > 0 and n_missing_mat / total > 0.5:
        score -= 20
    no_quantities = (
        "volume_method" in df.columns
        and (df["volume_method"] == "none").all()
    )
    if no_quantities:
        score -= 10
    score = max(0, score)

    # ── element type breakdown (missing materials per type) ──
    type_breakdown = (
        df[missing_mat_mask]
        .groupby("element_type")
        .size()
        .to_dict()
    )

    # ── top issues ───────────────────────────────────────────
    issues = []
    if n_missing_mat > 0:
        issues.append(
            f"{n_missing_mat} elements ({pct(n_missing_mat):.0f}%) "
            f"have no material assigned"
        )
    if n_missing_vol > 0:
        issues.append(
            f"{n_missing_vol} elements ({pct(n_missing_vol):.0f}%) "
            f"have no volume / quantity data"
        )
    if n_missing_stor > 0:
        issues.append(
            f"{n_missing_stor} elements ({pct(n_missing_stor):.0f}%) "
            f"have no storey assignment"
        )
    if no_quantities:
        issues.append(
            "No quantity sets exported — enable base quantities "
            "in your IFC export settings"
        )
    if not issues:
        issues.append("No critical issues found")
    top_issues = issues[:3]

    return {
        "quality_score": score,
        "total_elements": total,
        "matched_materials": {
            "count": n_matched, "pct": pct(n_matched)
        },
        "missing_materials": {
            "count": n_missing_mat, "pct": pct(n_missing_mat)
        },
        "missing_volumes": {
            "count": n_missing_vol, "pct": pct(n_missing_vol)
        },
        "missing_storeys": {
            "count": n_missing_stor, "pct": pct(n_missing_stor)
        },
        "defaulted_elements": n_defaulted,
        "element_type_breakdown": type_breakdown,
        "top_issues": top_issues,
        "software_hint": _detect_software(df),
    }