APP_NAME = "feuze"
SEQ_FORMAT = "{dirname}{basename}{padding}{extension} {range}" # TODO check if this is used
VERSION_PATTERN = "^[vV]?(?P<versions>[0-9]+)$" # TODO check if this is used
THREAD_COUNT = 8 # TODO need better name


class VersionType(object):  # TODO check if this is used
    MULTISEQ = "MultiSequence"
    IMAGESEQ = "ImageSequence"
    SINGLEFILE = "SingleFile"
    QUICKTIME = "QuickTime"


class Align:  # TODO check if this is used
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
} # TODO can make it by footage/atask type , aftet implementing media, do we need this

# Template can include any key in Shot.__dict__ [{project}, {reel}, {shot} , {name}]
ALL_FOOTAGE_TYPES = {  #TODO to be removed using media now
    "Render": {"name": "Render", "short_name": "GR", "sub_dir": "Renders", "template": "{name}"},
    "Plate": {"name": "Plate", "short_name": "P", "sub_dir": "Plates", "template": "{shot}_{name}"},
    "Output": {"name": "Output", "short_name": "OUT", "sub_dir": "Outputs", "template": "{shot}_{name}"},
    "Precomp": {"name": "Precomp", "short_name": "POUT", "sub_dir": "Renders\Precomps", "template": "POUT_{shot}_{name}"},
    "Passrender": {"name": "Passrender", "short_name": "PR", "sub_dir": "Comp\Passrenders", "template": "PR_{shot}_{name}"},
    "Qt": {"name": "Qt", "short_name": "QT", "sub_dir": "QT", "template": "{shot}_{name}"}
}

ALL_TASK_TYPES = {
    "Comp": {
        "short_name": "CMP",
        "sub_dir": "Comp",
        "task_names": ["final", "previz", "trailer", "temp"],
        "validators": [ # TODO work on this, this is validator which is not implemented yet
            {
                "name": "HasMediaAttached",
                "args": ["Render", "Final"],
                "kwargs": {}
            }
        ]
    },
}

# Template can include any key in Shot.__dict__ [{project}, {reel}, {shot} , {name}] TODO Media
MEDIA_TYPES = {
    "_default": {
        "media_type": "FileMedia",
        "short_name": "FLS",
        "sub_dir": "Files",
        "name_template": "{name}",  # [{project}, {reel}, {shot} , {name}]
        "media_class": "FileMedia",  # FileMedia | DataMedia
        "file_type": "MultiSequence",  # Sequence | SingleFile | MultiSequence | None
        "extension": None,
        "validators": ["FileValidator", "DataValidator"],
        "version_format": "v{major:0>2}" #"v{major:0>2}.{minor:0>3}"  # {major} {minor}
    },
    "Render": {
        "media_type": "Render",
        "short_name": "RNDR",
        "sub_dir": "Renders",
        "extension": "exr",
        "file_type": "Sequence",
    },
    "NukeScript": {
        "media_type": "NukeScript",
        "short_name": "NK",
        "extension": "nk",
        "file_type": "SingleFile",
        "version_format": "v{major:0>2}.{minor:0>3}"
    }
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

USER_ROLES = {
    "admin": ["super_admin", "user_admin", "project_admin", "task_assign"],
    "user": []
}

# ROLES TODO for documentation
"""
task_assign: Can assign or reassign task
user_admin: Can create delete users
project_admin: Can create projects/scene/shot
"""


TASK_STATUSES = [
    {"status": "Done", "full_name": "Done", "short_name": "DONE", "color": "#ffffff"},
    {"status": "Wip", "full_name": "Work In Progress", "short_name": "WIP", "color": "#ffffff"},
    {"status": "Review", "full_name": "For Review", "short_name": "REVW", "color": "#ffffff"},
    {"status": "Assigned", "full_name": "Assigned", "short_name": "ASND", "color": "#ffffff"},
    {"status": "Correction", "full_name": "Correction", "short_name": "CRCN", "color": "#ffffff"},
]
SHOT_STATUSES = [
    {"status": "Final", "full_name": "Final", "short_name": "FNL", "color": "#ffffff"},
    {"status": "Approved", "full_name": "Internal Approved", "short_name": "APPRV", "color": "#ffffff"},
    {"status": "Client", "full_name": "Sent to client", "short_name": "CLNT", "color": "#ffffff"},
    {"status": "Started", "full_name": "Work Started", "short_name": "STRT", "color": "#ffffff"},
    {"status": "Review", "full_name": "For Started", "short_name": "REVW", "color": "#ffffff"},
    {"status": "Omitted", "full_name": "Omitted", "short_name": "OMIT", "color": "#ffffff"},
    {"status": "Hold", "full_name": "On Hold", "short_name": "HOLD", "color": "#ffffff"},

]