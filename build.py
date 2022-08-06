import os
import shutil


# for root, dirs, files in os.walk("K:\\feuze\\src"):
#     if root.endswith("__pycache__"):
#         continue
#     print((root, dirs, files))
all = [
('K:\\feuze\\src', ['core', 'ui'], ['__init__.py']),
('K:\\feuze\\src\\core', [], ['badge.py', 'configs.py', 'constant.py', 'fold.py', 'media.py', 'status.py', 'task.py', 'user.py', 'utility.py', 'version.py', '__init__.py']),
('K:\\feuze\\src\\ui', ['base'], ['main_window.py', 'models.py', 'utility.py', 'widgets.py', 'windows.py', '__init__.py']),
('K:\\feuze\\src\\ui\\base', [], ['dialog.py', 'generic.py', 'icons_rc.py', 'input.py', 'main_window_ui.py', 'placer_ui.py', '__init__.py']),
]
try:
    shutil.rmtree("K:\\feuze\\.build\\feuze")
except FileNotFoundError:
    pass
for root, dirs, files in all:
    dest = root.replace("K:\\feuze\\src", "K:\\feuze\\.build\\feuze")
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


