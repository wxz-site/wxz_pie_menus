import bpy
import os
from bpy.types import Menu, Panel, Operator
from .utils import check_rely_addon, rely_addons, set_pie_ridius, pie_op_check
from .utils import change_default_keymap, restored_default_keymap

submoduname = __name__.split('.')[-1]
bl_info = {
    "name": submoduname,
    "author": "wxz",
    "version": (0, 0, 1),
    "blender": (3, 3, 0),
    "location": "View3D",
    "category": "3D View",
}


class VIEW3D_PIE_MT_Bottom_S(Menu):
    bl_label = submoduname

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        set_pie_ridius(context, 100)

        ui = context.area.ui_type

        if ui == "VIEW_3D":
            ob_type = context.object.type
            ob_mode = context.object.mode


            if ob_mode == 'OBJECT':
                #4 - LEFT
                X = pie.operator(PIE_S_Flat_Object.bl_idname, text='X对齐')
                X.X = True
                X.Y = False
                X.Z = False
                # 6 - RIGHT
                pie.separator()
                # 2 - BOTTOM
                X = pie.operator(PIE_S_Flat_Object.bl_idname, text='Z对齐')
                X.X = False
                X.Y = False
                X.Z = True
                # 8 - TOP
                X = pie.operator(PIE_S_Flat_Object.bl_idname, text='Y对齐')
                X.X = False
                X.Y = True
                X.Z = False
                # 7 - TOP - LEFT
                pie.separator()
                # 9 - TOP - RIGHT
                pie.separator()
                # 1 - BOTTOM - LEFT
                pie.separator()
                # 3 - BOTTOM - RIGHT
                pie.separator()
            if ob_mode == 'EDIT':
                # 4 - LEFT
                X = pie.operator(PIE_S_Flat_Mesh.bl_idname, text='X拍平')
                X.X = True
                X.Y = False
                X.Z = False
                # 6 - RIGHT
                pie.separator()
                # 2 - BOTTOM
                X = pie.operator(PIE_S_Flat_Mesh.bl_idname, text='Z拍平')
                X.X = False
                X.Y = False
                X.Z = True
                # 8 - TOP
                X = pie.operator(PIE_S_Flat_Mesh.bl_idname, text='Y拍平')
                X.X = False
                X.Y = True
                X.Z = False
                # 7 - TOP - LEFT
                pie.separator()
                # 9 - TOP - RIGHT
                pie.separator()
                # 1 - BOTTOM - LEFT
                pie.separator()
                # 3 - BOTTOM - RIGHT
                pie.separator()
        elif ui == "UV":
            # 4 - LEFT
            pie.operator('uv.align', text='对齐到 X 轴').axis = 'ALIGN_X'
            # 6 - RIGHT
            pie.separator()
            # 2 - BOTTOM
            pie.operator('uv.align', text='对齐到 Y 轴').axis = 'ALIGN_Y'
            # 8 - TOP
            pie.separator()
            # 7 - TOP - LEFT
            pie.separator()
            # 9 - TOP - RIGHT
            pie.separator()
            # 1 - BOTTOM - LEFT
            pie.separator()
            # 3 - BOTTOM - RIGHT
            pie.separator()


class PIE_S_Flat_Mesh(Operator):
    bl_idname = "pie.view_s_flat_mesh"
    bl_label = ""
    bl_options = {"REGISTER", "UNDO"}

    X: bpy.props.BoolProperty(name='X')
    Y: bpy.props.BoolProperty(name='Y')
    Z: bpy.props.BoolProperty(name='Z')

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        X = self.X
        Y = self.Y
        Z = self.Z
        if X:
            bpy.ops.transform.resize(value=(0, 1, 1))
        elif Y:
            bpy.ops.transform.resize(value=(1, 0, 1))
        elif Z:
            bpy.ops.transform.resize(value=(1, 1, 0))
        return {"FINISHED"}


class PIE_S_Flat_Object(Operator):
    bl_idname = "pie.view_s_flat_object"
    bl_label = ""
    bl_options = {"REGISTER", "UNDO"}

    X: bpy.props.BoolProperty(name='X')
    Y: bpy.props.BoolProperty(name='Y')
    Z: bpy.props.BoolProperty(name='Z')

    @classmethod
    def poll(cls, context):
        if context.selected_objects:
            if context.object.mode == 'OBJECT':
                return True
        else:
            return False

    def execute(self, context):
        X = self.X
        Y = self.Y
        Z = self.Z
        if context.scene.tool_settings.use_transform_pivot_point_align == False:
            context.scene.tool_settings.use_transform_pivot_point_align = True
            if X:
                bpy.ops.transform.resize(value=(0, 1, 1))
            elif Y:
                bpy.ops.transform.resize(value=(1, 0, 1))
            elif Z:
                bpy.ops.transform.resize(value=(1, 1, 0))
            context.scene.tool_settings.use_transform_pivot_point_align = False
        else:
            if X:
                bpy.ops.transform.resize(value=(0, 1, 1))
            elif Y:
                bpy.ops.transform.resize(value=(1, 0, 1))
            elif Z:
                bpy.ops.transform.resize(value=(1, 1, 0))
        return {"FINISHED"}


classes = [VIEW3D_PIE_MT_Bottom_S, 
        PIE_S_Flat_Mesh,
        PIE_S_Flat_Object
        ]

addon_keymaps = []


def register_keymaps():
    addon = bpy.context.window_manager.keyconfigs.addon

    space_name = [
        ('3D View', 'VIEW_3D'),
        ('UV Editor', 'EMPTY'),
    ]
    for space in space_name:
        km = addon.keymaps.new(name=space[0], space_type=space[1])
        kmi = km.keymap_items.new("wm.call_menu_pie", 'S', 'CLICK_DRAG')
        kmi.properties.name = "VIEW3D_PIE_MT_Bottom_S"
        addon_keymaps.append(km)


def unregister_keymaps():
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)
        # wm.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymaps()

    global key1 # 3d视图s
    key1 = change_default_keymap(
        '3D View','transform.resize',
        [('value','CLICK')]
        )
    global key2 # UV视图s
    key2 = change_default_keymap(
        'UV Editor','transform.resize',
        [('value','CLICK')]
        )
    global key3 # 曲线视图s
    key3 = change_default_keymap(
        'Graph Editor','transform.resize',
        [('value','CLICK')]
        )
    global key4 # 节点视图s
    key4 = change_default_keymap(
        'Node Editor','transform.resize',
        [('value','CLICK')]
        )
    

def unregister():
    restored_default_keymap(key1)
    restored_default_keymap(key2)
    restored_default_keymap(key3)
    restored_default_keymap(key4)

    unregister_keymaps()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# if __name__ == "__main__":
#     register()
#     bpy.ops.wm.call_menu_pie(name="VIEW3D_PIE_MT_Bottom_S")
