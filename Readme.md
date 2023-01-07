### Project Name: Feuze
####Requiremnts
- PySide2 (PySide2)
- PyYaml (PyYAML)
- cryptography
- Fileseq
- Qt.py

## Version
### BaseVersion

- init:
    - validate version
    - set path
    - set attribute
    - fetch/set info
    - set type
- create
    - create file path
    - set filepaths based on type
    - update in info file
    - only create if it doesn't exist
- exits
    - check if version exists
    - local and centrally
- new
    - returns new version
- delete
    - delete a version and its files
- copy_from_path
    - create version first
    - copy files from a path
- create_link
    - create version
    - create link to a path
- update_info
    - update info to file and instance
- localise
    - localise files
- centralise
    - centralise local files
- latest
    - get latest available version
- get_all_versions
    - get all version in current name
-

## Config Studio

- create config.yaml in project root folder
- create user config file in
    - Windows: C:\users\<user>\APPNAME\APPNAME.yaml
    - Linux: $HOME/APPNAME/APPNAME.yaml
    - Mac: $HOME/Library/Preferences/APPNAME/APPNAME.yaml
  > APPNAME is set from constant.py (by default Feuze)
- add central/local project root path in user config
-

### How to create project

```python
from feuze.core.fold import Project

# create Project object
project1 = Project(name="ProjectName")

# create project folders and data file
project1.create()

# Create project with additional info , 
# any ifo you want to save in data
project1.create(resolution="1920x1080", fps=24)
```

### Get info from project
```python
from feuze.core.fold import Project

# Get project info
project1 = Project(name="ProjectName")
print(project1.get_info("fps"))
```

### Update info of project
```python
from feuze.core.fold import Project

# Get project info
project1 = Project(name="ProjectName")
project1.update_info(fps=25)

info = {
  "client": "CLIENT NAME",
  "resolution": "1920x1081",
}
project1.update_info(**info)
```

### Project api
```python
from feuze.core.fold import Project

project1 = Project(name="ProjectName")

# check if project exists
project1.exists()

#create sub directories(as configured in config)
project1.create_sub_dirs()

# get all reels/seq in the project
project1.get_reels()

# get path pf the project(server or central path)
path = project1.path

# get local path (from user pc)
local_path = project1.local_path

# get thumbnail 
thumb = project1.thumbnail
```

### Reel/Seq/Ep
Sequence is represented as reel in feuze, like project se also can be created with Reel class
```python
from feuze.core.fold import Reel

reel1 = Reel(project="Project_Name", name="REEL1")
# create reel folder and info file
reel1.create()

# check exists
reel1.exists()

# get all shots in the seq
reel1.get_shots()

```

### Shot
```python
from feuze.core.fold import Shot

shot1 = Shot(project="Project_Name", reel="REEL1", name="SHOT1")
# create reel folder and info file
shot1.create(start=1001, end=1050, other_info="this")

# check exists
shot1.exists()

# create shot sub directories
shot1.create_sub_dirs()

```

### Media
Any file in the pipeline is represented as Media in feuze. For example a work file or an exr input sequence
Media can be file media also data type media which doesn't have physical file but just info
each media type we are going to use needs to be defined in the configuration.

In config
```yaml
MEDIA_TYPES:
  NukeFile:
   media_type: NukeFile
   short_name: NK
   sub_dir: NukeFiles
   name_template: "{name}"
   media_class: FileMedia
   file_type: SingleFile
   extension: nk
   validators: 
    - FileValidator
    - DataValidator
   version_format:  v{major:0>2}.{minor:0>3}
```
**media_type**: this is media type, name for this media config.

**short_name**: short name for this media type. Not in use at present

**sub_dir**: Sub directory in the shot where this media has to be kept

**name_template**: template for media name, can use wild cards from {project}, {reel}, {shot} , {name}

**media_class**: Media subclass to use. This class has to be defined in media module. choices now FileMedia | DataMedia

**file_type**: This is media file type options are Sequence | SingleFile | MultiSequence | None

**extension**: file extension of file.

**validators**: Validator for media creation(not in use now)

**version_format**:  How version is formatted  for example v{major:0>2}.{minor:0>3} will keep version as v01.001
wild card are {major} {minor}

#### How it works
Media object can be created with MediaFactory class, which reads configs and creates appropriate media object.
the object will load media info wile init if the media exist otherwise it will create potential media object version potential version.

```python
from feuze.core.media import MediaFactory
from feuze.core.fold import Shot
shot = Shot(project="Project1", reel="REEL1", name="SHOT1")

# create media object
nuke_file = MediaFactory(shot=shot, name="Final_Comp", media_type="NukeFile")

# create media version object, from media version object you get file potential paths
nuke_file_version = nuke_file.version()

# above will create version object potentially new version, if no version recorded in info
print(nuke_file_version.filepath)
# >>> ..\Projects\XYZ\01_Shots\REEL1\SHOT01\NukeFiles\NukeFile\Final_Comp\Final_Comp_v01.000.nk
```
Initializing a media version checks version in info_file(database) first
if version records found then sets attributes of the object with info from db
if not then sets attributes by evaluating inputs and configs

create method in version object will create entry for that version in info_file
So next time when initialize same version it will load info from that.

```python
from feuze.core.media import MediaFactory
from feuze.core.fold import Shot
shot = Shot(project="Project1", reel="REEL1", name="SHOT1")

# create media object
nuke_file = MediaFactory(shot=shot, name="Final_Comp", media_type="NukeFile")

nuke_file_version = nuke_file.version()

# create file in the path 
# nuke.ScriptSave(nuke_file_version.filepath)

# create data entry
nuke_file_version.create()
```
## TODO
- get all media form shot 
- get meda from path 
- get all versions of a media 
- latest version of a media


## Task
- create task
- assign task
- set status of task
- attach a media to a task
