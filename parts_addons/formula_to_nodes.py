bl_info = {
    "name": "node_quick_maths",
    "author": "Erin MacDonald",
    "version": (1, 1, 9),
    "blender": (4, 2, 0),
    "description": "A fast way to make long math chains in node editors",
    "category": "Node",
}
import ast
from abc import abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Generic, Literal, NoReturn, Self, TypeAlias, TypeVar, Union

import bpy
from bpy.types import Context, Event, UILayout

from ..utils import get_prefs

# from __future__ import annotations


T = TypeVar("T", covariant=True)
E = TypeVar("E", covariant=True)


class Ok(Generic[T]):
    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        self._value = value

    def is_err(self) -> Literal[False]:
        return False

    def unwrap(self) -> T:
        return self._value

    def unwrap_err(self) -> NoReturn:
        raise Exception("Unwrapped an err on an Ok value")


class Err(Generic[E]):
    __slots__ = ("_value",)

    def __init__(self, value: E) -> None:
        self._value = value

    def is_err(self) -> Literal[True]:
        return True

    def unwrap(self) -> NoReturn:
        raise Exception("Unwrapped on an Err value")

    def unwrap_err(self) -> E:
        return self._value


Result: TypeAlias = Union[Ok[T], Err[E]]


BAD_MATH_AST_NODES = (
    ast.BoolOp,
    ast.NamedExpr,
    ast.Lambda,
    ast.IfExp,
    ast.Dict,
    ast.Set,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.Await,
    ast.Yield,
    ast.YieldFrom,
    ast.FormattedValue,
    ast.JoinedStr,
    ast.Attribute,
    ast.Subscript,
    ast.Starred,
    ast.List,
    ast.Tuple,
    ast.Slice,
)

SHADER_MATH_CALLS = {  # Function inputs in python, names Blender
    # -------
    # Functions
    # ADD, SUBTRACT, MULTIPLY, DIVIDE, POWER have dedicated operators
    "log": ((1, 2), "LOGARITHM"),  # (x[, base])
    "sqrt": ((1,), "SQRT"),  # (x)
    "abs": ((1,), "ABSOLUTE"),  # (x)
    "exp": ((1,), "EXPONENT"),  # (x)
    # -------
    # Comparison
    "min": ((2,), "MINIMUM"),  # (x, y)
    "max": ((2,), "MAXIMUM"),  # (x, y)
    # LESS_THAN, GREATER_THAN have dedicated operators
    "sign": ((1,), "SIGN"),  # (x), SIGN
    "cmp": ((3,), "COMPARE"),  # (x, y, z)
    "smin": ((3,), "SMOOTH_MIN"),  # (x, y, z)
    "smax": ((3,), "SMOOTH_MAX"),  # (x, y, z)
    # -------
    # Rounding
    "round": ((1,), "ROUND"),  # (x)
    "floor": ((1,), "FLOOR"),  # (x)
    "ceil": ((1,), "CEIL"),  # (x)
    "trunc": ((1,), "TRUNC"),  # (x)
    "int": ((1,), "TRUNC"),  # alias for truncate
    "frac": ((1,), "FRACT"),  # (x)
    # MODULO has a dedicated operator
    "fmod": ((2,), "FLOORED_MODULO"),  # (x, y)
    "wrap": ((3,), "WRAP"),  # (x, y, z)
    "snap": ((2,), "SNAP"),  # (x, y)
    "pingpong": ((2,), "PINGPONG"),  # (x, y)
    # -------
    # Trigonometric
    "sin": ((1,), "SINE"),  # (x)
    "cos": ((1,), "COSINE"),  # (x)
    "tan": ((1,), "TANGENT"),  # (x)
    "asin": ((1,), "ARCSINE"),  # (x)
    "acos": ((1,), "ARCCOSINE"),  # (x)
    "atan": ((1,), "ARCTANGENT"),  # (x)
    "atan2": ((2,), "ARCTAN2"),  # (x, y)
    "sinh": ((1,), "SINH"),  # (x)
    "cosh": ((1,), "COSH"),  # (x)
    "tanh": ((1,), "TANH"),  # (x)
    # -------
    # Conversion
    "rad": ((1,), "RADIANS"),  # (x)
    "deg": ((1,), "DEGREES"),  # (x)
}

