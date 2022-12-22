import os
import shutil
this_path = os.path.dirname(__file__)

print(this_path)

# for root, dirs, files in os.walk("K:\\feuze\\src"):
#     if root.endswith("__pycache__"):
#         continue
#     print((root, dirs, files))

src_path = os.path.join(this_path, "src")
dest_path = os.path.join(this_path, ".build", "feuze")
all = [
(src_path, ['core', 'ui'], ['__init__.py']),
(src_path + '\\core', [], ['attachment.py', 'badge.py', 'configs.py', 'constant.py', 'fold.py', 'media.py', 'status.py', 'task.py', 'user.py', 'utility.py', 'version.py', '__init__.py']),
(src_path + '\\ui', ['base'], ['main_window.py', 'models.py', 'utility.py', 'widgets.py', 'windows.py', '__init__.py']),
(src_path + '\\ui\\base', [], ['dialog.py', 'generic.py', 'icons_rc.py', 'input.py', 'main_window_ui.py', 'placer_ui.py', '__init__.py']),
]

try:
    shutil.rmtree(dest_path)
except FileNotFoundError:
    pass
for root, dirs, files in all:
    dest = root.replace(src_path, dest_path)
    try:
        os.makedirs(os.path.normpath(dest))
    except FileExistsError:
        pass
    for dir in dirs:
        d = os.path.join(dest, dir)
        try:
            os.makedirs(os.path.normpath(d))
        except FileExistsError:
            pass
    for f in files:
        os.link(os.path.join(root, f), os.path.join(dest, f))


