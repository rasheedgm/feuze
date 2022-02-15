APP_NAME = "frolic"
SEQ_FORMAT = "{dirname}{basename}{padding}{extension} {range}"
VERSION_PATTERN = "^[vV]([0-9]+)$"
THREAD_COUNT = 8


class VersionType(object):
    MULTISEQ = "MultiSequence"
    IMAGESEQ = "ImageSequence"
    SINGLEFILE = "SingleImage"
    QUICKTIME = "QuickTime"


class Align:
    VERTICAL = "Vertical"
    HORIZONTAL = "Horizontal"
    RIGHT = "Right"
    LEFT = "Left"


class Location:
    LOCAL = "Local"
    CENTRAL = "Central"
    BOTH = "Both"
    NONE = None


DEFAULT_EXTENSIONS = {
    VersionType.IMAGESEQ: ".exr",
    VersionType.MULTISEQ: ".exr",
    VersionType.SINGLEFILE: ".mov"
}

# Template can include any key in Shot.__dict__ [{project}, {reel}, {shot} , {name}]
ALL_FOOTAGE_TYPES = {
    "Render": {"name": "Render", "short_name": "GR", "sub_dir": "Renders", "template": "{name}"},
    "Plate": {"name": "Plate", "short_name": "P", "sub_dir": "Plates", "template": "{shot}_{name}"},
    "Output": {"name": "Output", "short_name": "OUT", "sub_dir": "Outputs", "template": "{shot}_{name}"},
    "Precomp": {"name": "Precomp", "short_name": "POUT", "sub_dir": "Renders\Precomps", "template": "POUT_{shot}_{name}"},
    "Passrender": {"name": "Passrender", "short_name": "PR", "sub_dir": "Comp\Passrenders", "template": "PR_{shot}_{name}"},
    "Qt": {"name": "Qt", "short_name": "QT", "sub_dir": "QT", "template": "{shot}_{name}"}
}

# directory names
WORKFLOW_DIR_NAME = "01_Shots"
DAILIES_DIR_NAME = "02_Dailies"
ASSETS_DIR_NAME = "03_Assets"
FROM_CLIENT_DIR_NAME = "04_From_Client"
TO_CLIENT_DIR_NAME = "05_To_Client"


# TODO make it universal
# Either this or from global config
SHOT_SUB_DIRS = [
    "CG/CG_Renders",
    "CG/CG_Scripts",
    "Comp/Passrenders",
    "Comp/Script",
    "FBX",
    "Mattepaint",
    "Outputs",
    "Plates",
    "QT",
    "Renders",
    "Track",
]







