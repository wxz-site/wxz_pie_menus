# students = [('john', 'A', 15), ('jane', 'B', 12), ('dave', 'B', 10)]
# print(sorted(students, key=lambda student: student[2]))


keymap_items = {
    '3D View': 'VIEW_3D',
    'Node Editor': 'NODE_EDITOR',
    'Image': 'IMAGE_EDITOR'
}
for i, o in keymap_items.items():
    print(i, o)
