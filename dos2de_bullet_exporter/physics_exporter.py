from contextlib import contextmanager
import os.path
import subprocess

from math import radians
from mathutils import Euler, Matrix

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
import bmesh

def error_missing_layer_names(self, context):
    self.layout.label("Layer Names are not enabled. Please enable the Layer Management or Leader Helpers addon for layer names.")

def error_no_active_object(self, context):
    self.layout.label("No active object set.")

def enum_members_from_type(rna_type, prop_str):
    prop = rna_type.bl_rna.properties[prop_str]
    return [(i.identifier, i.name, i.description, i.icon, i.value) for i in prop.enum_items.values()]

physics_type_items = enum_members_from_type(bpy.types.GameObjectSettings, "physics_type")
collision_bounds_type_items = enum_members_from_type(bpy.types.GameObjectSettings, "collision_bounds_type")

class LEADER_OT_physics_exporter(bpy.types.Operator, ExportHelper):
    """Export physics data with Divinity-specific options (.bullet, .bin)"""
    bl_idname = "export_scene.dos2de_physics"
    bl_label = "Export Divinity Physics"
    bl_options = {"PRESET", "REGISTER", "UNDO"}

    filename_ext = StringProperty(
        name="File Extension",
        options={"HIDDEN"},
        default=".bullet"
    )

    filter_glob = StringProperty(default="*.bullet;*.bin", options={"HIDDEN"})
    
    filename = StringProperty(
        name="File Name",
        options={"HIDDEN"}
    )

    directory = StringProperty(
        name="Directory",
        options={"HIDDEN"}
    )

    export_directory = StringProperty(
        name="Project Export Directory",
        default="",
        options={"HIDDEN"}
    )

    auto_determine_path = BoolProperty(
        default=False,
        name="Use Project Pathways",
        description="Automatically determine the export path via Divinity Exporter project settings"
    )
    
    divinity_exporter_active = BoolProperty(
        default=False,
        options={'HIDDEN'}
    )

    def update_filepath(self, context):
        if self.filepath != "" and self.last_filepath == "":
            self.last_filepath = self.filepath

        if self.directory == "":
            self.directory = os.path.dirname(bpy.data.filepath)

        if self.filepath == "":
            self.filepath = bpy.path.ensure_ext("{}\\{}".format(self.directory, str.replace(bpy.path.basename(bpy.data.filepath), ".blend", "")), self.filename_ext)
            print("[DOS2DE-Physics] Set initial path to '{}'.".format(self.filepath))

        user_preferences = context.user_preferences
        if "io_scene_dos2de" in user_preferences.addons:
            addon_prefs = user_preferences.addons["io_scene_dos2de"].preferences
            
            if addon_prefs is not None:
                self.divinity_exporter_active = True
                if self.auto_determine_path == True and addon_prefs.auto_export_subfolder == True and self.export_directory != "":
                    auto_directory = "{}\\{}".format(self.export_directory, "Physics")
                    if os.path.exists(auto_directory):
                        self.directory = auto_directory
                        self.update_path = True

        if self.filepath != "":
            if self.auto_name == "LAYER":
                if hasattr(context.scene, "namedlayers"):
                    for i in range(20):
                        if (context.scene.layers[i]):
                                layername = context.scene.namedlayers.layers[i].name
                                if layername is not None and layername != "":
                                    self.auto_filepath = bpy.path.ensure_ext("{}\\{}".format(self.directory, layername), self.filename_ext)
                                    self.update_path = True
                                    break
                else:
                    bpy.context.window_manager.popup_menu(error_missing_layer_names, title="Warning", icon='ERROR')
            elif self.auto_name == "OBJECT":
                if getattr(context.scene.objects, "active", None) is not None and hasattr(context.scene.objects.active, "name"):
                    self.auto_filepath = bpy.path.ensure_ext("{}\\{}".format(self.directory, context.scene.objects.active.name), self.filename_ext)
                    self.update_path = True
                else:
                    bpy.context.window_manager.popup_menu(error_no_active_object, title="Warning", icon='ERROR')
            elif self.auto_name == "DISABLED" and self.last_filepath != "":
                self.auto_filepath = bpy.path.ensure_ext(self.last_filepath, self.filename_ext)
                self.update_path = True
        return

    use_rotation_apply_each = BoolProperty(
        name="Apply Each Rotation",
        description="Each rotation will be applied before the next",
        default=False
    )

    use_rotation_axis_x = BoolProperty(
        name="X",
        description="Rotate the object on the x axis. Default direction to convert to a y-up world",
        default=True
    )

    use_rotation_x_amount = FloatProperty(
        name="Rotation Amount",
        description="Rotate the object by this amount in degrees",
        default=-90
    )

    use_rotation_axis_y = BoolProperty(
        name="Y",
        description="Rotate the object on the y axis",
        default=False
    )

    use_rotation_y_amount = FloatProperty(
        name="Rotation Amount",
        description="Rotate the object by this amount in degrees",
        default=0
    )

    use_rotation_axis_z = BoolProperty(
        name="Z",
        description="Rotate the object on the z axis",
        default=False
    )

    use_rotation_z_amount = FloatProperty(
        name="Rotation Amount",
        description="Rotate the object by this amount in degrees",
        default=0
    )

    def update_preset(self, context):
        if self.preset == "WEAPON_RIGID":
            self.xflip = False
            self.use_rotation_x_amount = 90
            self.use_rotation_axis_x = True
            self.use_rotation_axis_y = False
            self.use_rotation_axis_z = False
        elif self.preset == "WEAPON_RIGGED":
            self.xflip = False
            self.use_rotation_x_amount = 90
            self.use_rotation_z_amount = 180
            self.use_rotation_axis_x = True
            self.use_rotation_axis_y = False
            self.use_rotation_axis_z = True
        elif self.preset == "DEFAULT":
            self.xflip = True
            self.use_rotation_x_amount = -90
            self.use_rotation_axis_x = True
            self.use_rotation_axis_y = False
            self.use_rotation_axis_z = False

    preset = EnumProperty(
        name="Preset",
        description="Pre-configured settings for various weapon types",
        items=(
            ("NONE", "None", ""),
            ("DEFAULT", "Default", ""),
            ("WEAPON_RIGID", "Weapon (Rigid)", ""),
            ("WEAPON_RIGGED", "Weapon (Rigged)", "")
        ),
        default=("NONE"),
        update=update_preset
    )

    xflip = BoolProperty(
        name="X-Flip",
        description="X-flip the mesh before exporting",
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
        default="",
        options={'HIDDEN'}
    )

    object_types = EnumProperty(
        name="Export Objects",
        options={"ENUM_FLAG"},
        items=(
               ("LAYERS", "Active Layers", "Export only objects on the active layers"),
               ("VISIBLE", "Visible", "Export only visible objects"),
               ("SELECTED", "Selected", "Export only selected objects (and visible in active layers if that applies)")
        ),
        default={"LAYERS", "VISIBLE"}
    )

    export_combine_visible = BoolProperty(
        name="Combine Visible Meshes",
        description="Combine all copies of visible meshes before exporting",
        default=False
    )

    physics_type = EnumProperty(
        name="Physics Type",
        description="The type of physical representation to use for meshes",
        items=physics_type_items,
        default=("STATIC")
    )

    collision_bounds_type = EnumProperty(
        name="Physics Bounds",
        description="The collision shape that better fits the object",
        items=collision_bounds_type_items,
        default=("CONVEX_HULL")
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

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "preset")
        layout.prop(self, "object_types")
        layout.label(text="Physics:", icon="PHYSICS")
        box = layout.box()
        box.prop(self, "physics_type", text="Type")
        box.prop(self, "collision_bounds_type", text="Bounds")
        box.prop(self, "xflip")
        layout.label(text="Rotation:", icon="ROTATE")
        box = layout.box()
        box.prop(self, "use_rotation_apply_each")
        row = box.column()
        col = row.column()
        col.prop(self, "use_rotation_axis_x")
        if self.use_rotation_axis_x:
            col.prop(self, "use_rotation_x_amount")
        row = box.column()
        col = row.column()
        col.prop(self, "use_rotation_axis_y")
        if self.use_rotation_axis_y:
            col.prop(self, "use_rotation_y_amount")
        row = box.column()
        col = row.column()
        col.prop(self, "use_rotation_axis_z")
        if self.use_rotation_axis_z:
            col.prop(self, "use_rotation_z_amount")

        layout.label(text="Path:", icon="EXPORT")
        box = layout.box()
        if self.divinity_exporter_active:
            box.prop(self, "auto_determine_path")
        box.prop(self, "auto_name")

        layout.label(text="Extra:", icon="LOGIC")
        box = layout.box()
        box.prop(self, "binconversion_enabled")
        box.prop(self, "export_combine_visible")

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
            self.setpath_initial = False
        
        if self.update_path and self.auto_filepath != "":
            update = True
            self.filepath = self.auto_filepath  
            self.update_path = False
        return update

    def invoke(self, context, event):
        if self.auto_name == "LAYER" and hasattr(context.scene, "namedlayers") == False:
            #bpy.context.window_manager.popup_menu(error_missing_layer_names, title="Warning", icon='ERROR')
            self.auto_name = "DISABLED"

        if self.setpath_initial:
            self.update_filepath(context)
            self.setpath_initial = False

        user_preferences = context.user_preferences

        if "io_scene_dos2de" in user_preferences.addons:
            addon_prefs = user_preferences.addons["io_scene_dos2de"].preferences
            if addon_prefs is not None:
                self.auto_determine_path = getattr(addon_prefs, "auto_export_subfolder", None) is True
                if self.auto_determine_path:
                    projects = addon_prefs.projects.project_data
                    if projects:
                        for project in projects:
                            project_folder = project.project_folder
                            export_folder = project.export_folder

                            print("[DOS2DE-Physics] Checking path '{}' for project folder '{}'.".format(self.filepath, project_folder))

                            if(export_folder != "" and project_folder != "" and 
                                bpy.path.is_subdir(self.filepath, project_folder)):
                                    self.export_directory = export_folder
                                    self.directory = export_folder
                                    self.filepath = export_folder
                                    self.last_filepath = self.filepath
                                    print("[DOS2DE-Physics] Setting start path to project export folder: \"{}\"".format(export_folder))
                                    break

        from . import get_preferences
        addon_prefs = get_preferences(context)
        if addon_prefs is not None:
            self.binconversion_enabled = os.path.isfile(addon_prefs.binutil_path)
            self.binutil_path = addon_prefs.binutil_path
            self.export_combine_visible = addon_prefs.export_combine_visible
            self.physics_type = addon_prefs.default_physics_type
            self.collision_bounds_type = addon_prefs.default_collision_bounds_type
        
        self.update_filepath(context)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def create_filepath(self, context, obj):
        obj_filepath = ""

        if self.auto_name == "LAYER":
            if hasattr(context.scene, "namedlayers"):
                for i in range(20):
                    if (obj.layers[i]):
                            layername = context.scene.namedlayers.layers[i].name
                            if layername is not None and layername != "":
                                obj_filepath = bpy.path.ensure_ext(os.path.join(self.directory, layername), self.filename_ext)
                                break

        if obj_filepath == "" or self.auto_name == "OBJECT":
            obj_filepath = bpy.path.ensure_ext(os.path.join(self.directory, obj.name), self.filename_ext)
        elif obj_filepath == "":
            obj_filepath = bpy.path.ensure_ext(self.last_filepath, self.filename_ext)

        return obj_filepath

    def can_export_object(self, context, obj):
        if "VISIBLE" in self.object_types and obj.hide or obj.hide_select:
            return False
        if "SELECTED" in self.object_types and obj.select == False:
            return False
        if "LAYERS" in self.object_types:
            for i in range(20):
                if context.scene.layers[i] and not obj.layers[i]:
                    return False
        return True

    def export_bullet(self, context, obj):

        export_path = self.create_filepath(context, obj)

        print("[DOS2DE-Physics] Exporting bullet file to {}".format(export_path))

        context.scene.objects.active = obj

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
                        raise Warning("[DOS2DE-Physics] Bullet file not found. Was it exported? If exporting to a User folder, this may cause it to fail.")
                else:
                    raise Exception("[DOS2DE-Physics] Bin conversion program not found.")
    def finish(self, context, **args):
        delete_objects = args["delete_objects"]
        prev_engine = args["prev_engine"]
        object_settings = args["object_settings"]
        active_object = args["active_object"]
        last_mode = args["last_mode"]

        last_material_settings = args["last_material_settings"]

        if last_material_settings is not None:
            for mat_tuple in last_material_settings:
                mat = mat_tuple[0]
                mat.game_settings.alpha_blend = mat_tuple[1]

        for obj in delete_objects:
            if obj is not None:
                print("[DOS2DE-Physics] Deleting {}".format(obj.name))
                data = bpy.data.objects[obj.name]
                bpy.data.objects.remove(data, do_unlink=True)

        delete_objects.clear()

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
            context.scene.objects.active = active_object
        
        # Return to previous mode
        if (last_mode is not None and active_object is not None 
                and active_object.hide == False and active_object.hide_select == False):
            if active_object.type != "ARMATURE" and last_mode == "POSE":
                bpy.ops.object.mode_set(mode="OBJECT")
            else:
                bpy.ops.object.mode_set (mode=last_mode)

    def transform_apply(self, context, obj, location=False, rotation=False, scale=False):
        if obj.parent is not None:
            self.transform_apply(context, obj.parent, location, rotation, scale)
        obj.select = True
        last_selected = getattr(context.scene.objects, "active", None)
        context.scene.objects.active = obj
        bpy.ops.object.mode_set(mode="OBJECT")
        print("   [DOS2DE-Physics] Applying transformations for {}".format(obj.name))
        bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)
        obj.select = False

        #for childobj in obj.children:
        #    self.transform_apply(context, childobj)
        context.scene.objects.active = last_selected

    def get_top_parent(self, obj):
        if obj.parent is not None:
            return self.get_top_parent(obj.parent)
        else:
            return obj

    def execute(self, context):
        if not self.filepath:
            raise Exception("[DOS2DE-Physics] Filepath not set.")
            return {'CANCELLED'}

        prev_engine = context.scene.render.engine or 'BLENDER_RENDER'
        context.scene.render.engine = 'BLENDER_GAME'

        export_objects = []
        delete_objects = []
        object_settings = {}

        last_mode = getattr(bpy.context.object, "mode", None)
        
        active_object = None
        if context.scene.objects.active:
            active_object = context.scene.objects.active

        exportable_objects = [x for x in context.scene.objects if (x.type == "ARMATURE" or x.type == "MESH") and self.can_export_object(context, x)]
        if len(exportable_objects) <= 0:
            raise Warning("[DOS2DE-Physics] No objects to export.")
            return {'CANCELLED'}
        
        for obj in exportable_objects:
            object_settings[obj.name] = {
                "selected": obj.select,
                "hide_render": obj.hide_render,
                "use_collision_bounds": bpy.data.objects[obj.name].game.use_collision_bounds
            }

            obj.select = True
            obj.hide_render = True

            #Using copies, hide the originals
            if bpy.data.objects[obj.name] is not None:
                bpy.data.objects[obj.name].game.use_collision_bounds = False

        context.scene.objects.active = exportable_objects[0]
        bpy.ops.object.mode_set(mode="OBJECT")
        print("[DOS2DE-Physics] Duplicating objects.")
        bpy.ops.object.duplicate()
        
        if context.selected_objects is not None:
            export_objects.extend(context.selected_objects)
            print("[DOS2DE-Physics] Added context.selected_objects to export_objects ({}).".format(len(export_objects)))
        elif (context.scene.objects.active != None):
            print("[DOS2DE-Physics] Added context.scene.objects.active to export_objects.")
            export_objects.append(context.scene.objects.active)

        context.scene.objects.active = None
        bpy.ops.object.select_all(action='DESELECT')

        if len(export_objects) <= 0:
            print("[DOS2DE-Physics] No object to export! Cancelling.")
            self.finish(context, export_objects=export_objects, delete_objects=delete_objects, 
                    object_settings=object_settings, active_object=active_object, 
                    prev_engine=prev_engine, last_mode=last_mode, last_material_settings=None)
            return {'CANCELLED'}

        from . import get_preferences
        addon_prefs = get_preferences(context)

        print("[DOS2DE-Physics] Applying transformations for objects.")
        for obj in export_objects:
            # if not self.can_export_object(context, obj):
            #     bpy.data.objects.remove(obj.data, do_unlink=True)
            #     export_objects.remove(obj)
            obj.hide_render = False
            self.transform_apply(context, obj, location=True, rotation=True, scale=True)

        bpy.ops.object.select_all(action='DESELECT')

        delete_objects.extend(export_objects)

        if self.export_combine_visible and len(export_objects) > 1:
            print("[DOS2DE-Physics] Joining objects.")

            mesh_copies = [x for x in export_objects if x.type == "MESH"]
            for obj in mesh_copies:
                obj.select = True
                delete_objects.remove(obj)

            context.scene.objects.active = mesh_copies[0]
            bpy.ops.object.join()

            export_objects.clear()
            export_objects.append(context.scene.objects.active)
            delete_objects.append(context.scene.objects.active)
            print("[DOS2DE-Physics] Objects joined into '{}'.".format(context.scene.objects.active.name))

        if context.scene.objects.active is not None:
            bpy.ops.object.select_all(action='DESELECT')
        
        arm_num = 1

        last_material_settings = []
        last_cursor_loc = bpy.context.scene.cursor_location.copy()
        for obj in export_objects:
            #target = self.get_top_parent(obj)
            target = obj
            if self.use_rotation_axis_y == True:
                target.rotation_euler = (target.rotation_euler.to_matrix() * Matrix.Rotation(radians(self.use_rotation_y_amount), 3, "Y")).to_euler()
                rotated = True
                if self.use_rotation_apply_each:
                    self.transform_apply(context, target, rotation=True, location=True)
            if self.use_rotation_axis_z == True:
                target.rotation_euler = (target.rotation_euler.to_matrix() * Matrix.Rotation(radians(self.use_rotation_z_amount), 3, "Z")).to_euler()
                rotated = True
                if self.use_rotation_apply_each:
                    self.transform_apply(context, target, rotation=True, location=True)
            if self.use_rotation_axis_x == True:
                target.rotation_euler = (target.rotation_euler.to_matrix() * Matrix.Rotation(radians(self.use_rotation_x_amount), 3, "X")).to_euler()
                rotated = True
                if self.use_rotation_apply_each:
                    self.transform_apply(context, target, rotation=True, location=True)

            self.transform_apply(context, target, rotation=True, location=True)
            #return {"FINISHED"}
            if self.xflip == True and obj.type == "MESH":
                print("[DOS2DE-Physics] X-flipping mesh.")
                context.scene.objects.active = obj
                obj.select = True
                # bpy.context.scene.cursor_location = obj.location
                # bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
                # if obj.scale[0] > 0:
                #     obj.scale[0] = -1
                # else:
                #     obj.scale[0] *= -1
                # bpy.ops.object.editmode_toggle()
                # bpy.ops.mesh.select_all(action='SELECT')
                # bpy.ops.mesh.flip_normals()
                # bpy.ops.object.editmode_toggle()
                # bpy.context.scene.cursor_location = last_cursor_loc
                self.transform_apply(context, obj, scale=True)
                obj.scale = (-1.0, 1.0, 1.0)
                self.transform_apply(context, obj, scale=True)
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                bmesh.ops.reverse_faces(bm, faces=bm.faces)
                bm.to_mesh(obj.data)
                bm.clear()
                obj.data.update()
                print("[DOS2DE-Physics] Flipped and applied scale transformation for {} ".format(obj.name))
                #rint("[DOS2DE-Physics] Last cursor loc: {} | Current cursor loc {}:".format(last_cursor_loc, bpy.context.scene.cursor_location))
                #bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                #print("[DOS2DE-Physics] Rotating object '{}' on the {} axis.".format(obj.name, self.use_rotation_axis))
            #return {"FINISHED"} #Debugging flips
            if (obj.parent is None or obj.parent.type != "ARMATURE") and obj.type != "ARMATURE":
                print("[DOS2DE-Physics] Creating armature for '{}'.".format(obj.name))
                #bpy.ops.object.armature_add()
                #armature = context.scene.objects.active
                data_name = 'armbexporttempdata-{}'.format(arm_num)
                arm_name = 'armbexporttemp-{}'.format(arm_num)
                arm_num += 1

                armature_data = bpy.data.armatures.new(data_name)
                armature = bpy.data.objects.new(arm_name, armature_data)
                armature.hide_render = False
                context.scene.objects.link(armature)

                obj.select = True

                if len(obj.data.materials) > 0:
                    mat = obj.data.materials[0]
                    if(mat.game_settings.alpha_blend is not "OPAQUE"):
                        last_material_settings.append((mat, mat.game_settings.alpha_blend))
                        print(" [DOS2DE-Physics] Set non-opaque material '{}[{}]' to OPAQUE.".format(mat.name, mat.game_settings.alpha_blend))
                        mat.game_settings.alpha_blend = "OPAQUE"

                context.scene.objects.active = armature
                bpy.ops.object.parent_set(type="ARMATURE")

                for i in range(20):
                    armature.layers[i] = obj.layers[i]

                delete_objects.append(armature)
                print(" [DOS2DE-Physics] Armature '{}' created.".format(armature.name))
        
        for obj in [x for x in export_objects if x.type == "MESH"]:
            phys_type = bpy.data.objects[obj.name].game.physics_type
            phys_enabled = bpy.data.objects[obj.name].game.use_collision_bounds

            print("[DOS2DE-Physics] Phys type for '{}' is {}.".format(obj.name, phys_type))

            if addon_prefs is not None and addon_prefs.export_use_defaults:
                if phys_enabled is False or phys_type is None or phys_type == "NO_COLLISION":
                    print("[DOS2DE-Physics] Using default physics settings for '{}'.".format(obj.name))
                    bpy.data.objects[obj.name].game.physics_type = self.physics_type
                    bpy.data.objects[obj.name].game.collision_bounds_type = self.collision_bounds_type
                    bpy.data.objects[obj.name].game.use_collision_bounds = True
                    phys_enabled = True

            if phys_enabled:
                print("[DOS2DE-Physics] Exporting object '{}'".format(obj.name))
                self.export_bullet(context, obj)

        self.finish(context, export_objects=export_objects, delete_objects=delete_objects, 
                object_settings=object_settings, active_object=active_object, 
                prev_engine=prev_engine, last_mode=last_mode, last_material_settings=last_material_settings)

        return {"FINISHED"}

def menu_func(self, context):
    self.layout.operator(LEADER_OT_physics_exporter.bl_idname, text="Divinity Physics (.bullet, .bin)")
