# -*- coding: utf-8 -*-

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
    "category": "Import-Export"
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

def default_filename(context):
    current_path = context.blend_data.filepath
    if current_path:
        return os.path.join(
            os.path.dirname(current_path),
            '{}.bullet'.format(
                os.path.splitext(os.path.basename(current_path))[0]))
    else:
        return os.path.join(os.path.expanduser("~"), '.bullet')

def error_missing_layer_names(self, context):
    self.layout.label("Layer Names are not enabled. Please enable the Layer Management or Leader Helpers addon for layer names.")

def error_no_active_object(self, context):
    self.layout.label("No active object set.")

class BulletDataExporter(bpy.types.Operator, ExportHelper):
    """Export physics data with Divinity-specific options (.bullet, .bin)"""
    bl_idname = "dos2.op_export_bullet"
    bl_label = "Export Bullet"
    bl_options = {"PRESET", "REGISTER", "UNDO"}

    filename_ext = ".bullet"
    filter_glob = StringProperty(default="*.bullet;*.bin", options={"HIDDEN"})
    
    filename = StringProperty(
        name="File Name",
        options={"HIDDEN"}
    )    
    directory = StringProperty(
        name="Directory",
        options={"HIDDEN"}
    )
    
    def update_filepath(self, context):
        if self.filepath != "" and self.last_filepath == "":
            self.last_filepath = self.filepath
        
        if self.filepath != "":
            if self.auto_name == "LAYER":
                if hasattr(bpy.data.scenes["Scene"], "namedlayers"):
                    for i in range(20):
                        if (bpy.data.scenes["Scene"].layers[i]):
                                layername = bpy.data.scenes["Scene"].namedlayers.layers[i].name
                                if layername is not None and layername != "":
                                    self.auto_filepath = bpy.path.ensure_ext("{}\\{}".format(self.directory, layername), self.filename_ext)
                                    self.update_path = True
                                    break
                else:
                    bpy.context.window_manager.popup_menu(error_missing_layer_names, title="Warning", icon='ERROR')
            elif self.auto_name == "OBJECT":
                if getattr(bpy.context.scene.objects, "active", None) is not None and hasattr(bpy.context.scene.objects.active, "name"):
                    self.auto_filepath = bpy.path.ensure_ext("{}\\{}".format(self.directory, bpy.context.scene.objects.active.name), self.filename_ext)
                    self.update_path = True
                else:
                    bpy.context.window_manager.popup_menu(error_no_active_object, title="Warning", icon='ERROR')
            elif self.auto_name == "DISABLED" and self.last_filepath != "":
                self.auto_filepath = bpy.path.ensure_ext(self.last_filepath, self.filename_ext)
                self.update_path = True
        return

#   ==== Default Properties Start ====
    yup_enabled = BoolProperty(
        name="Y-Up Rotation",
        description="Rotates the object for a Y-up world",
        default=True
        )

    auto_name = EnumProperty(
        name="Name",
        description="Auto-generate a filename based on a property name",
        items=(("DISABLED", "Disabled", ""),
               ("LAYER", "Layer Name", ""),
               ("OBJECT", "Active Object Name", "")),
        default=("LAYER"),
        update=update_filepath
        )
        
    binconversion_enabled = BoolProperty(
        name="Convert to Bin",
        description="Converts the resulting .bullet file to .bin",
        default=True
        )  
        
    binutil_path = StringProperty(
        name="LSPakUtilityBulletToPhysX",
        description="Path to the exe that converts bullet files to bin",
        default="C:\The Divinity Engine 2\DefEd\LSPakUtilityBulletToPhysX.exe",
        subtype='FILE_PATH'
        )
