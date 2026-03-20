import ifcopenshell
import ifcopenshell.util.element as Element
import pandas as pd

def parse_ifc(file_path):
    model = ifcopenshell.open(file_path)

    target_types = [
        "IfcWall", "IfcSlab", "IfcColumn",
        "IfcBeam", "IfcFooting"
    ]

    records = []

    for ifc_type in target_types:
        for element in model.by_type(ifc_type):

            # Get material name
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
            except Exception:
                material_name = "Unknown"

            # Get volume
            volume = 0.0
            try:
                for rel in element.IsDefinedBy:
                    if rel.is_a("IfcRelDefinesByProperties"):
                        props = rel.RelatingPropertyDefinition
                        if props.is_a("IfcElementQuantity"):
                            for qty in props.Quantities:
                                if qty.is_a("IfcQuantityVolume"):
                                    volume = qty.VolumeValue
            except Exception:
                volume = 0.0

            # Get storey
            storey = "Unknown"
            try:
                for rel in element.ContainedInStructure:
                    container = rel.RelatingStructure
                    if container.is_a("IfcBuildingStorey"):
                        storey = container.Name
            except Exception:
                storey = "Unknown"

            records.append({
                "element_id": element.GlobalId,
                "element_type": ifc_type,
                "material": material_name,
                "volume_m3": round(volume, 4),
                "storey": storey
            })

    df = pd.DataFrame(records)
    return df


def get_summary(df):
    summary = {
        "total_elements": len(df),
        "element_types": df["element_type"].value_counts().to_dict(),
        "unique_materials": df["material"].nunique(),
        "storeys": df["storey"].unique().tolist(),
        "missing_material": int((df["material"] == "Unknown").sum()),
        "missing_volume": int((df["volume_m3"] == 0).sum()),
        "missing_storey": int((df["storey"] == "Unknown").sum()),
    }
    return summary