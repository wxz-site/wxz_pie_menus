import bpy
from bpy.types import Menu, Operator, Panel

from .pie_utils import *


class PIE_Bottom_W_alt(Operator):
    bl_idname = "pie.w_alt_key"
    bl_label = get_pyfilename()
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print("yes")
        if context.active_object:
            if context.object.mode in ["EDIT", "SCULPT", "POSE", "WEIGHT_PAINT", "VERTEX_PAINT", "TEXTURE_PAINT"]:
                bpy.ops.object.transfer_mode("INVOKE_DEFAULT")
                return {"FINISHED"}
            else:
                self.report({"INFO"}, "此模式无法传递编辑状态")
                return {"CANCELLED"}
        else:
            return {"CANCELLED"}


classes = [
    PIE_Bottom_W_alt,
]

addon_keymaps = []


def register_keymaps():
    addon = bpy.context.window_manager.keyconfigs.addon

    # km = addon.keymaps.new(name="3D View", space_type="VIEW_3D")
    # kmi = km.keymap_items.new(
    #     PIE_Bottom_W_alt.bl_idname, 'W', 'CLICK', alt=True
    # )
    # addon_keymaps.append(km)


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


def unregister():
    unregister_keymaps()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