#   ==== Default Properties End ====        
    use_active_layers = BoolProperty(
        name="Active Layers Only",
        description="Export only objects on the active layers.",
        default=True
        )
    use_export_selected = BoolProperty(
        name="Selected Only",
        description="Export only selected objects (and visible in active "
                    "layers if that applies).",
        default=False
        )

    use_export_visible = BoolProperty(
        name="Visible Only",
        description="Export only visible, unhidden, selectable objects",
        default=True
        )

    update_path = BoolProperty(
        default=False,
        options={"HIDDEN"},
        )
        
    setpath_initial = BoolProperty(
        default=True,
        options={"HIDDEN"},
        )

    auto_filepath = StringProperty(
        name="Auto Filepath",
        default="",
        options={"HIDDEN"},
        )     
        
    last_filepath = StringProperty(
        name="Last Filepath",
        default="",
        options={"HIDDEN"},
        )

    @contextmanager
    def text_snippet(self, context, export_filepath):
        self.snip = context.blend_data.texts.new('phys_export_snip')
        self.snip.write(
            'import PhysicsConstraints\n'
            'PhysicsConstraints.exportBulletFile("{}")'.format(export_filepath))
        yield
        context.blend_data.texts.remove(self.snip)
        self.snip = None
        
    @property
    def check_extension(self):
        return True

    def check(self, context):
        update = False
        
        if self.setpath_initial:
            self.update_filepath(context)
            setpath_initial = False
        
        if self.update_path and self.auto_filepath != "":
            update = True
            self.filepath = self.auto_filepath  
            self.update_path = False
        return update

    def invoke(self, context, event):
        if self.filepath != "" and self.last_filepath == "":
            self.last_filepath = self.filepath
        if self.auto_name == "LAYER" and hasattr(bpy.data.scenes["Scene"], "namedlayers") == False:
            #bpy.context.window_manager.popup_menu(error_missing_layer_names, title="Warning", icon='ERROR')
            self.auto_name = "DISABLED"
        if self.binconversion_enabled:
            if self.binutil_path is None or self.binutil_path == "" or os.path.isfile(self.binutil_path) == False:
                self.binconversion_enabled = False
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def create_filepath(self, context, obj):
        obj_filepath = ""

        if self.auto_name == "LAYER":
            if hasattr(bpy.data.scenes["Scene"], "namedlayers"):
                for i in range(20):
                    if (obj.layers[i]):
                            layername = bpy.data.scenes["Scene"].namedlayers.layers[i].name
                            if layername is not None and layername != "":
                                obj_filepath = bpy.path.ensure_ext("{}\\{}".format(self.directory, layername), self.filename_ext)
                                break

        if obj_filepath == "" or self.auto_name == "OBJECT":
            obj_filepath = bpy.path.ensure_ext("{}\\{}".format(self.directory, obj.name), self.filename_ext)
        elif obj_filepath == "":
            obj_filepath = bpy.path.ensure_ext(self.last_filepath, self.filename_ext)

        return obj_filepath

    def can_export_object(self, context, obj):
        if self.use_export_visible and obj.hide or obj.hide_select:
            return False
        if self.use_export_selected and obj.select == False:
            return False
        if self.use_active_layers:
            for i in range(20):
                if context.scene.layers[i] and not obj.layers[i]:
                    return False
        return True

    def export_bullet(self, context, obj):

        export_path = self.create_filepath(context, obj)

        print("[DOS2DE-Bullet] Exporting bullet file to {}".format(export_path))

        with self.text_snippet(context, export_path):
            # create a trigger
            bpy.ops.logic.sensor_add(type='ALWAYS', name='phys_export_trigger', object=obj.name)
            trigger = obj.game.sensors[-1]

            # create export controller
            bpy.ops.logic.controller_add(type='PYTHON', name='phys_export', object=obj.name)
            export_ctrl = obj.game.controllers[-1]
            export_ctrl.text = self.snip
            #print(self.snip.as_string())
            trigger.link(export_ctrl)

            # create AND controller
            bpy.ops.logic.controller_add(type='LOGIC_AND', name='phys_export_pass', object=obj.name)
            pass_ctrl = obj.game.controllers[-1]
            trigger.link(pass_ctrl)

            # create QUIT actuator
            bpy.ops.logic.actuator_add(type='GAME', name='phys_export_quit', object=obj.name)
            quit_act = obj.game.actuators[-1]
            quit_act.mode = 'QUIT'
            pass_ctrl.link(actuator=quit_act)

            # run game engine!
            bpy.ops.view3d.game_start()

            # cleanup
            print("[DOS2DE-Bullet] Cleaning up.")
            bpy.ops.logic.controller_remove(controller=export_ctrl.name, object=obj.name)
            bpy.ops.logic.controller_remove(controller=pass_ctrl.name, object=obj.name)
            bpy.ops.logic.actuator_remove(actuator=quit_act.name, object=obj.name)
            bpy.ops.logic.sensor_remove(sensor=trigger.name, object=obj.name)
            print("[DOS2DE-Bullet] Done.")

            if self.binconversion_enabled:
                if self.binutil_path is not None and self.binutil_path != "" and os.path.isfile(self.binutil_path):
                    if os.path.isfile(export_path):
                        subprocess.run([self.binutil_path,'-i', export_path])
                        os.remove(export_path)
                    else:
                        raise Warning("[DOS2DE-Bullet] Bullet file not found. Try exporting to a folder not in your User directory.")
                else:
                    raise Exception("[DOS2DE-Bullet] Bin conversion program not found.")

    def execute(self, context):
        if not self.filepath:
            raise Exception("[DOS2DE-Bullet] Filepath not set.")
        prev_engine = context.scene.render.engine or 'BLENDER_RENDER'
        context.scene.render.engine = 'BLENDER_GAME'

        export_objects = []
        new_armatures = []

        selected_objects = []

        last_mode = getattr(bpy.context.object, "mode", None)
        
        active_object = None
        if bpy.context.scene.objects.active:
            active_object = bpy.context.scene.objects.active

        for obj in context.scene.objects:
            if obj.select:
                selected_objects.append(obj)
                obj.select = False

            if obj.type == "MESH" and self.can_export_object(context, obj):
                copy = obj.copy()
                copy.data = obj.data.copy()
                context.scene.objects.link(copy)
                export_objects.append(copy)
        
        if len(export_objects) <= 0:
            raise Exception("[DOS2DE-Bullet] No object to export! Cancelling.")
            return {'CANCELLED'}

        bpy.context.scene.objects.active = None

        bpy.ops.object.select_all(action='DESELECT')
        #bpy.ops.object.mode_set(mode='OBJECT')

        for obj in export_objects:
            if self.yup_enabled:
                euler = Euler(map(radians, (-90, 180, 0)), 'XYZ')
                copy.rotation_euler = euler

            if copy.parent is None or copy.parent.type != "ARMATURE":
                bpy.context.scene.objects.active = None

                bpy.ops.object.armature_add()
                armature = bpy.context.scene.objects.active
                copy.parent = armature

                for i in range(20):
                    armature.layers[i] = obj.layers[i]
                
                bpy.context.scene.objects.active = copy

                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.modifier_add(type="ARMATURE")

                armature_modifiers = (mod for mod in copy.modifiers if mod.type == "ARMATURE")
                for mod in armature_modifiers:
                    mod.object = copy.parent

                new_armatures.append(armature)

        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons["dos2_bullet_exporter"].preferences

        for obj in export_objects:
            phys_type = bpy.data.objects[obj.name].game.physics_type
            if addon_prefs.export_use_defaults:
                
                if phys_type is None or phys_type == "NO_COLLISION":
                    physics_type = addon_prefs.default_physics_type
                    bpy.data.objects[obj.name].game.physics_type = physics_type
                    bpy.data.objects[obj.name].game.collision_bounds_type = addon_prefs.default_collision_bounds_type
                    bpy.data.objects[obj.name].game.use_collision_bounds = True

            if phys_type is not None and phys_type != "NO_COLLISION":
                #self.export_bullet(context, obj)
                continue

        bpy.ops.object.select_all(action='DESELECT')

        for obj in export_objects:
            if obj is not None:
                obj.select = True

        for obj in new_armatures:
            if obj is not None:
                obj.select = True

        bpy.ops.object.delete(use_global=True)

        for block in bpy.data.meshes:
            if block.users == 0:
                bpy.data.meshes.remove(block)

        for block in bpy.data.armatures:
            if block.users == 0:
                bpy.data.armatures.remove(block)

        bpy.ops.object.select_all(action='DESELECT')

        context.scene.render.engine = prev_engine

        for obj in selected_objects:
            obj.select = True
        
        if active_object is not None:
            bpy.context.scene.objects.active = active_object
        
        # Return to previous mode
        if last_mode is not None and active_object is not None:
            if active_object.type != "ARMATURE" and current_mode == "POSE":
                bpy.ops.object.mode_set(mode="OBJECT")
            else:
                bpy.ops.object.mode_set (mode=last_mode)

        return {"FINISHED"}


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
