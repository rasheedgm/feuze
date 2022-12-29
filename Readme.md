### Project Name: Feuze
####Requiremnts
- PySide2 (PySide2)
- PyYaml (PyYAML)
- cryptography
- Fileseq
- Qt.py

#### something else
- Testing this
- need some example

<code > this is code block</code>

```python
# comment
from feuze.core.configs import UserConfig
# just test
```

## Version
### BaseVerson

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
    - only create if doesnt exits
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
    - create verion
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



