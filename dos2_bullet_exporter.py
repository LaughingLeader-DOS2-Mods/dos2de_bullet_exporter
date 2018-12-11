# -*- coding: utf-8 -*-

from contextlib import contextmanager
import bpy
import os.path
import subprocess

from math import radians
from mathutils import Euler, Matrix

from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty

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


def default_filename(context):
    current_path = context.blend_data.filepath
    if current_path:
        return os.path.join(
            os.path.dirname(current_path),
            '{}.bullet'.format(
                os.path.splitext(os.path.basename(current_path))[0]))
    else:
        return os.path.join(os.path.expanduser("~"), '.bullet')


class BulletDataExporter(bpy.types.Operator, ExportHelper):
    """Export physics data"""
    bl_idname = "dos2.export_bullet"
    bl_label = "Export Bullet"
    bl_options = {"PRESET", "REGISTER", "UNDO"}

    filename_ext = ".bullet"
    filter_glob = StringProperty(default="*.bullet", options={"HIDDEN"})
    
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
                for i in range(20):
                    if (bpy.data.scenes["Scene"].layers[i]):
                        self.auto_filepath = bpy.path.ensure_ext("{}\\{}".format(self.directory, 
                                                bpy.data.scenes["Scene"].namedlayers.layers[i].name), 
                                            self.filename_ext)
                        self.update_path = True
            elif self.auto_name == "OBJECT":
                self.auto_filepath = bpy.path.ensure_ext("{}\\{}".format(self.directory, bpy.context.scene.objects.active.name), self.filename_ext)
                self.update_path = True
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
    def text_snippet(self, context):
        self.snip = context.blend_data.texts.new('phys_export_snip')
        self.snip.write(
            'import PhysicsConstraints\n'
            'PhysicsConstraints.exportBulletFile("{}")'.format(self.filepath))
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
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
    def execute(self, context):
        if not self.filepath:
            raise Exception("[DOS2DE-Bullet] Filepath not set.")
        prev_engine = context.scene.render.engine or 'BLENDER_RENDER'
        context.scene.render.engine = 'BLENDER_GAME'
        if not context.selected_objects:
            raise Exception("[DOS2DE-Bullet] No selected objects! Cancelling.")
            return {'CANCELLED'}

        last_mode = bpy.context.object.mode
        obj = context.selected_objects[0]
        
        bpy.ops.object.mode_set(mode='OBJECT')
        #print("[DOS2DE-Bullet] Selected objects: " + obj.name)
        
        if self.yup_enabled:
            euler = Euler(map(radians, (-90, 180, 0)), 'XYZ')
            obj.rotation_euler = euler
            
        with self.text_snippet(context):
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

        context.scene.render.engine = prev_engine
        
        if self.yup_enabled:
            euler = Euler(map(radians, (0, 0, 0)), 'XYZ')
            obj.rotation_euler = euler
        
        if last_mode is not None and last_mode != "" and last_mode != bpy.context.object.mode:
            bpy.ops.object.mode_set(last_mode)
        
        if self.binconversion_enabled:
            if self.binutil_path is not None and self.binutil_path != "" and os.path.isfile(self.binutil_path):
                subprocess.run([self.binutil_path,'-i',self.filepath])
                #subprocess.call([self.binutil_path,'-i',self.filepath])
                #command = "\"{}\" -i \"{}\"".format(self.binutil_path, self.filepath)
                #os.system("start /wait cmd /c {} pause".format(self.command))
                os.remove(self.filepath)
            else:
                raise Exception("[DOS2DE-Bullet] Bin conversion program not found.")
        return {"FINISHED"}


def menu_func(self, context):
    self.layout.operator(BulletDataExporter.bl_idname, text="Divinity Physics (.bullet, .bin)")


def register():
    bpy.utils.register_module(__name__)
    #bpy.utils.register_class(BulletDataExporter)
    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)
    #bpy.utils.unregister_class(BulletDataExporter)
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