PRINTABLE_SHADER_MATH_CALLS = {
    "Functions": (
        "+  加法",
        "-  减法",
        "*  乘法",
        "/  除法",
        "**  乘方",
        "log(x[, base])  对数",
        "sqrt(x)  平方根",
        "abs(x)  绝对值",
        "exp(x)  指数",
    ),
    "Comparison": (
        "min(x, y)  最小值",
        "max(x, y)  最大值",
        "x > y  小于",
        "x < y  大于",
        "sign(x)  符号",
        "cmp(x, y, z)  比较",
        "smin(x, y, z)  平滑最小值",
        "smax(x, y, z)  平滑最大值",
    ),
    "Rounding": (
        "round(x)  四舍五入",
        "floor(x)  向下取整",
        "ceil(x)  向上取整",
        "trunc(x)  截断",
        "frac(x)  分数",
        "x % y  截断取模",
        "fmod(x, y)  向下取模",
        "wrap(x, y, z)  循环",
        "snap(x, y)  吸附",
        "pingpong(x, y)  乒-乓",
    ),
    "Trigonometric": (
        "sin(x)  正弦",
        "cos(x)  余弦",
        "tan(x)  正切",
        "asin(x)  反正弦",
        "acos(x)  反余弦",
        "atan(x)  反正切",
        "atan2(x,y)  反正切2",
        "sinh(x)  双曲正弦",
        "cosh(x)  双曲余弦",
        "tanh(x)  双曲正切",
    ),
    "Conversion": ("rad(x)  到弧度", "deg(x)  到角度"),
}


SHADER_NODE_BASIC_OPS = {
    ast.Add: "ADD",
    ast.Sub: "SUBTRACT",
    ast.Mult: "MULTIPLY",
    ast.Div: "DIVIDE",
    ast.Mod: "MODULO",
    ast.Pow: "POWER",
}


VARIABLE_NAME = str


@dataclass
class Operation:
    name: str
    inputs: "list[int | float | str | Operation]"

    @classmethod
    @abstractmethod
    def validate(
        cls,
        e: ast.Module,
        bad_nodes: tuple[type[ast.expr], ...] = BAD_MATH_AST_NODES,
        functions: dict[str, tuple[tuple[int, ...], str]] = SHADER_MATH_CALLS,
    ) -> Result[tuple, str]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def parse(cls, e: ast.expr) -> int | float | str | Self:
        raise NotImplementedError

    def to_tree(self):
        return Tree(variables=list(self.variables()), root=self)

    def variables(self) -> set[VARIABLE_NAME]:
        vars: set[VARIABLE_NAME] = set()
        for input in self.inputs:
            if isinstance(input, Operation):
                vars.update(input.variables())
            elif isinstance(input, VARIABLE_NAME):
                vars.add(input)
        return vars

    @abstractmethod
    def create_node(self, nt: bpy.types.NodeTree) -> bpy.types.Node:
        raise NotImplementedError

    def generate(self, nt: bpy.types.NodeTree) -> tuple[
        bpy.types.Node,
        list[list[bpy.types.Node]],
        list[tuple[str, bpy.types.NodeInputs]],
    ]:
        """
        Creates nodes. returns a list of tuples of
        (
            toplevel node,
            subtrees
            input socket
        )
        """
        parent = self.create_node(nt)

        oinputs = []
        children: list[bpy.types.Node] = []

        # [
        #     [                    child1,                                         child2                    ],
        #     [       child1.1,                child1.2,              child2.1,               child2.2       ],
        #     [child1.1.1, child1.1.2, child1.2.1, child1.2.2, child2.1.1, child2.1.2, child2.2.1, child2.2.2],
        # ]
        layers: list[list[bpy.types.Node]] = []

        for idx, child in enumerate(self.inputs):
            if isinstance(child, Operation):
                node, sublayers, inputs = child.generate(nt)
                oinputs.extend(inputs)
                nt.links.new(node.outputs[0], parent.inputs[idx])

                # add each layer to the tree
                if sublayers:
                    for idx, layer in enumerate(sublayers):
                        if len(layers) <= idx:
                            layers.append([])

                        layers[idx].extend(layer)

                # add the node to children
                children.append(node)

            elif isinstance(child, str):  # add it to the oinputs
                oinputs.append((child, parent.inputs[idx]))
            else:
                parent.inputs[idx].default_value = child

        if children:
            layers.insert(0, children)

        return parent, layers, oinputs


