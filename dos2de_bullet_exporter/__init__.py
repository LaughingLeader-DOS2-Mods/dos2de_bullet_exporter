import bpy

from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from bpy.types import Operator, OperatorFileListElement, AddonPreferences

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

# Fix for reloads
if "bpy" in locals():
    from . import physics_exporter
    import imp
    if "physics_exporter" in locals():
        imp.reload(physics_exporter) # noqa

def enum_members_from_type(rna_type, prop_str):
    prop = rna_type.bl_rna.properties[prop_str]
    return [(i.identifier, i.name, i.description, i.icon, i.value) for i in prop.enum_items.values()]

physics_type_items = enum_members_from_type(bpy.types.GameObjectSettings, "physics_type")
collision_bounds_type_items = enum_members_from_type(bpy.types.GameObjectSettings, "collision_bounds_type")

from os.path import basename, dirname
dos2de_physics_preferences_id = basename(dirname(__file__))

class DivinityPhysicsExporterAddonPreferences(AddonPreferences):
    bl_idname = dos2de_physics_preferences_id

    binutil_path = StringProperty(
        name="LSPakUtilityBulletToPhysX",
        description="Path to LSPakUtilityBulletToPhysX.exe that converts bullet files to bin\nLocated within your Divinity Engine/DefEd folder by default",
        default="",
        subtype='FILE_PATH'
    )
    
    export_combine_visible = BoolProperty(
        name="Combine Visible Meshes",
        description="Combine all copies of visible meshes before exporting",
        default=True
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

        layout.label(text="Export Settings:", icon="EXPORT")
        box = layout.box()
        box.prop(self, "export_use_defaults")
        box.prop(self, "default_physics_type")
        box.prop(self, "default_collision_bounds_type")
        box.prop(self, "export_combine_visible")

def get_preferences(context):
    user_preferences = context.user_preferences
    
    if dos2de_physics_preferences_id in user_preferences.addons:
        return user_preferences.addons[dos2de_physics_preferences_id].preferences
    
    return None

addon_keymaps = []

def register():
    bpy.utils.register_module(__name__)
    
    bpy.types.INFO_MT_file_export.append(physics_exporter.menu_func)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new('Window', space_type='EMPTY', region_type='WINDOW', modal=False)
    kmi = km.keymap_items.new(physics_exporter.LEADER_OT_physics_exporter.bl_idname, 'E', 'PRESS', ctrl=True, shift=True, alt=True)
    addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(physics_exporter.menu_func)

    try:
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        if kc:
            for km, kmi in addon_keymaps:
                km.keymap_items.remove(kmi)
        addon_keymaps.clear()
    except:
        pass
if __name__ == "__main__":
    register()
