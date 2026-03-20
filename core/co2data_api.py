import requests
import pandas as pd

CO2DATA_URL = "https://co2data.fi/api/co2data_construction.json"
CONSERVATIVE_FACTOR = 1.2

EXACT_NAME_MAP = {
    "concrete": "Ready-mix concrete, C25/30",
    "betoni": "Ready-mix concrete, C25/30",
    "beton": "Ready-mix concrete, C25/30",
    "c20": "Ready-mix concrete, C20/25",
    "c20/25": "Ready-mix concrete, C20/25",
    "c25": "Ready-mix concrete, C25/30",
    "c25/30": "Ready-mix concrete, C25/30",
    "c30": "Ready-mix concrete, C30/37",
    "c30/37": "Ready-mix concrete, C30/37",
    "c35": "Ready-mix concrete, C35/45",
    "c35/45": "Ready-mix concrete, C35/45",
    "c40": "Ready-mix concrete, C40/50",
    "c40/50": "Ready-mix concrete, C40/50",
    "c45": "Ready-mix concrete, C45/55",
    "c45/55": "Ready-mix concrete, C45/55",
    "c50": "Ready-mix concrete, C50/60",
    "c50/60": "Ready-mix concrete, C50/60",
    "ready-mix": "Ready-mix concrete, C25/30",
    "ready mix": "Ready-mix concrete, C25/30",
    "reinforced concrete": "Ready-mix concrete, C30/37",
    "teräsbetoni": "Ready-mix concrete, C30/37",
    "stahlbeton": "Ready-mix concrete, C30/37",
    "raudoitettu betoni": "Ready-mix concrete, C30/37",
    "hollow core 200": "Precast concrete, hollow core slab 200 mm",
    "hollow core 265": "Precast concrete, hollow core slab 265 mm",
    "hollow core 320": "Precast concrete, hollow core slab 320 mm",
    "hollow core 370": "Precast concrete, hollow core slab 370 mm",
    "hollow core 400": "Precast concrete, hollow core slab 400 mm",
    "hollow core 500": "Precast concrete, hollow core slab 500 mm",
    "ontelolaatta": "Precast concrete, hollow core slab 265 mm",
    "hollow core": "Precast concrete, hollow core slab 265 mm",
    "sandwich wall": "Precast concrete, sandwich, exterior wall 150+220+80 mm",
    "sandwich elementti": "Precast concrete, sandwich, exterior wall 150+220+80 mm",
    "julkisivuelementti": "Precast concrete, sandwich, exterior wall 150+220+80 mm",
    "precast beam": "Precast concrete, beam 480 x 380 mm",
    "precast column": "Precast concrete, column 380 x 380 mm",
    "precast": "Precast concrete, hollow core slab 265 mm",
    "elementti": "Precast concrete, hollow core slab 265 mm",
    "aac": "Autoclaved aerated concrete block, exterior walls",
    "ytong": "Autoclaved aerated concrete block, exterior walls",
    "siporex": "Autoclaved aerated concrete block, exterior walls",
    "kevytbetoni": "Autoclaved aerated concrete block, exterior walls",
    "autoclaved": "Autoclaved aerated concrete block, exterior walls",
    "structural steel": "Structural steel for load bearing structure",
    "steel": "Structural steel for load bearing structure",
    "teräs": "Structural steel for load bearing structure",
    "stahl": "Structural steel for load bearing structure",
    "s235": "Structural steel for load bearing structure",
    "s275": "Structural steel for load bearing structure",
    "s355": "Structural steel for load bearing structure",
    "s420": "Structural steel for load bearing structure",
    "hea": "Structural steel for load bearing structure",
    "heb": "Structural steel for load bearing structure",
    "rhs": "Structural steel for load bearing structure",
    "chs": "Structural steel for load bearing structure",
    "steel profile": "Steel profile, 100 % scrap-based",
    "recycled steel": "Steel profile, 100 % scrap-based",
    "eaf steel": "Steel profile, 100 % scrap-based",
    "steel pile": "Steel pile",
    "teräspaalu": "Steel pile",
    "rebar": "Steel rebar for concrete reinforcement",
    "reinforcement": "Steel rebar for concrete reinforcement",
    "harjateräs": "Steel rebar for concrete reinforcement",
    "raudoitus": "Steel rebar for concrete reinforcement",
    "b500": "Steel rebar for concrete reinforcement",
    "a500": "Steel rebar for concrete reinforcement",
    "stainless steel": "Stainless steel sheet",
    "stainless rebar": "Stainless steel rebar",
    "glulam": "GLT, Glued laminated timber",
    "glt": "GLT, Glued laminated timber",
    "liimapuu": "GLT, Glued laminated timber",
    "bsh": "GLT, Glued laminated timber",
    "gl24": "GLT, Glued laminated timber",
    "gl30": "GLT, Glued laminated timber",
    "clt": "CLT, Cross laminated timber",
    "cross laminated": "CLT, Cross laminated timber",
    "ristikkoliimapuu": "CLT, Cross laminated timber",
    "lvl beam": "LVL, laminated veneer lumber for beams, posts, and panels",
    "lvl wall": "LVL, laminated veneer lumber for wall studs",
    "lvl": "LVL, laminated veneer lumber for beams, posts, and panels",
    "kerto": "LVL, laminated veneer lumber for beams, posts, and panels",
    "viilupuu": "LVL, laminated veneer lumber for beams, posts, and panels",
    "glvl": "GLVL, multiple glued laminated veneer lumber",
    "sawn timber": "Sawn timber",
    "sahatavara": "Sawn timber",
    "timber": "Sawn timber",
    "wood": "Sawn timber",
    "puu": "Sawn timber",
    "holz": "Sawn timber",
    "softwood": "Sawn timber",
    "pine": "Sawn timber",
    "spruce": "Sawn timber",
    "kuusi": "Sawn timber",
    "mänty": "Sawn timber",
    "planed timber": "Sawn timber, planed",
    "log wall": "Solid log wall structure",
    "laminated log": "Laminated log wall structure",
    "hirsiseinä": "Solid log wall structure",
    "plywood spruce": "Plywood, spruce, uncoated",
    "plywood birch": "Plywood, birch, uncoated",
    "plywood": "Plywood, spruce, uncoated",
    "vaneri": "Plywood, spruce, uncoated",
    "osb": "OSB panel",
    "chipboard": "Chipboard",
    "mdf": "Fibreboard, medium density, mdf",
    "fibreboard": "Fibreboard, hard",
    "mineral wool 20": "Glass wool insulation, density 20 kg/m3",
    "mineral wool 60": "Glass wool insulation, density 60 kg/m3",
    "mineral wool 100": "Glass wool insulation, density 100 kg/m3",
    "glass wool 20": "Glass wool insulation, density 20 kg/m3",
    "glass wool 60": "Glass wool insulation, density 60 kg/m3",
    "glass wool 100": "Glass wool insulation, density 100 kg/m3",
    "glass wool": "Glass wool insulation, density 20 kg/m3",
    "lasivillalevy": "Glass wool insulation, density 20 kg/m3",
    "stone wool facade": "Stone wool insulation for facades, density 61 kg/m3",
    "stone wool roof": "Stone wool insulation for roofs, density 63 kg/m3",
    "stone wool 30": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "stone wool 33": "Stone wool insulation, blowing, average density 33 kg/m3",
    "stone wool": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "kivivilla": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "rockwool": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "paroc": "Stone wool insulation for facades, density 61 kg/m3",
    "isover": "Glass wool insulation, density 20 kg/m3",
    "mineral wool": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "mineraalivilla": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "villa": "Stone wool, low-density for general building insulation, average density 30 kg/m3",
    "eps": "EPS insulation",
    "polystyrene": "EPS insulation",
    "polystyreeni": "EPS insulation",
    "styrox": "EPS insulation",
    "thermisol": "EPS insulation",
    "xps": "XPS-insulation",
    "finnfoam": "XPS-insulation",
    "extruded polystyrene": "XPS-insulation",
    "pu insulation": "PU-insulation",
    "pur": "PU-insulation",
    "pir": "Phenolic insulation, aluminum foil coating, 40-200mm",
    "phenolic": "Phenolic insulation, aluminum foil coating, 40-200mm",
    "cellulose insulation board": "Cellulose insulation board",
    "cellulose loose": "Cellulose insulation, loose-fill",
    "cellulose": "Cellulose insulation board",
    "puukuitu": "Cellulose insulation board",
    "wood fibre": "Cellulose insulation board",
    "gypsum plasterboard": "Gypsum plasterboard, interiors",
    "gypsum board": "Gypsum plasterboard, interiors",
    "gypsum fire": "Gypsum plasterboard, hard, fire resistant",
    "gypsum wind": "Gypsum plasterboard, wind shield",
    "plasterboard": "Gypsum plasterboard, interiors",
    "kipsilevy": "Gypsum plasterboard, interiors",
    "gyproc": "Gypsum plasterboard, interiors",
    "knauf": "Gypsum plasterboard, interiors",
    "drywall": "Gypsum plasterboard, interiors",
    "gypsum": "Gypsum plasterboard, interiors",
    "kipsi": "Gypsum plasterboard, interiors",
    "plastering mortar": "Plastering mortar",
    "general mortar": "General mortar",
    "mortar": "General mortar",
    "laasti": "General mortar",
    "masonry mortar": "Masonry mortar",
    "element joint mortar": "Element joint mortar",
    "screed cement": "Screed, cement-based",
    "screed": "Screed, cement-based",
    "tasoitus": "Screed, cement-based",
    "brick red": "Brick, red",
    "clay brick": "Brick, red",
    "brick": "Brick, red",
    "tiili": "Brick, red",
    "polttotiili": "Brick, red",
    "wienerberger": "Brick, red",
    "light brick": "Brick, light",
    "kevyttiili": "Brick, light",
    "calcium silicate": "Calcium silicate brick",
    "kalkkihiekkatiili": "Calcium silicate brick",
    "kalksandstein": "Calcium silicate brick",
    "float glass": "Float glass",
    "glass": "Float glass",
    "lasi": "Float glass",
    "glazing": "Insulating glass unit",
    "insulating glass": "Insulating glass unit",
    "triple glazed": "Window, wood-aluminium, triple-glazed",
    "kolmilasi": "Window, wood-aluminium, triple-glazed",
    "coated glass": "Coated glass",
    "laminated glass": "Laminated glass",
    "toughened glass": "Thermally toughened glass",
    "glass facade": "Glass-aluminium facade, triple-glazed",
    "aluminium profile": "Aluminium profile, -tube or -rod, extruded, scrap 0%",
    "aluminium sheet": "Aluminium sheet for walls and ceilings, scrap 0%",
    "aluminium recycled": "Aluminium profile, scrap 100%",
    "aluminium": "Aluminium profile, -tube or -rod, extruded, scrap 0%",
    "aluminum": "Aluminium profile, -tube or -rod, extruded, scrap 0%",
    "alumiini": "Aluminium profile, -tube or -rod, extruded, scrap 0%",
    "alu": "Aluminium profile, -tube or -rod, extruded, scrap 0%",
    "copper sheet": "Copper sheet",
    "copper tube": "Copper tube",
    "copper wire": "Copper wire",
    "copper": "Copper sheet",
    "kupari": "Copper sheet",
    "kupfer": "Copper sheet",
    "fibre cement": "Fibre cement board",
    "kuitusementti": "Fibre cement board",
    "ceramic floor": "Ceramic tile for floors",
    "ceramic wall": "Ceramic tile for walls",
    "ceramic": "Ceramic tile for floors",
    "laatta": "Ceramic tile for floors",
    "tile": "Ceramic tile for floors",
    "glass tile": "Glass tile",
    "parquet": "Flooring, parquet",
    "vinyl flooring": "Vinyl flooring",
    "textile flooring": "Textile flooring, polyamide",
    "bitumen membrane": "Bitumen waterproofing membrane, top layer membrane, TL2",
    "bitumen": "Bitumen waterproofing membrane, top layer membrane, TL2",
    "bituumi": "Bitumen waterproofing membrane, top layer membrane, TL2",
    "roofing membrane": "Bitumen waterproofing membrane, continuous roofing system",
    "epdm": "Bitumen waterproofing membrane, single-ply roofing system, TL1",
    "pvc pipe": "Electric cable protecting pipe, PVC",
    "pvc": "Electric cable protecting pipe, PVC",
    "pe pipe": "Drinking water pipe, PEX",
    "pex": "Drinking water pipe, PEX",
    "gravel": "Gravel and sand",
    "sand": "Gravel and sand",
    "hiekka": "Gravel and sand",
    "sora": "Gravel and sand",
    "crushed rock": "Crushed rock",
    "murske": "Crushed rock",
    "crushed concrete": "Crushed concrete",
    "fly ash": "Fly ash",
    "lentotuhka": "Fly ash",
    "natural stone tile": "Natural stone, tile for facades and floors",
    "natural stone": "Natural stone, tile for facades and floors",
    "granite": "Natural stone, tile for facades and floors",
    "graniitti": "Natural stone, tile for facades and floors",
    "slate": "Natural stone, slate for facades and yard",
    "stone paving": "Natural stone, rectangular paving stone",
    "concrete pile": "Concrete pile RTB-300",
    "betonipaalut": "Concrete pile RTB-300",
    "concrete block": "Concrete block, insulated, U=0.17 W/m2K",
    "concrete paving": "Concrete paving block",
    "concrete roofing tile": "Concrete roofing tile",
    "sandwich panel steel": "Sandwich panel, steel, mineral wool insulation",
    "steel sandwich": "Sandwich panel, steel, mineral wool insulation",
    "color coated steel": "Color coated steel sheet profile",
    "profiled steel sheet": "Color coated steel sheet profile",
    "trapeziblatt": "Color coated steel sheet profile",
    "light steel": "Metal coated light-weight steel profile or grill",
    "partition glass": "Partition wall, glass with aluminium frame",
    "door wooden": "Door, outdoor, wooden with wooden frame",
    "door metal": "Door, metallic, fire-rated",
    "door glass": "Door, outdoor, glass with aluminium frame",
    "window": "Window, wood-aluminium, triple-glazed",
    "ikkuna": "Window, wood-aluminium, triple-glazed",
    "paint exterior": "Paint, acrylic, water-borne for exterior use",
    "paint interior": "Paint, acrylic, water-borne for interior use",
    "paint": "Paint, acrylic, water-borne for interior use",
    "maali": "Paint, acrylic, water-borne for interior use",
    "geotextile": "Geotextile, PP-based",
    "geotekstiili": "Geotextile, PP-based",
    "solar panel": "Solar panel, monocrystalline",
    "aurinkopaneeli": "Solar panel, monocrystalline",
    "heat pump": "Heat pump, air to air",
    "lämpöpumppu": "Heat pump, air to air",
}

