from contextlib import contextmanager
import os.path
import subprocess

from math import radians
from mathutils import Euler, Matrix

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper

def error_missing_layer_names(self, context):
    self.layout.label("Layer Names are not enabled. Please enable the Layer Management or Leader Helpers addon for layer names.")

def error_no_active_object(self, context):
    self.layout.label("No active object set.")

class PhysicsExporter(bpy.types.Operator, ExportHelper):
    """Export physics data with Divinity-specific options (.bullet, .bin)"""
    bl_idname = "export_scene.dos2de_physics"
    bl_label = "Export Divinity Physics"
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

        print("[DOS2DE-Physics] Exporting bullet file to {}".format(export_path))

        bpy.context.scene.objects.active = obj

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
            print("[DOS2DE-Physics] Cleaning up.")
            bpy.ops.logic.controller_remove(controller=export_ctrl.name, object=obj.name)
            bpy.ops.logic.controller_remove(controller=pass_ctrl.name, object=obj.name)
            bpy.ops.logic.actuator_remove(actuator=quit_act.name, object=obj.name)
            bpy.ops.logic.sensor_remove(sensor=trigger.name, object=obj.name)
            print("[DOS2DE-Physics] Done.")

            if self.binconversion_enabled:
                if self.binutil_path is not None and self.binutil_path != "" and os.path.isfile(self.binutil_path):
                    if os.path.isfile(export_path):
                        subprocess.run([self.binutil_path,'-i', export_path])
                        os.remove(export_path)
                    else:
                        raise Warning("[DOS2DE-Physics] Bullet file not found. Try exporting to a folder not in your User directory.")
                else:
                    raise Exception("[DOS2DE-Physics] Bin conversion program not found.")
    def finish(self, context, **args):
        export_objects = args["export_objects"]
        new_armatures = args["new_armatures"]
        prev_engine = args["prev_engine"]
        object_settings = args["object_settings"]
        active_object = args["active_object"]
        last_mode = args["last_mode"]

        for obj in export_objects:
            if obj is not None:
                data = bpy.data.objects[obj.name]
                bpy.data.objects.remove(data, do_unlink=True)

        for obj in new_armatures:
            if obj is not None:
                data = bpy.data.objects[obj.name]
                bpy.data.objects.remove(data, do_unlink=True)

        export_objects.clear()
        new_armatures.clear()

        context.scene.render.engine = prev_engine

        for obj in context.scene.objects:
            obj.select = False

        for k in object_settings:
            settings = object_settings[k]
            obj = context.scene.objects[k]
            obj.select = settings["selected"]
            obj.hide_render = settings["hide_render"]
            bpy.data.objects[obj.name].game.use_collision_bounds = settings["use_collision_bounds"]
        
        if active_object is not None:
            bpy.context.scene.objects.active = active_object
        
        # Return to previous mode
        if last_mode is not None and active_object is not None:
            if active_object.type != "ARMATURE" and last_mode == "POSE":
                bpy.ops.object.mode_set(mode="OBJECT")
            else:
                bpy.ops.object.mode_set (mode=last_mode)

    def execute(self, context):
        if not self.filepath:
            raise Exception("[DOS2DE-Physics] Filepath not set.")
        prev_engine = context.scene.render.engine or 'BLENDER_RENDER'
        context.scene.render.engine = 'BLENDER_GAME'

        export_objects = []
        new_armatures = []
        armature_copies = {}
        object_settings = {}

        last_mode = getattr(bpy.context.object, "mode", None)
        
        active_object = None
        if bpy.context.scene.objects.active:
            active_object = bpy.context.scene.objects.active

        for obj in context.scene.objects:

            object_settings[obj.name] = {
                "selected": obj.select,
                "hide_render": obj.hide_render,
                "use_collision_bounds": bpy.data.objects[obj.name].game.use_collision_bounds
            }

            if obj.type == "MESH" and self.can_export_object(context, obj):
                print("[DOS2DE-Physics] Copying object '{}'.".format(obj.name))

                copy = obj.copy()
                copy.data = obj.data.copy()
                context.scene.objects.link(copy)
                export_objects.append(copy)

                copy.hide_render = False

                if obj.parent is not None:
                    if obj.parent.name in armature_copies:
                        print("[DOS2DE-Physics] Set copy '{}' parent to {}.".format(obj.name, obj.parent.name))
                        copy.parent = armature_copies[obj.parent.name]
                    elif obj.parent.type == "ARMATURE":
                        print("[DOS2DE-Physics] Copying object parent '{}' - {}.".format(obj.name, obj.parent.name))
                        parent_copy = obj.parent.copy()
                        parent_copy.data = obj.parent.data.copy()
                        context.scene.objects.link(parent_copy)
                        new_armatures.append(parent_copy)
                        copy.parent = parent_copy
                        armature_copies[obj.name] = parent_copy
                        parent_copy.hide_render = False

            obj.select = False
            obj.hide_render = True

            #Using copies, hide the originals
            if bpy.data.objects[obj.name] is not None:
                bpy.data.objects[obj.name].game.use_collision_bounds = False

        if len(export_objects) <= 0:
            print("[DOS2DE-Physics] No object to export! Cancelling.")
            self.finish(context, export_objects=export_objects, new_armatures=new_armatures, 
                    object_settings=object_settings, active_object=active_object, 
                    prev_engine=prev_engine, last_mode=last_mode)
            return {'CANCELLED'}

        bpy.context.scene.objects.active = None
        bpy.ops.object.select_all(action='DESELECT')

        from . import get_preferences

        addon_prefs = get_preferences(context)

        if addon_prefs.export_combine_visible and len(export_objects) > 1:
            print("[DOS2DE-Physics] Joining objects.")

            for obj in export_objects:
                obj.select = True

            bpy.context.scene.objects.active = export_objects[0]
            bpy.ops.object.join()

            export_objects.clear()
            export_objects.append(bpy.context.scene.objects.active)
            print("[DOS2DE-Physics] Objects joined into '{}'.".format(bpy.context.scene.objects.active.name))
            bpy.context.scene.objects.active.select = True

        if bpy.context.scene.objects.active is not None:
            bpy.ops.object.select_all(action='DESELECT')

        arm_num = 1

        for obj in export_objects:
            if self.yup_enabled:
                print("[DOS2DE-Physics] Rotating object '{}' to y-up.".format(obj.name))
                obj.rotation_euler = (obj.rotation_euler.to_matrix() * Matrix.Rotation(radians(90), 3, 'X')).to_euler()

            if obj.parent is None or obj.parent.type != "ARMATURE":
                print("[DOS2DE-Physics] Creating armature for '{}'.".format(obj.name))
                #bpy.ops.object.armature_add()
                #armature = bpy.context.scene.objects.active
                data_name = 'armbexporttempdata-{}'.format(arm_num)
                arm_name = 'armbexporttemp-{}'.format(arm_num)
                arm_num += 1

                armature_data = bpy.data.armatures.new(data_name)
                armature = bpy.data.objects.new(arm_name, armature_data)
                armature.hide_render = False
                context.scene.objects.link(armature)

                obj.parent = armature

                for i in range(20):
                    armature.layers[i] = obj.layers[i]

                mod = obj.modifiers.new("Armature", "ARMATURE")
                mod.object = armature

                new_armatures.append(armature)
                print(" [DOS2DE-Physics] Armature '{}' created.".format(armature.name))

        for obj in export_objects:
            phys_type = bpy.data.objects[obj.name].game.physics_type

            print("[DOS2DE-Physics] Phys type for '{}' is {}.".format(obj.name, phys_type))

            if addon_prefs is not None and addon_prefs.export_use_defaults:
                if phys_type is None or phys_type == "NO_COLLISION":
                    print("[DOS2DE-Physics] Using default physics settings for '{}'.".format(obj.name))
                    physics_type = addon_prefs.default_physics_type
                    bpy.data.objects[obj.name].game.physics_type = physics_type
                    bpy.data.objects[obj.name].game.collision_bounds_type = addon_prefs.default_collision_bounds_type
                    bpy.data.objects[obj.name].game.use_collision_bounds = True

            phys_enabled = bpy.data.objects[obj.name].game.use_collision_bounds

            if phys_enabled:
                print("[DOS2DE-Physics] Exporting object '{}'".format(obj.name))
                self.export_bullet(context, obj)

        self.finish(context, export_objects=export_objects, new_armatures=new_armatures, 
                object_settings=object_settings, active_object=active_object, 
                prev_engine=prev_engine, last_mode=last_mode)

        return {"FINISHED"}

def menu_func(self, context):
    self.layout.operator(PhysicsExporter.bl_idname, text="Divinity Physics (.bullet, .bin)")
