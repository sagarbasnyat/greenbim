import ifcopenshell
import ifcopenshell.util.element as Element
import pandas as pd


def get_material_name(element):
    material_name = "Unknown"
    try:
        material = Element.get_material(element)
        if material:
            if hasattr(material, "Name") and material.Name:
                material_name = material.Name
            elif hasattr(material, "MaterialLayers"):
                layers = material.MaterialLayers
                if layers and layers[0].Material:
                    material_name = layers[0].Material.Name
            elif hasattr(material, "Materials"):
                mats = material.Materials
                if mats:
                    material_name = mats[0].Name
            elif hasattr(material, "MaterialConstituents"):
                constituents = material.MaterialConstituents
                if constituents and constituents[0].Material:
                    material_name = (
                        constituents[0].Material.Name
                    )
    except Exception:
        pass
    return material_name if material_name else "Unknown"


def get_volume(element):
    volume = 0.0

    # Method 1 — IfcElementQuantity (Archicad standard)
    try:
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                props = rel.RelatingPropertyDefinition
                if props.is_a("IfcElementQuantity"):
                    for qty in props.Quantities:
                        if qty.is_a("IfcQuantityVolume"):
                            val = qty.VolumeValue
                            if val and val > volume:
                                volume = val
    except Exception:
        pass

    if volume > 0:
        return volume

    # Method 2 — IfcPropertySet volume properties (Revit)
    try:
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                props = rel.RelatingPropertyDefinition
                if props.is_a("IfcPropertySet"):
                    for prop in props.HasProperties:
                        if prop.is_a("IfcPropertySingleValue"):
                            name = prop.Name.lower()
                            if any(
                                v in name for v in [
                                    "volume", "tilavuus",
                                    "volumen", "vol",
                                    "netvolume", "grossvolume"
                                ]
                            ):
                                if prop.NominalValue:
                                    try:
                                        val = float(
                                            prop.NominalValue
                                            .wrappedValue
                                        )
                                        if val > volume:
                                            volume = val
                                    except Exception:
                                        pass
    except Exception:
        pass

    if volume > 0:
        return volume

    # Method 3 — BaseQuantities (Tekla Structures)
    try:
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                props = rel.RelatingPropertyDefinition
                if props.is_a("IfcElementQuantity"):
                    if hasattr(props, "Name") and props.Name:
                        if "base" in props.Name.lower():
                            for qty in props.Quantities:
                                if qty.is_a(
                                    "IfcQuantityVolume"
                                ):
                                    val = qty.VolumeValue
                                    if val and val > volume:
                                        volume = val
    except Exception:
        pass

    if volume > 0:
        return volume

    # Method 4 — Estimate from dimensions if available
    try:
        length = 0.0
        width = 0.0
        height = 0.0
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                props = rel.RelatingPropertyDefinition
                if props.is_a("IfcElementQuantity"):
                    for qty in props.Quantities:
                        name = qty.Name.lower()
                        if qty.is_a("IfcQuantityLength"):
                            if "length" in name:
                                length = qty.LengthValue
                            elif "width" in name:
                                width = qty.LengthValue
                            elif "height" in name or "depth" in name:
                                height = qty.LengthValue
                        elif qty.is_a("IfcQuantityArea"):
                            if "net" in name or "cross" in name:
                                if height > 0:
                                    volume = (
                                        qty.AreaValue * height
                                    )
        if volume == 0 and length > 0 and width > 0 and height > 0:
            volume = length * width * height
    except Exception:
        pass

    return round(volume, 4)


def get_storey(element):
    storey = "Unknown"
    try:
        for rel in element.ContainedInStructure:
            container = rel.RelatingStructure
            if container.is_a("IfcBuildingStorey"):
                storey = container.Name
                break
    except Exception:
        pass

    if storey == "Unknown":
        try:
            if hasattr(element, "Decomposes"):
                for rel in element.Decomposes:
                    if hasattr(rel, "RelatingObject"):
                        obj = rel.RelatingObject
                        if obj.is_a("IfcBuildingStorey"):
                            storey = obj.Name
                            break
                        elif obj.is_a("IfcBuildingElement"):
                            for rel2 in (
                                obj.ContainedInStructure
                            ):
                                container = (
                                    rel2.RelatingStructure
                                )
                                if container.is_a(
                                    "IfcBuildingStorey"
                                ):
                                    storey = container.Name
                                    break
        except Exception:
            pass

    return storey if storey else "Unknown"


def parse_ifc(file_path):
    model = ifcopenshell.open(file_path)

    target_types = [
        "IfcWall",
        "IfcWallStandardCase",
        "IfcSlab",
        "IfcColumn",
        "IfcBeam",
        "IfcFooting",
        "IfcPile",
        "IfcStair",
        "IfcRoof",
        "IfcPlate",
        "IfcMember"
    ]

    records = []

    for ifc_type in target_types:
        for element in model.by_type(ifc_type):
            material_name = get_material_name(element)
            volume = get_volume(element)
            storey = get_storey(element)

            records.append({
                "element_id": element.GlobalId,
                "element_type": ifc_type.replace(
                    "StandardCase", ""
                ),
                "material": material_name,
                "volume_m3": round(volume, 4),
                "storey": storey
            })

    df = pd.DataFrame(records)
    return df


def get_summary(df):
    summary = {
        "total_elements": len(df),
        "element_types": (
            df["element_type"].value_counts().to_dict()
        ),
        "unique_materials": df["material"].nunique(),
        "storeys": df["storey"].unique().tolist(),
        "missing_material": int(
            (df["material"] == "Unknown").sum()
        ),
        "missing_volume": int((df["volume_m3"] == 0).sum()),
        "missing_storey": int(
            (df["storey"] == "Unknown").sum()
        ),
    }
    return summary