class ShaderMathOperation(Operation):
    def create_node(self, nt: bpy.types.NodeTree) -> bpy.types.Node:
        node = nt.nodes.new("ShaderNodeMath")
        node.operation = self.name
        return node

    @classmethod
    def _check_bad_type(cls, node: ast.Constant) -> Result[tuple, str]:
        if not isinstance(node.value, (int, float)):
            return Err(f"常量不能是整数或浮点数以外的任何东西.\n{node.value} 不允许")
        return Ok(())

    @classmethod
    def validate_node(
        cls,
        node: ast.Expr,
        bad_nodes: tuple[type[ast.expr], ...],
        functions: dict[str, tuple[tuple[int, ...], str]],
    ) -> Result[tuple, str]:
        # check if node is bad
        if any(isinstance(node, bad_node) for bad_node in bad_nodes):
            return Err(f"Do not use node of type: {type(node)} ")

        # check if node is a constant and it is a disallowed type
        if isinstance(node, ast.Constant):
            r = cls._check_bad_type(node)
            if r.is_err():
                return r

        # check if node is a call and it has an allowed function name
        if isinstance(node, ast.Call):
            name: ast.Name = node.func
            allowed_nums = functions.get(name.id)
            if allowed_nums is None:
                Err(f"无法识别的函数名: '{name.id}'")
            # check if the number of arguments align with the number of arguments in the GOOD_CALLS
            elif all(len(node.args) != x for x in allowed_nums[0]):
                return Err(
                    f"Function {name.id} is allowed, but\nthe number of arguments is wrong\n({len(node.args)} is not in {allowed_nums[0]})"
                )

        return Ok(())

    @classmethod
    def validate(
        cls,
        e: ast.Module,
        bad_nodes: tuple[type[ast.expr], ...] = BAD_MATH_AST_NODES,
        functions: dict[str, tuple[tuple[int, ...], str]] = SHADER_MATH_CALLS,
    ) -> Result[tuple, str]:
        # check that the node in the ast body is just an Expr
        expr: ast.stmt

        if not e.body:
            return Err("表达式为空")

        if not isinstance((expr := e.body[0]), ast.Expr):  # Unsure how this can show up
            return Err("表达式类型无效。只能创建允许的数学表达式!")

        for node in ast.walk(expr):
            r = cls.validate_node(node, bad_nodes, functions)
            if r.is_err():
                return r

        return Ok(())

    @classmethod
    def parse(cls, e: ast.expr) -> int | float | str | Self:
        if isinstance(e, ast.BinOp):
            op = e.op

            if type(op) in SHADER_NODE_BASIC_OPS:
                # check for Multiply Add
                if isinstance(op, ast.Add):
                    if isinstance(e.left, ast.BinOp) and isinstance(e.left.op, ast.Mult):
                        return cls(
                            name="MULTIPLY_ADD",
                            inputs=[
                                cls.parse(e.left.left),
                                cls.parse(e.left.right),
                                cls.parse(e.right),
                            ],
                        )
                    elif isinstance(e.right, ast.BinOp) and isinstance(e.right.op, ast.Mult):
                        return cls(
                            name="MULTIPLY_ADD",
                            inputs=[
                                cls.parse(e.right.left),
                                cls.parse(e.right.right),
                                cls.parse(e.left),
                            ],
                        )
                return cls(
                    name=SHADER_NODE_BASIC_OPS[type(op)],
                    inputs=[cls.parse(e.left), cls.parse(e.right)],
                )
            elif isinstance(op, ast.FloorDiv):
                return cls(
                    name="FLOOR",
                    inputs=[
                        cls(
                            name="DIVIDE",
                            inputs=[cls.parse(e.left), cls.parse(e.right)],
                        ),
                        0,
                    ],
                )
            else:
                raise NotImplementedError(f"Unhandled operation {op}")

        if isinstance(e, ast.UnaryOp) and isinstance(e.op, ast.USub):
            if isinstance(e.operand, ast.Constant):
                return -e.operand.value
            else:
                return cls(
                    name="MULTIPLY",
                    inputs=[cls.parse(e.operand), -1],
                )

        if isinstance(e, ast.Compare):
            if isinstance(e.ops[0], (ast.Gt, ast.GtE)):
                return cls(
                    name="GREATER_THAN",
                    inputs=[cls.parse(e.left), cls.parse(e.comparators[0])],
                )
            elif isinstance(e.ops[0], (ast.Lt, ast.LtE)):
                return cls(
                    name="LESS_THAN",
                    inputs=[cls.parse(e.left), cls.parse(e.comparators[0])],
                )
            elif isinstance(e.ops[0], ast.Eq):  # Opinion
                return cls(
                    name="COMPARE",
                    inputs=[
                        cls.parse(e.left),
                        cls.parse(e.comparators[0]),
                        0.5,
                    ],
                )

        if isinstance(e, ast.Call):
            inputs = []
            for arg in e.args:
                inputs.append(cls.parse(arg))

            return cls(name=SHADER_MATH_CALLS[e.func.id][1], inputs=inputs)

        if isinstance(e, ast.Constant):
            return e.value

        if isinstance(e, ast.Name):
            return e.id

        if isinstance(e, ast.Expr):
            return cls.parse(e.value)

        raise NotImplementedError(f"未处理的表达式 {ast.dump(e, indent=4)}")


