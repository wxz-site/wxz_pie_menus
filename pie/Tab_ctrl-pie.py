import bpy
import os
from pathlib import *
from bpy.types import Menu, Operator, AddonPreferences
from .utils import set_pie_ridius, change_default_keymap, restored_default_keymap


submoduname = __name__.split(".")[-1]
bl_info = {
    "name": submoduname,
    "author": "wxz",
    "version": (0, 0, 1),
    "blender": (3, 3, 0),
    "location": "View3D",
    "category": "PIE",
}


class VIEW3D_PIE_MT_Ctrl_Tab(Menu):
    bl_label = "Tab-ctrl"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # ob_type = context.object.type
        # ob_mode = context.object.mode

        set_pie_ridius(context, 100)

        print(context.area.type, context.area.ui_type)

        # 4 - LEFT
        L = pie.operator("pie.workspaceswapper", text="UV", icon="UV_DATA")
        L.target_workspace = "4-UV"
        L.default_workspace = "UV Editing"
        # 6 - RIGHT
        R = pie.operator("pie.workspaceswapper", text="MOD", icon="CUBE")
        R.target_workspace = "1-MOD"
        R.default_workspace = "Modeling"
        # 2 - BOTTOM
        B = pie.operator("pie.workspaceswapper", text="MAT", icon="MATERIAL")
        B.target_workspace = "3-MAT"
        B.default_workspace = "Shading"
        # 8 - TOP
        box = pie.column(align=True)
        row = box.row()
        row.scale_y = 1.3
        T1 = row.operator("pie.workspaceswapper", text="SETTING", icon="SETTINGS")
        T1.target_workspace = "8-SETTING"
        T1.default_workspace = "Scripting"

        row = box.row(align=True)
        row.scale_y = 1.1
        split = row.split()
        T2_1 = split.operator("pie.workspaceswapper", text="LIB", icon="BOOKMARKS")
        T2_1.target_workspace = "0-LIB"
        T2_1.default_workspace = "Layout"
        split = row.split()
        T2_2 = split.operator(
            "pie.workspaceswapper", text="COMPO", icon="NODE_COMPOSITING"
        )
        T2_2.target_workspace = "7-COMPO"
        T2_2.default_workspace = "Compositing"

        row = box.row(align=True)
        row.scale_y = 1.1
        split = row.split()
        T3_1 = split.operator(
            "pie.workspaceswapper", text="MOTION", icon="MOD_INSTANCE"
        )
        T3_1.target_workspace = "5-MOTION"
        T3_1.default_workspace = "Animation"
        split = row.split()
        T3_2 = split.operator(
            "pie.workspaceswapper", text="RENDER", icon="RENDER_STILL"
        )
        T3_2.target_workspace = "6-RENDER"
        T3_2.default_workspace = "Rendering"
        # 7 - TOP - LEFT
        pie.separator()
        # 9 - TOP - RIGHT
        pie.separator()
        # 1 - BOTTOM - LEFT
        pie.separator()
        # 3 - BOTTOM - RIGHT
        BR = pie.operator("pie.workspaceswapper", text="GN", icon="CUBE")
        BR.target_workspace = "2-GN"
        BR.default_workspace = "Geometry Nodes"


class PIE_WorkspaceSwapOperator(Operator):
    """Swap workspaces with this operator"""

    bl_idname = "pie.workspaceswapper"
    bl_label = "Swap Workspace"
    bl_options = {"REGISTER", "UNDO"}

    target_workspace: bpy.props.StringProperty(name="Target Workspace")
    default_workspace: bpy.props.StringProperty(
        name="Default Workspcae", default="Layout"
    )

    def execute(self, context):
        t_name = self.target_workspace
        d_name = self.default_workspace
        d_spaces = bpy.data.workspaces

        path = str(Path(__file__).parent.parent / "workspace.blend")
        workspaces_dir = {
            "0-LIB": "Layout",
            "1-MOD": "Modeling",
            "2-GN": "Geometry Nodes",
            "3-MAT": "Shading",
            "4-UV": "UV Editing",
            "5-MOTION": "Animation",
            "6-RENDER": "Rendering",
            "7-COMPO": "Compositing",
            "8-SETTING": "Scripting",
        }

        if context.workspace.name == t_name:
            self.report({"INFO"}, "已经为该工作空间！")
            return {"CANCELLED"}

        if t_name in d_spaces:
            context.window.workspace = d_spaces[t_name]
            self.report({"INFO"}, '已切换工作空间:"%s"' % (t_name))
            return {"FINISHED"}

        if t_name not in d_spaces:
            # 删除原始工作空间
            # w = bpy.data.workspaces[workspaces_dir[t_name]]
            # bpy.ops.workspace.delete({"workspace": w})
            # 添加指定工作空间
            bpy.ops.workspace.append_activate(idname=t_name, filepath=path)
            # 重排序工作空间
            # 获取工作空间列表(固定)
            # wk_list = [workspace.name for workspace in bpy.data.workspaces]
            # for name in wk_list:
            #     bpy.context.window.workspace = bpy.data.workspaces[name]
            #     w = bpy.data.workspaces[name]
            #     # 重排序到最前
            #     bpy.ops.workspace.reorder_to_front({"workspace": w})
            # # 提示
            context.window.workspace = d_spaces[t_name]
            self.report({"INFO"}, '已添加工作空间:"%s"' % (t_name))

            return {"FINISHED"}


