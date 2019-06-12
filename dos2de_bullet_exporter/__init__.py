from contextlib import contextmanager
import bpy
import os.path
import subprocess

from math import radians
from mathutils import Euler, Matrix

from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from bpy.types import Operator, OperatorFileListElement, AddonPreferences

from bpy_extras.io_utils import ExportHelper

bl_info = {
    "name": "Bullet Exporter - Divinity: Original Sin 2",
    "author": "LaughingLeader",
    "blender": (2, 7, 9),
    "api": -1,
    "location": "File > Import-Export",
    "description": ("Export Bullet Files"),
    "warning": "",
    "wiki_url": (""),
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Export"
}

def enum_members_from_type(rna_type, prop_str):
    prop = rna_type.bl_rna.properties[prop_str]
    return [(i.identifier, i.name, i.description, i.icon, i.value) for i in prop.enum_items.values()]

physics_type_items = enum_members_from_type(bpy.types.GameObjectSettings, "physics_type")
collision_bounds_type_items = enum_members_from_type(bpy.types.GameObjectSettings, "collision_bounds_type")

class DivinityBulletExporterAddonPreferences(AddonPreferences):
    bl_idname = "dos2_bullet_exporter"

    binutil_path = StringProperty(
        name="LSPakUtilityBulletToPhysX",
        description="Path to the exe that converts bullet files to bin",
        default="C:\The Divinity Engine 2\DefEd\LSPakUtilityBulletToPhysX.exe",
        subtype='FILE_PATH'
    )
    
    export_use_defaults = BoolProperty(
        name="Use Defaults",
        description="Meshes with no physics set will use default settings when exporting",
        default=True
    )

    default_physics_type = EnumProperty(
        name="Default Physics Type",
        description="The type of physical representation to use for meshes",
        items=physics_type_items,
        default=("STATIC")
    )

    default_collision_bounds_type = EnumProperty(
        name="Default Bounds",
        description="The collision shape that better fits the object",
        items=collision_bounds_type_items,
        default=("CONVEX_HULL")
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="General:", icon="OUTLINER_DATA_META")
        box = layout.box()
        box.prop(self, "binutil_path")

        layout.label(text="Export Defaults:", icon="EXPORT")
        box = layout.box()
        box.prop(self, "export_autosetup")
        box.prop(self, "default_physics_type")
        box.prop(self, "default_collision_bounds_type")

def menu_func(self, context):
    self.layout.operator(BulletDataExporter.bl_idname, text="Divinity Physics (.bullet, .bin)")

def register():
    bpy.utils.register_module(__name__)
    #bpy.utils.register_class(BulletDataExporter)
    bpy.types.INFO_MT_file_export.append(menu_func)

    #wm = bpy.context.window_manager
    #m = wm.keyconfigs.addon.keymaps.new('Window', space_type='EMPTY', region_type='WINDOW', modal=False)
    #kmi = km.keymap_items.new(BulletDataExporter.bl_idname, 'E', 'PRESS', ctrl=True, shift=True, alt=True)
    #print(__name__)
    #kmi.properties.name = ExportDAE.bl_idname
    addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_module(__name__)
    #bpy.utils.unregister_class(BulletDataExporter)
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