class CompositorMathOperation(ShaderMathOperation):
    def create_node(self, nt: bpy.types.NodeTree) -> bpy.types.Node:
        node: bpy.types.CompositorNodeMath = nt.nodes.new("CompositorNodeMath")
        node.operation = self.name
        return node


class TextureMathOperation(ShaderMathOperation):
    def create_node(self, nt: bpy.types.NodeTree) -> bpy.types.Node:
        node: bpy.types.TextureNodeMath = nt.nodes.new("TextureNodeMath")
        node.operation = self.name
        return node


@dataclass
class Tree:
    variables: list[VARIABLE_NAME]
    root: Operation


def _new_reroute(nt: bpy.types.NodeTree, name: str):
    node = nt.nodes.new("NodeReroute")
    if name:
        node.label = name
    return node


InputSocketType = [
    ("VALUE", "值", "使用值连接变量。"),
    ("REROUTE", "转接点", "使用转接点连接变量。"),
    ("GROUP", "节点组", "使用节点组打包创建。"),
]


@dataclass
class ComposeNodes:
    socket_type: str = "VALUE"
    center_nodes: bool = True
    hide_nodes: bool = False

    tree_type: ClassVar[str]
    group_type: ClassVar[str]

    def preview_generate(self, root: Operation, layout: UILayout) -> None:
        """Generates a node tree, but inside a uiLayout for previewing"""
        child_col = layout.column(align=True)
        for input in root.inputs:
            input_row = child_col.box().row()
            if isinstance(input, Operation):
                # gengenerate_previewr the child operation
                self.preview_generate(input, input_row)
            elif not self.hide_nodes:
                input_row.label(text=str(input))

        # # create a row for the current node's name
        # root_row = row.column(align=True)
        layout.label(text=root.name)
        ...

    def run(
        self,
        source: ast.Expr,
        tree: Tree,
        context: bpy.types.Context,
    ):
        bpy.ops.node.select_all(action="DESELECT")
        # Hmm...
        space_data: bpy.types.SpaceNodeEditor = context.space_data
        nt: bpy.types.NodeTree = space_data.edit_tree

        layers = self.execute(source, tree, nt, group_offset=space_data.cursor_location)

        if self.socket_type != "GROUP":
            offset = space_data.cursor_location
        else:
            offset = (0.0, 0.0)

        # node.height is too small to represent the actual visible height of the nodes
        # for some reason, so these are a little bigger than the width margin
        if self.hide_nodes:
            height_margin = -20
        else:
            height_margin = 60
        width_margin = 20

        layer_heights: list[float] = []
        for layer in layers:
            if self.hide_nodes:
                for node in layer:
                    node.hide = True

            # calculate the total height of the layer
            height = 0
            for node in layer:
                height += node.height + height_margin
            layer_heights.append(height)

        max_height = max(layer_heights)

        # loop through every layer in the subtrees, move them to the correct location
        for l_idx, (layer, layer_heights) in enumerate(zip(layers, layer_heights)):
            # offset the layer by user-defined rules
            if self.center_nodes:
                layer_offset = (
                    offset[0],
                    offset[1] - ((max_height / 2) - (layer_heights / 2)),
                )
            else:
                layer_offset = offset

            # move the nodes
            for n_idx, node in enumerate(layer):
                position = (
                    (layer_offset[0] - (node.width + width_margin) * l_idx),
                    (layer_offset[1] - (node.height + height_margin) * n_idx),
                )
                node.location = position

        bpy.ops.node.translate_attach_remove_on_cancel("INVOKE_DEFAULT")

        return {"FINISHED"}

    @staticmethod
    @abstractmethod
    def _new_value(nt: bpy.types.NodeTree, name: str = ""):
        _new_reroute(nt, name)

    def execute(
        self,
        source: ast.Expr,
        tree: Tree,
        nt: bpy.types.NodeTree,
        group_offset=(0, 0),
    ) -> list[list[bpy.types.Node]]:
        sublayers: list[list[bpy.types.Node]]

        if self.socket_type == "GROUP":
            group = bpy.data.node_groups.new(ast.unparse(source), self.tree_type)

            # add group to node tree
            node = nt.nodes.new(self.group_type)
            node.location = group_offset
            node.node_tree = group

            nt = group
            interface = nt.interface

        node, sublayers, inputs = tree.root.generate(
            nt=nt,
        )

        sublayers.insert(0, [node])

        if self.socket_type == "GROUP":
            # create the input sockets
            group_input = nt.nodes.new("NodeGroupInput")
            sublayers.append([group_input])

            # create the output socket
            group_output = nt.nodes.new("NodeGroupOutput")
            interface.new_socket(name="Output", in_out="OUTPUT", socket_type="NodeSocketFloat")
            nt.links.new(node.outputs[0], group_output.inputs[0])
            sublayers.insert(0, [group_output])

            # add the variables to the interface
            sockets = {}
            for variable in tree.variables:
                interface.new_socket(name=variable, in_out="INPUT", socket_type="NodeSocketFloat")
                sockets[variable] = group_input.outputs[variable]

        else:
            # Create the variables nodes
            sockets = {}
            layer = []
            for variable in tree.variables:
                if self.socket_type == "REROUTE":
                    node = _new_reroute(nt, name=variable)
                elif self.socket_type == "VALUE":
                    node = self._new_value(nt, name=variable)
                layer.append(node)
                sockets[variable] = node.outputs[0]
            sublayers.append(layer)

        # Connect the nodes to the corresponding sockets
        for variable, input in inputs:
            nt.links.new(sockets[variable], input)

        return sublayers