class PIE_Workspace_Import_Online_Operator(Operator):
    """Import All Onlline_workspaces Into Scenes"""

    bl_idname = "pie.workspace_online_batch_import"
    bl_label = "Import Workspaces"
    bl_options = {"REGISTER", "UNDO"}

    target_workspace: bpy.props.StringProperty(name="Target Workspace")

    def execute(self, context):
        t_name = self.target_workspace
        d_spaces = bpy.data.workspaces

        path = str(Path(__file__).parent.parent / "workspace_online.blend")
        workspaces_online_name = [
            "0-LIB",
            "1-MOD",
            "2-GN",
            "3-MAT",
            "4-UV",
            "5-MOTION",
            "6-RENDER",
            "7-COMPO",
            "8-SETTING",
        ]

        for online_input in workspaces_online_name:
            if context.workspace.name == online_input:
                self.report({"INFO"}, "已经为该工作空间！")
                return {"CANCELLED"}

            if online_input in d_spaces:
                context.window.workspace = d_spaces[online_input]
                self.report({"INFO"}, '已切换工作空间:"%s"' % (online_input))
                return {"FINISHED"}

            if online_input not in d_spaces:
                bpy.ops.workspace.append_activate(idname=online_input, filepath=path)

                context.window.workspace = d_spaces[online_input]
                self.report({"INFO"}, '已添加工作空间:"%s"' % (online_input))

        return {"FINISHED"}


classes = [
    VIEW3D_PIE_MT_Ctrl_Tab,
    PIE_WorkspaceSwapOperator,
    PIE_Workspace_Import_Online_Operator,
]


addon_keymaps = []


def register_keymaps():
    addon = bpy.context.window_manager.keyconfigs.addon

    keymap_items = {
        "3D View": "VIEW_3D",
        "Node Editor": "NODE_EDITOR",
        "Image": "IMAGE_EDITOR",
        "Graph Editor": "GRAPH_EDITOR",
        "Window": "EMPTY",
    }
    for name, space in keymap_items.items():
        km = addon.keymaps.new(name=name, space_type=space)
        kmi = km.keymap_items.new(
            idname="wm.call_menu_pie",
            type="TAB",
            value="CLICK_DRAG",
            ctrl=True,
            shift=False,
            alt=False,
        )
        kmi.properties.name = "VIEW3D_PIE_MT_Ctrl_Tab"
        addon_keymaps.append(km)

    wspace_names = {
        "0-LIB": "ZERO",
        "1-MOD": "ONE",
        "2-GN": "TWO",
        "4-UV": "FOUR",
        "3-MAT": "THREE",
        "5-MOTION": "FIVE",
        "6-RENDER": "SIX",
        "7-COMPO": "SEVEN",
        "8-SETTING": "EIGHT",
    }

    km = addon.keymaps.new(name="Window")  # , space_type='EMPTY'
    for name, number in wspace_names.items():
        kmi = km.keymap_items.new(
            idname=PIE_WorkspaceSwapOperator.bl_idname,
            type=number,
            value="PRESS",
            ctrl=False,
            shift=False,
            alt=True,
        )
        kmi.properties.target_workspace = name
    addon_keymaps.append(km)

    km = addon.keymaps.new(name="Window")
    kmi = km.keymap_items.new(
        idname=PIE_Workspace_Import_Online_Operator.bl_idname,
        type="NINE",
        value="PRESS",
        ctrl=False,
        shift=False,
        alt=True,
    )

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


def unregister():
    unregister_keymaps()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# if __name__ == "__main__":
#     register()
#     bpy.ops.wm.call_menu_pie(name="VIEW3D_PIE_MT_Ctrl_Tab")
