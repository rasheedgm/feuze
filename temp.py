from feuze.core.attachment import AttachmentManager, Attachment
from feuze.core.fold import Shot
from feuze.core.media import MediaFactory, media_from_path
from feuze.core.status import StatusManager
from feuze.core.task import Task
from feuze.core.user import User, Auth, Role
from feuze.core.configs import GlobalConfig


#
# user = User(name="admin")

auth = Auth("admin", "admin")
auth.authorise()

user1 = User("user")
user_role = Role("user")
# user1.create(auth=auth, full_name="user_pass",role=user_role, password="pass")
#  c

# # user.create(auth=None, full_name="Admin", role="admin", password="admin")
shot = Shot(project="XYZ", reel="REEL01", name="SHOT02")

# create media object
nuke_file = MediaFactory(shot=shot, name="Final_Comp", media_type="NukeFile")

# create media version object, from media version object you get file potential paths
nuke_file_version = nuke_file.version()
# above will create version object potentially new version, if no version recorded in info
# print(nuke_file_version.filepath)
# >>> ..\Projects\XYZ\01_Shots\REEL01\SHOT02\NukeFiles\NukeFile\Final_Comp\Final_Comp_v01.000.nk
m = media_from_path(r"C:\Users\gmabd\Documents\Feuze\Projects\XYZ\01_Shots\REEL01\SHOT02\NukeFiles\NukeFile\Final_Comp")
print(m.media_type)

#
# media = MediaFactory(shot, name="comp", media_type="Render")w
# task = Task(shot=shot, name="final", task_type="Comp")
# task.create()
# manager = StatusManager(task)
#
# t_v = task.version("latest")
# # t_v.create()
# # t_v.commit("Commit this again")
# manager.set_status("Wip")
#
# at_manage = AttachmentManager(t_v)
# for at in at_manage.fetch().values():
#     print(at)
#
# print(manager.get_current_status())
#
# # at_manage.attach(Attachment(name="workfile", path=media.version("latest").filepath))
#
# # t_v.create()
# version = media.version(1)
#
# # print(version.create())