class ComposeShaderMathNodes(ComposeNodes):
    tree_type = "ShaderNodeTree"
    group_type = "ShaderNodeGroup"

    @staticmethod
    def _new_value(nt: bpy.types.NodeTree, name: str = ""):
        node = nt.nodes.new("ShaderNodeValue")
        if name:
            node.label = name
        return node


class ComposeGeometryMathNodes(ComposeShaderMathNodes):
    tree_type = "GeometryNodeTree"
    group_type = "GeometryNodeGroup"


class ComposeCompositorMathNodes(ComposeNodes):
    tree_type = "CompositorNodeTree"
    group_type = "CompositorNodeGroup"

    @staticmethod
    def _new_value(nt: bpy.types.NodeTree, name: str = ""):
        node = nt.nodes.new("CompositorNodeValue")
        if name:
            node.label = name
        return node


class ComposeTextureMathNodes(ComposeNodes):
    tree_type = "TextureNodeTree"
    group_type = "TextureNodeGroup"


class ComposeNodeTree(bpy.types.Operator):
    bl_idname = "node.formula_to_nodes"
    bl_label = "表达式公式转换为节点："

    show_available_functions: bpy.props.BoolProperty(
        name="展示表达式规则",
        default=True,
    )  # type: ignore
    hide_nodes: bpy.props.BoolProperty(
        name="折叠节点",
        description="隐藏节点以保留网格空间。",
    )  # type: ignore
    center_nodes: bpy.props.BoolProperty(
        name="节点居中",
        description="使生成的节点居中。这是个人喜好。",
    )  # type: ignore

    editor_type: bpy.props.StringProperty(name="编辑器类型")  # type: ignore
    expression: bpy.props.StringProperty(name="公式表达式", description="节点的源表达式。")  # type: ignore
    input_socket_type: bpy.props.EnumProperty(items=InputSocketType, default="REROUTE")  # type: ignore
    generate_previews: bool

    def invoke(self, context: Context, event: Event) -> set[str]:
        wm = context.window_manager
        ui_mode = context.area.ui_type
        self.editor_type = ui_mode
        if get_prefs().debug_prints:
            print(f"NQM: Editor type: {self.editor_type}")

        self.generate_previews = get_prefs().generate_previews

        # return wm.invoke_props_dialog(self, confirm_text="Create", width=800)
        return wm.invoke_props_dialog(self, width=800)

    def current_operation_type(
        self,
    ) -> tuple[type[Operation], type[ComposeNodes]] | None:
        if self.editor_type == "ShaderNodeTree":
            return (ShaderMathOperation, ComposeShaderMathNodes)
        elif self.editor_type == "GeometryNodeTree":
            return (ShaderMathOperation, ComposeGeometryMathNodes)
        elif self.editor_type == "CompositorNodeTree":
            return (CompositorMathOperation, ComposeCompositorMathNodes)
        elif self.editor_type == "TextureNodeTree":
            return (TextureMathOperation, ComposeTextureMathNodes)
        else:
            return None

    def generate_tree(self, expression: str) -> Result[tuple[ast.Expr, Tree], str]:
        op_type = self.current_operation_type()
        if op_type is None:
            return Err("解析的表达式含有无法识别的操作符")
        op, _ = op_type
        try:
            mod = ast.parse(expression, mode="exec")

            r = op.validate(mod)
            if r.is_err():
                return Err(r.unwrap_err())

            expr: ast.Expr = mod.body[0]
        except SyntaxError:
            return Err("无法解析表达式")

        try:
            parsed = op.parse(expr)
        except Exception as e:
            return Err(str(e))
        if not isinstance(parsed, Operation):
            return Err("解析的表达式含有无法识别的操作符")

        return Ok((expr, parsed.to_tree()))

    def execute(self, context: Context):
        # Create nodes from tree
        try:
            bpy.ops.node.select_all(action="DESELECT")
        except:
            self.report({("ERROR", "请先创建节点树")})
            pass
        tree = self.generate_tree(self.expression)
        o = self.current_operation_type()
        if tree.is_err() or o is None:
            return {"CANCELLED"}

        expr, tree = tree.unwrap()
        _, composer_class = o

        composer = composer_class(
            socket_type=self.input_socket_type,
            center_nodes=self.center_nodes,
            hide_nodes=self.hide_nodes,
        )

        return composer.run(expr, tree, context)

    def draw(self, context: Context):
        layout = self.layout

        o = self.current_operation_type()
        if o is None:
            layout.label(text="当前不支持此节点编辑器!")
            return
        opt, comp = o

        layout.prop(self, "expression")

        options_box = layout.box()
        options = options_box.column(align=True)

        options.prop(self, "input_socket_type", expand=True)
        options.prop(self, "hide_nodes")
        options.prop(
            self,
            "center_nodes",
        )
        options.prop(self, "show_available_functions")

        if self.show_available_functions:
            functions_box = layout.column()
            functions_box.label(text="可用的表达式:")
            functions_box.separator()
            b = functions_box.box()
            row = b.row()
            for type_, funcs in PRINTABLE_SHADER_MATH_CALLS.items():
                func_row = row.column(heading=type_)
                for func in funcs:
                    func_row.label(text=func, translate=False)

        txt = self.expression

        if txt:
            r = self.generate_tree(txt)
            if r.is_err():  # print the error
                msg = r.unwrap_err()

                b = layout.box()
                err_col = b.column()
                err_col.label(text="Error:")
                for line in msg.splitlines():
                    err_col.label(text=line, translate=False)
            elif self.generate_previews:  # create a representation of the node tree under the settings
                preview_box = layout.box()

                composer = comp(
                    socket_type=self.input_socket_type,
                    center_nodes=self.center_nodes,
                    hide_nodes=self.hide_nodes,
                )
                composer.preview_generate(r.unwrap()[1].root, preview_box.row())


# class Preferences(bpy.types.AddonPreferences):
#     bl_idname = __package__

#     debug_prints: bpy.props.BoolProperty(
#         name="Debug prints",
#         description="Enables debug prints in the terminal.",
#         default=False,
#     )

#     def draw(self, context):
#         layout = self.layout

#         row = layout.column(align=True)
#         row.label(text="Check the Keymaps settings to edit activation. Default is Ctrl + M")
#         row.prop(self, "debug_prints")


addon_keymaps = []


def registerKeymaps():
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.get("Node Editor")
        if not km:
            km = wm.keyconfigs.addon.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")

        kmi = km.keymap_items.new(
            "node.formula_to_nodes",
            "M",
            "PRESS",
            ctrl=True,
        )
        addon_keymaps.append((km, kmi))


def unregisterKeymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def draw_header_menu_button(self, context):
    layout = self.layout
    layout.operator("node.formula_to_nodes", text="表达式转节点")


classes = (ComposeNodeTree,)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
    registerKeymaps()
    bpy.types.NODE_HT_header.append(draw_header_menu_button)


def unregister():
    # unregisterKeymaps()
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    registerKeymaps()
    bpy.types.NODE_HT_header.remove(draw_header_menu_button)


if __name__ == "__main__":
    register()