_cache = None
_resource_index = None


def fetch_co2data():
    global _cache, _resource_index
    if _cache is not None:
        return _cache
    try:
        response = requests.get(CO2DATA_URL, timeout=15)
        if response.status_code == 200:
            data = response.json()
            resources = data.get("Resources", [])
            _cache = resources
            _resource_index = {
                r.get("Name", "").lower(): r
                for r in resources
            }
            return _cache
    except Exception as e:
        print(f"CO2data fetch error: {e}")
    return None


def get_resource_index():
    global _resource_index
    if _resource_index is None:
        fetch_co2data()
    return _resource_index or {}


def get_gwp_value(resource, module="A1-A3 Conservative"):
    try:
        data_items = resource.get("DataItems", {})
        values = data_items.get("DataValueItems", [])
        for item in values:
            if item.get("DataModuleCode") == module:
                val = item.get("Value")
                if val is not None and val > 0:
                    return val
    except Exception:
        pass
    return None


def get_density(resource):
    try:
        conversions = resource.get("Conversions", [])
        for conv in conversions:
            if conv.get("Field") == "Volume":
                return conv.get("Value")
    except Exception:
        pass
    return None


def get_finnish_carbon_value(material_name):
    fetch_co2data()
    index = get_resource_index()
    if not index:
        return None

    name_lower = material_name.lower().strip()

    target_name = None
    for keyword, mapped in EXACT_NAME_MAP.items():
        if keyword in name_lower:
            target_name = mapped
            break

    if not target_name:
        return None

    resource = index.get(target_name.lower())
    if not resource:
        for key, res in index.items():
            if target_name.lower() in key:
                resource = res
                break

    if not resource:
        return None

    conservative = get_gwp_value(resource, "A1-A3 Conservative")
    typical = get_gwp_value(resource, "A1-A3 Typical")
    density = get_density(resource)

    if not conservative:
        return None

    return {
        "material_name": resource.get("Name"),
        "conservative_gwp": conservative,
        "typical_gwp": typical,
        "density_kg_m3": density,
        "unit": "kg CO2e/kg",
        "source": (
            "co2data.fi / Finnish Environment Institute Syke"
        ),
        "standard": "Finnish MoE 2021 / EN 15804",
        "version": "1.01.008"
    }


def build_finnish_carbon_db():
    data = fetch_co2data()
    if not data:
        return None

    records = []
    for resource in data:
        conservative = get_gwp_value(
            resource, "A1-A3 Conservative"
        )
        typical = get_gwp_value(resource, "A1-A3 Typical")
        density = get_density(resource)

        if conservative and conservative > 0:
            records.append({
                "material_name": resource.get("Name", ""),
                "density_kg_m3": density,
                "conservative_gwp_a1_a3": conservative,
                "typical_gwp_a1_a3": typical,
                "unit": "kg CO2e/kg",
                "source": "co2data.fi / Syke Finland",
                "standard": "Finnish MoE 2021 / EN 15804",
                "resource_id": resource.get("ResourceId")
            })

    return pd.DataFrame(records) if records else None