DEFAULT_PROJECT_PATH = "K:\\NAS"
WORKFLOW_DIRECTORY_NAME = "01_Workflow"
SEQ_FORMAT = "{dirname}{basename}{padding}{extension} {range}"
VERSION_PATTERN = "^[vV]([0-9]+)$"
THREAD_COUNT = 8


class VersionType(object):
    MULTISEQ = "MultiSequence"
    IMAGESEQ = "ImageSequence"
    SINGLEFILE = "SingleImage"


DEFAULT_EXTENSIONS = {
    VersionType.IMAGESEQ: ".exr",
    VersionType.MULTISEQ: ".exr",
    VersionType.SINGLEFILE: ".mov"
}

# Template can include any key in Shot.__dict__ [{project}, {reel}, {shot} , {naem}]
ALL_FOOTAGE_TYPES = {
    "Render": {"name": "Render", "short_name": "GR", "sub_dir": "Renders", "template": "{name}"},
    "Plate": {"name": "Plate", "short_name": "P", "sub_dir": "Plates", "template": "{shot}_{name}"},
    "Output": {"name": "Output", "short_name": "OUT", "sub_dir": "Outputs", "template": "{shot}_{name}"},
    "Precomp": {"name": "Precomp", "short_name": "POUT", "sub_dir": "Renders\Precomps", "template": "POUT_{shot}_{name}"}
}








