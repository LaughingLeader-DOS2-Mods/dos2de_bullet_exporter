import bpy

from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from bpy.types import Operator, OperatorFileListElement, AddonPreferences

from . import physics_exporter

bl_info = {
    "name": "Divinity Physics Exporter",
    "author": "LaughingLeader",
    "blender": (2, 7, 9),
    "api": -1,
    "location": "File > Import-Export",
    "description": ("Export physics files for Divinity: Original Sin 2 - Definitive Edition."),
    "warning": "",
    "wiki_url": (""),
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Import-Export"
}

def enum_members_from_type(rna_type, prop_str):
    prop = rna_type.bl_rna.properties[prop_str]
    return [(i.identifier, i.name, i.description, i.icon, i.value) for i in prop.enum_items.values()]

physics_type_items = enum_members_from_type(bpy.types.GameObjectSettings, "physics_type")
collision_bounds_type_items = enum_members_from_type(bpy.types.GameObjectSettings, "collision_bounds_type")

class DivinityPhysicsExporterAddonPreferences(AddonPreferences):
    bl_idname = "dos2de_physics_exporter"

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

def register():
    bpy.utils.register_module(__name__)
    physics_exporter.register()

    #wm = bpy.context.window_manager
    #m = wm.keyconfigs.addon.keymaps.new('Window', space_type='EMPTY', region_type='WINDOW', modal=False)
    #kmi = km.keymap_items.new(BulletDataExporter.bl_idname, 'E', 'PRESS', ctrl=True, shift=True, alt=True)
    #print(__name__)
    #kmi.properties.name = ExportDAE.bl_idname
    #addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_module(__name__)
    physics_exporter.unregister()

if __name__ == "__main__":
    register()
