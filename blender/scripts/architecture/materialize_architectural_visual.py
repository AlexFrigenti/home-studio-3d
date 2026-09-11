"""Blender-only materialization adapters for the T7.02/T7.03 visual plans.

The source authority and the Slice 006 derived scene are never edited by this
module.  It owns only the ``HSARCH_VISUAL_*`` collection subtree supplied by
the pure geometry planner.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping
from typing import Any

try:  # Blender is available only inside the GUI runtime.
    import bpy as _bpy  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised outside Blender.
    _bpy = None

import architectural_visual_geometry as geometry_plan
import architectural_visual_materials as materials_plan


ROOT_COLLECTION_NAME = "HSARCH_VISUAL_living-room-main_slice-007_v1"
ARCHITECTURAL_COLLECTION_NAME = "ArchitecturalVisual"
OPENING_COLLECTION_NAME = "OpeningVisual"
FIXED_COLLECTION_NAME = "FixedElementVisual"
OBJECT_PREFIX = "HSARCH_VISUAL_"
OWNER = "ArchitecturalVisual"
NAMESPACE = "HSARCH_VISUAL"
SOURCE_SCENE_SUFFIX = "/blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend"
SLICE_006_SCENE_SUFFIX = "/blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend"
SLICE_007_SCENE_SUFFIX = "/blender/scenes/review/2026-09-10-living-room-main-slice-007-architectural-visual-v1.blend"


class ArchitecturalVisualMaterializationError(RuntimeError):
    """Raised when the Blender scene cannot be changed within Slice 007 scope."""


def validate_scene_output_path(filepath: str) -> None:
    """Reject source/Slice 006 paths and require the T7.02 derived output."""

    normalized = str(filepath).replace("\\", "/").lower()
    if normalized.endswith(SOURCE_SCENE_SUFFIX.lower()):
        raise ArchitecturalVisualMaterializationError("refusing to materialize into the architectural source scene")
    if normalized.endswith(SLICE_006_SCENE_SUFFIX.lower()):
        raise ArchitecturalVisualMaterializationError("refusing to materialize into the Slice 006 derived scene")
    if not normalized.endswith(SLICE_007_SCENE_SUFFIX.lower()):
        raise ArchitecturalVisualMaterializationError("T7.02 output filepath must be the Slice 007 derived scene")


def _runtime_bpy(bpy_module: Any | None) -> Any:
    runtime = bpy_module or _bpy
    if runtime is None:
        raise ArchitecturalVisualMaterializationError("T7.02 materialization requires Blender bpy")
    return runtime


def _iter_collection_tree(collection: Any) -> Iterable[Any]:
    yield collection
    for child in collection.children:
        yield from _iter_collection_tree(child)


def _iter_collection_objects(collection: Any) -> Iterable[Any]:
    for child in _iter_collection_tree(collection):
        yield from child.objects


def _collection_is_direct_scene_child(scene: Any, collection: Any) -> bool:
    return any(child == collection for child in scene.collection.children)


def _expected_names(plan: Mapping[str, Any]) -> set[str]:
    names = {plan["root_name"]}
    for opening in plan["openings"]:
        names.add(opening["root"]["name"])
        names.update(component["name"] for component in opening["components"])
    return names


def _assert_no_external_collisions(runtime: Any, scene: Any, plan: Mapping[str, Any], existing_root: Any | None) -> None:
    managed_objects = set(_iter_collection_objects(existing_root)) if existing_root is not None else set()
    for name in _expected_names(plan):
        object_data = runtime.data.objects.get(name)
        if object_data is not None and object_data not in managed_objects:
            raise ArchitecturalVisualMaterializationError(f"object name collision outside managed root: {name}")
    for name in (
        ROOT_COLLECTION_NAME,
        ARCHITECTURAL_COLLECTION_NAME,
        OPENING_COLLECTION_NAME,
        FIXED_COLLECTION_NAME,
    ):
        collection = runtime.data.collections.get(name)
        if collection is not None and collection != existing_root:
            if existing_root is None or collection not in set(_iter_collection_tree(existing_root)):
                raise ArchitecturalVisualMaterializationError(
                    f"collection name collision outside managed root: {name}"
                )
    if existing_root is not None:
        for object_data in managed_objects:
            if not object_data.name.startswith(OBJECT_PREFIX):
                raise ArchitecturalVisualMaterializationError(
                    f"managed root contains an unowned object: {object_data.name}"
                )


def _remove_owned_tree(runtime: Any, root_collection: Any) -> None:
    descendants = list(_iter_collection_tree(root_collection))
    objects = list(_iter_collection_objects(root_collection))
    for object_data in objects:
        if not object_data.name.startswith(OBJECT_PREFIX):
            raise ArchitecturalVisualMaterializationError(
                f"refusing to remove object outside HSARCH_VISUAL_*: {object_data.name}"
            )
    for object_data in objects:
        mesh = object_data.data if object_data.type == "MESH" else None
        runtime.data.objects.remove(object_data, do_unlink=True)
        if mesh is not None and mesh.users == 0:
            runtime.data.meshes.remove(mesh)
    # Repeated materialization can leave zero-user mesh datablocks behind when
    # Blender has already detached an object. They are still owned by this
    # namespace, so remove only those orphaned HSARCH datablocks before the
    # next deterministic creation pass. Unrelated mesh namespaces are intact.
    for mesh in list(runtime.data.meshes):
        if mesh.name.startswith(OBJECT_PREFIX) and mesh.users == 0:
            runtime.data.meshes.remove(mesh)
    for collection in reversed(descendants):
        runtime.data.collections.remove(collection, do_unlink=True)


def _set_metadata(data_block: Any, metadata: Mapping[str, Any], *, generator_version: str) -> None:
    data_block["hs3d_visual_owner"] = OWNER
    data_block["hs3d_visual_namespace"] = NAMESPACE
    data_block["hs3d_room_id"] = "living-room-main"
    data_block["hs3d_opening_id"] = metadata["source_opening_id"]
    data_block["hs3d_opening_kind"] = metadata["opening_type"]
    data_block["hs3d_wall_id"] = metadata["source_wall_id"]
    data_block["hs3d_component_type"] = metadata["component_type"]
    data_block["hs3d_support_level"] = metadata["support_level"]
    data_block["hs3d_provenance"] = metadata["provenance"]
    data_block["hs3d_derived_visual"] = bool(metadata["derived_visual"])
    data_block["hs3d_constructive_geometry"] = bool(metadata["constructive_geometry"])
    data_block["hs3d_presentation_only"] = bool(metadata.get("presentation_only", False))
    data_block["hs3d_opening_direction"] = metadata["opening_direction"]
    data_block["hs3d_source_ids"] = json.dumps(
        metadata["source_ids"],
        sort_keys=True,
        separators=(",", ":"),
    )
    data_block["hs3d_source_field_status"] = json.dumps(
        metadata["source_field_status"],
        sort_keys=True,
        separators=(",", ":"),
    )
    data_block["hs3d_effective_field_status"] = json.dumps(
        metadata["effective_field_status"],
        sort_keys=True,
        separators=(",", ":"),
    )
    if "pose" in metadata:
        data_block["hs3d_visual_pose"] = metadata["pose"]
    if "approximation" in metadata:
        data_block["hs3d_visual_approximation"] = metadata["approximation"]
    if "representation" in metadata:
        data_block["hs3d_visual_representation"] = metadata["representation"]
    if "orientation_source" in metadata:
        data_block["hs3d_orientation_source"] = metadata["orientation_source"]
    data_block["hs3d_generator_version"] = generator_version


def _set_collection_metadata(collection: Any, role: str, generator_version: str) -> None:
    collection["hs3d_visual_owner"] = OWNER
    collection["hs3d_visual_namespace"] = NAMESPACE
    collection["hs3d_visual_collection_role"] = role
    collection["hs3d_provenance"] = "procedural_synthetic"
    collection["hs3d_generator_version"] = generator_version


def _box_geometry(parts: list[Mapping[str, Any]]) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for part in parts:
        center = [float(value) for value in part["center_m"]]
        dimensions = [float(value) for value in part["dimensions_m"]]
        if len(center) != 3 or len(dimensions) != 3 or any(value <= 0.0 for value in dimensions):
            raise ArchitecturalVisualMaterializationError("invalid box part in geometry plan")
        hx, hy, hz = (value / 2.0 for value in dimensions)
        base = len(vertices)
        vertices.extend(
            [
                (center[0] - hx, center[1] - hy, center[2] - hz),
                (center[0] + hx, center[1] - hy, center[2] - hz),
                (center[0] + hx, center[1] + hy, center[2] - hz),
                (center[0] - hx, center[1] + hy, center[2] - hz),
                (center[0] - hx, center[1] - hy, center[2] + hz),
                (center[0] + hx, center[1] - hy, center[2] + hz),
                (center[0] + hx, center[1] + hy, center[2] + hz),
                (center[0] - hx, center[1] + hy, center[2] + hz),
            ]
        )
        faces.extend(
            [
                (base + 0, base + 1, base + 2, base + 3),
                (base + 4, base + 7, base + 6, base + 5),
                (base + 0, base + 4, base + 5, base + 1),
                (base + 1, base + 5, base + 6, base + 2),
                (base + 2, base + 6, base + 7, base + 3),
                (base + 4, base + 0, base + 3, base + 7),
            ]
        )
    return vertices, faces


def _create_component(runtime: Any, collection: Any, root: Any, component: Mapping[str, Any], generator_version: str) -> Any:
    mesh = runtime.data.meshes.new(f"{component['name']}_MESH")
    vertices, faces = _box_geometry(component["geometry"]["parts"])
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    object_data = runtime.data.objects.new(component["name"], mesh)
    collection.objects.link(object_data)
    object_data.parent = root
    object_data.location = (0.0, 0.0, 0.0)
    object_data.rotation_euler = (0.0, 0.0, 0.0)
    _set_metadata(object_data, component["metadata"], generator_version=generator_version)
    _set_metadata(mesh, component["metadata"], generator_version=generator_version)
    return object_data


def _create_root(runtime: Any, collection: Any, root_spec: Mapping[str, Any], generator_version: str) -> Any:
    object_data = runtime.data.objects.new(root_spec["name"], None)
    collection.objects.link(object_data)
    object_data.empty_display_type = "PLAIN_AXES"
    object_data.empty_display_size = 0.12
    object_data.location = tuple(root_spec["location_m"])
    object_data.rotation_euler = tuple(root_spec["rotation_euler_rad"])
    _set_metadata(object_data, root_spec["metadata"], generator_version=generator_version)
    return object_data


def _new_collection(runtime: Any, name: str, parent: Any, role: str, generator_version: str) -> Any:
    collection = runtime.data.collections.new(name)
    parent.children.link(collection)
    _set_collection_metadata(collection, role, generator_version)
    return collection


def materialize_architectural_visual(
    scene: Any,
    geometry: Mapping[str, Any],
    *,
    bpy_module: Any | None = None,
) -> dict[str, Any]:
    """Materialize only the T7.02 visual subtree in the supplied scene."""

    runtime = _runtime_bpy(bpy_module)
    geometry_plan.validate_opening_geometry_plan(geometry)
    if scene is None or getattr(scene, "collection", None) is None:
        raise ArchitecturalVisualMaterializationError("scene must expose a master collection")
    validate_scene_output_path(runtime.data.filepath)
    existing_root = runtime.data.collections.get(ROOT_COLLECTION_NAME)
    if existing_root is not None and not _collection_is_direct_scene_child(scene, existing_root):
        raise ArchitecturalVisualMaterializationError("managed visual root is outside the active scene")
    _assert_no_external_collisions(runtime, scene, geometry, existing_root)
    if existing_root is not None:
        _remove_owned_tree(runtime, existing_root)

    root_collection = _new_collection(
        runtime,
        ROOT_COLLECTION_NAME,
        scene.collection,
        "ArchitecturalVisualRoot",
        geometry["generator_version"],
    )
    architectural_collection = _new_collection(
        runtime,
        ARCHITECTURAL_COLLECTION_NAME,
        root_collection,
        ARCHITECTURAL_COLLECTION_NAME,
        geometry["generator_version"],
    )
    opening_collection = _new_collection(
        runtime,
        OPENING_COLLECTION_NAME,
        architectural_collection,
        OPENING_COLLECTION_NAME,
        geometry["generator_version"],
    )
    fixed_collection = _new_collection(
        runtime,
        FIXED_COLLECTION_NAME,
        architectural_collection,
        FIXED_COLLECTION_NAME,
        geometry["generator_version"],
    )
    if geometry["fixed_elements"] or list(fixed_collection.objects):
        raise ArchitecturalVisualMaterializationError("FixedElementVisual must remain empty")

    root_collection["hs3d_visual_root"] = True
    root_collection["hs3d_visual_owner"] = OWNER
    root_collection["hs3d_visual_namespace"] = NAMESPACE
    root_collection["hs3d_visual_contract_version"] = geometry["geometry_contract_version"]
    root_collection["hs3d_visual_write_scope"] = "HSARCH_VISUAL_*"
    root_collection["hs3d_source_contract_version"] = geometry["source_contract"]["contract_version"]
    root_collection["hs3d_room_logical_signature"] = geometry["source_contract"]["binding"]["room_logical_signature"]

    created_objects = []
    for opening in geometry["openings"]:
        root_object = _create_root(
            runtime,
            opening_collection,
            opening["root"],
            geometry["generator_version"],
        )
        created_objects.append(root_object)
        for component in opening["components"]:
            created_objects.append(
                _create_component(
                    runtime,
                    opening_collection,
                    root_object,
                    component,
                    geometry["generator_version"],
                )
            )
    return scene_inventory(scene, root_name=ROOT_COLLECTION_NAME, bpy_module=runtime)


def scene_inventory(scene: Any, *, root_name: str = ROOT_COLLECTION_NAME, bpy_module: Any | None = None) -> dict[str, Any]:
    """Return a normalized read-only inventory of the T7.02 managed subtree."""

    runtime = _runtime_bpy(bpy_module)
    root_collection = runtime.data.collections.get(root_name)
    if root_collection is None:
        raise ArchitecturalVisualMaterializationError(f"managed visual root not found: {root_name}")
    descendants = list(_iter_collection_tree(root_collection))
    objects = list(_iter_collection_objects(root_collection))
    opening_objects = [obj for obj in objects if obj.users_collection and any(collection.name == OPENING_COLLECTION_NAME for collection in obj.users_collection)]
    fixed_collection = runtime.data.collections.get(FIXED_COLLECTION_NAME)
    fixed_objects = list(fixed_collection.objects) if fixed_collection is not None else []
    components = [obj for obj in opening_objects if obj.type == "MESH"]
    roots = [obj for obj in opening_objects if obj.type == "EMPTY"]
    component_types = [obj.get("hs3d_component_type") for obj in components]
    return {
        "collections_total": len(runtime.data.collections),
        "objects_total": len(runtime.data.objects),
        "architectural_visual_collections": len(descendants),
        "architectural_visual_objects": len(objects),
        "opening_visual_objects": len(opening_objects),
        "fixed_element_visual_objects": len(fixed_objects),
        "roots_empty": len(roots),
        "meshes": len(components),
        "frames": component_types.count("FRAME"),
        "glass_panels": component_types.count("GLASS"),
        "neutral_door_infills": component_types.count("DOOR_INFILL"),
        "sill_bands": component_types.count("SILL"),
        "collections": [collection.name for collection in descendants],
        "object_names": sorted(obj.name for obj in objects),
        "root_names": sorted(obj.name for obj in roots),
        "component_names": sorted(obj.name for obj in components),
    }


def validate_scene_inventory(inventory: Mapping[str, Any]) -> None:
    expected = {
        "architectural_visual_collections": 4,
        "architectural_visual_objects": 22,
        "opening_visual_objects": 22,
        "fixed_element_visual_objects": 0,
        "roots_empty": 6,
        "meshes": 16,
        "frames": 6,
        "glass_panels": 4,
        "neutral_door_infills": 2,
        "sill_bands": 4,
    }
    for field, value in expected.items():
        if inventory.get(field) != value:
            raise ArchitecturalVisualMaterializationError(
                f"inventory mismatch for {field}: expected {value}, got {inventory.get(field)}"
            )
    if inventory.get("fixed_element_visual_objects") != 0:
        raise ArchitecturalVisualMaterializationError("FixedElementVisual inventory is not empty")


def _material_metadata(material: Any, descriptor: Mapping[str, Any]) -> None:
    material["hs3d_visual_owner"] = OWNER
    material["hs3d_material_owner"] = "Slice007ArchitecturalVisual"
    material["hs3d_visual_namespace"] = NAMESPACE
    material["hs3d_material_id"] = descriptor["material_id"]
    material["hs3d_semantic_role"] = descriptor["semantic_role"]
    material["hs3d_provenance"] = descriptor["provenance"]
    material["hs3d_derived_visual"] = bool(descriptor["derived_visual"])
    material["hs3d_constructive_geometry"] = bool(descriptor["constructive_geometry"])
    material["hs3d_presentation_only"] = bool(descriptor["presentation_only"])
    material["hs3d_material_contract_version"] = materials_plan.MATERIAL_CONTRACT_VERSION
    material["hs3d_material_generator_version"] = materials_plan.MATERIAL_GENERATOR_VERSION
    material["hs3d_external_images"] = bool(descriptor["external_images"])
    material["hs3d_external_textures"] = bool(descriptor["external_textures"])
    material["hs3d_external_asset_paths"] = json.dumps(
        descriptor["external_asset_paths"],
        sort_keys=True,
        separators=(",", ":"),
    )
    material["hs3d_node_policy"] = json.dumps(
        descriptor["node_policy"],
        sort_keys=True,
        separators=(",", ":"),
    )


def _node_input(node: Any, name: str) -> Any | None:
    inputs = getattr(node, "inputs", None)
    if inputs is None:
        return None
    getter = getattr(inputs, "get", None)
    if getter is not None:
        return getter(name)
    for socket in inputs:
        if socket.name == name:
            return socket
    return None


def _apply_material_nodes(material: Any, descriptor: Mapping[str, Any]) -> None:
    material.use_nodes = True
    node_tree = material.node_tree
    nodes = node_tree.nodes
    nodes.clear()
    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.name = "Material Output"
    shader = nodes.new(type="ShaderNodeBsdfPrincipled")
    shader.name = "Principled BSDF"
    node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    for input_name, value in (
        ("Base Color", tuple(descriptor["base_color"])),
        ("Roughness", float(descriptor["roughness"])),
        ("Metallic", float(descriptor["metallic"])),
        ("Alpha", float(descriptor["alpha"])),
        ("Transmission Weight", float(descriptor["transmission_weight"])),
    ):
        socket = _node_input(shader, input_name)
        if socket is not None:
            socket.default_value = value
    diffuse = list(descriptor["base_color"])
    diffuse[3] = float(descriptor["alpha"])
    material.diffuse_color = tuple(diffuse)
    if hasattr(material, "surface_render_method"):
        try:
            material.surface_render_method = "DITHERED"
        except (AttributeError, TypeError, ValueError):
            pass
    _material_metadata(material, descriptor)


def _get_owned_material(runtime: Any, descriptor: Mapping[str, Any]) -> Any:
    name = descriptor["material_id"]
    material = runtime.data.materials.get(name)
    if material is not None:
        if material.get("hs3d_visual_namespace") != NAMESPACE or material.get("hs3d_material_owner") != "Slice007ArchitecturalVisual":
            raise ArchitecturalVisualMaterializationError(
                f"material name collision outside Slice 007 ownership: {name}"
            )
        return material
    return runtime.data.materials.new(name)


def materialize_architectural_visual_materials(
    scene: Any,
    material_plan: Mapping[str, Any],
    *,
    bpy_module: Any | None = None,
) -> dict[str, Any]:
    """Materialize only T7.03 material data and assignments in HSARCH_VISUAL."""

    runtime = _runtime_bpy(bpy_module)
    materials_plan.validate_architectural_visual_material_plan(material_plan)
    if scene is None or getattr(scene, "collection", None) is None:
        raise ArchitecturalVisualMaterializationError("scene must expose a master collection")
    validate_scene_output_path(runtime.data.filepath)
    root_collection = runtime.data.collections.get(ROOT_COLLECTION_NAME)
    opening_collection = runtime.data.collections.get(OPENING_COLLECTION_NAME)
    fixed_collection = runtime.data.collections.get(FIXED_COLLECTION_NAME)
    if root_collection is None or not _collection_is_direct_scene_child(scene, root_collection):
        raise ArchitecturalVisualMaterializationError("Slice 007 visual root is not in the active scene")
    if opening_collection is None or opening_collection not in set(_iter_collection_tree(root_collection)):
        raise ArchitecturalVisualMaterializationError("OpeningVisual is outside the managed root")
    if fixed_collection is None or list(fixed_collection.objects):
        raise ArchitecturalVisualMaterializationError("FixedElementVisual must remain empty")

    material_by_id = {}
    for descriptor in material_plan["materials"]:
        material = _get_owned_material(runtime, descriptor)
        _apply_material_nodes(material, descriptor)
        material_by_id[descriptor["material_id"]] = material

    assignments = material_plan["assignments"]
    managed_objects = {}
    for object_data in _iter_collection_objects(root_collection):
        managed_objects[object_data.name] = object_data
    for assignment in assignments:
        object_name = assignment["object_name"]
        object_data = managed_objects.get(object_name)
        if object_data is None or object_data.type != "MESH":
            raise ArchitecturalVisualMaterializationError(
                f"material assignment target is not a managed mesh: {object_name}"
            )
        if object_data.get("hs3d_visual_namespace") != NAMESPACE:
            raise ArchitecturalVisualMaterializationError(
                f"material assignment target is outside HSARCH_VISUAL: {object_name}"
            )
        object_data.data.materials.clear()
        object_data.data.materials.append(material_by_id[assignment["material_id"]])
        object_data["hs3d_visual_material_id"] = assignment["material_id"]
        object_data.data["hs3d_visual_material_id"] = assignment["material_id"]

    assigned_names = {assignment["object_name"] for assignment in assignments}
    managed_meshes = {
        object_data.name
        for object_data in managed_objects.values()
        if object_data.type == "MESH"
    }
    if managed_meshes != assigned_names:
        raise ArchitecturalVisualMaterializationError(
            "every and only every HSARCH_VISUAL mesh must receive one material"
        )
    return scene_material_inventory(scene, material_plan=material_plan, bpy_module=runtime)


def scene_material_inventory(
    scene: Any,
    *,
    material_plan: Mapping[str, Any],
    bpy_module: Any | None = None,
) -> dict[str, Any]:
    """Return normalized T7.03 material names, nodes and assignments."""

    runtime = _runtime_bpy(bpy_module)
    root_collection = runtime.data.collections.get(ROOT_COLLECTION_NAME)
    if root_collection is None:
        raise ArchitecturalVisualMaterializationError("managed visual root not found")
    names = []
    material_nodes = {}
    for descriptor in material_plan["materials"]:
        material = runtime.data.materials.get(descriptor["material_id"])
        if material is None:
            raise ArchitecturalVisualMaterializationError(
                f"expected material is missing: {descriptor['material_id']}"
            )
        names.append(material.name)
        material_nodes[material.name] = sorted(node.name for node in material.node_tree.nodes)
    assignments = {}
    for object_data in _iter_collection_objects(root_collection):
        if object_data.type != "MESH":
            continue
        assignments[object_data.name] = [slot.name for slot in object_data.data.materials]
    return {
        "materials": names,
        "material_nodes": material_nodes,
        "assignments": assignments,
        "fixed_element_visual_objects": len(list(runtime.data.collections[FIXED_COLLECTION_NAME].objects)),
    }


def validate_scene_material_inventory(
    inventory: Mapping[str, Any],
    material_plan: Mapping[str, Any],
) -> None:
    """Validate exact T7.03 material count and one-slot role assignments."""

    expected_names = [item["material_id"] for item in material_plan["materials"]]
    if inventory.get("materials") != expected_names:
        raise ArchitecturalVisualMaterializationError("T7.03 material inventory mismatch")
    if inventory.get("fixed_element_visual_objects") != 0:
        raise ArchitecturalVisualMaterializationError("FixedElementVisual is not empty")
    expected_assignments = {
        item["object_name"]: [item["material_id"]]
        for item in material_plan["assignments"]
    }
    if inventory.get("assignments") != expected_assignments:
        raise ArchitecturalVisualMaterializationError("T7.03 material assignments mismatch")
    for node_names in inventory.get("material_nodes", {}).values():
        if node_names != ["Material Output", "Principled BSDF"]:
            raise ArchitecturalVisualMaterializationError("T7.03 material nodes are not minimal")
