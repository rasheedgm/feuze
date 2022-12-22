import os.path
import yaml
import datetime

from feuze.core import utility
from feuze.core.configs import GlobalConfig, UserConfig
from cryptography.fernet import Fernet


class Role(object):
    __all_roles = GlobalConfig.user_roles

    def __init__(self, role):
        super(Role, self).__init__()
        if role not in self.__all_roles.keys():
            raise Exception("Roles doesn't exists")
        self._name = role
        self._permissions = self.__all_roles[role]

    def has(self, permission):
        return permission in self._permissions

    @property
    def name(self):
        return self._name

    @property
    def permissions(self):
        return self._permissions


class Password(object):
    """password manage class"""
    __crypto = Fernet(key="gxPRh9GuWibLupSwBqKc55GQrcmPwdZJFJWACIjinVw=")

    def __init__(self, password):
        super(Password, self).__init__()
        if not isinstance(password, str):
            raise Exception("Password must be string")
        self._encrypted = self.encrypt(password)

    def verify(self, password):
        if isinstance(password, bytes):
            return self.decrypted == self.__crypto.decrypt(password).decode()
        else:
            return self.decrypted == password

    @classmethod
    def encrypt(cls, password: str):
        return cls.__crypto.encrypt(password.encode())

    @classmethod
    def decrypt(cls, encrypted, auth):
        if not isinstance(auth, Auth):
            raise Exception("Auth is required")
        if not auth.role.has("super_admin"):
            raise Exception("Not authorised to decrypt password")
        else:
            return cls.__crypto.decrypt(encrypted).decode()

    @property
    def encrypted(self):
        return self._encrypted

    @property
    def decrypted(self):
        return self.__crypto.decrypt(self._encrypted).decode()


class User(object):

    def __init__(self, name):
        super(User, self).__init__( )
        path = os.path.join(GlobalConfig.users_dir, name)
        self._path = path
        self._name = name
        self._thumbnail = None
        self._info, self._info_path = utility.read_info_yaml(path)
        role = self.get_info("role")
        self._role = Role(role) if role else None
        self._password = self.get_info("password")

    def create(self, auth, full_name, role, password, position=None, **kwargs):
        if self.exists():
            raise Exception("User already exists")

        self.__is_auth_user_admin(auth)

        if not os.path.exists(self._path):
            os.makedirs(self._path)

        role = role if role else "user"

        self._create_info_file(
            password=Password.encrypt(password),
            full_name=full_name.title(),
            role=role,
            position=position,
            created_by=auth.user.name,
            **kwargs
        )

    def _create_info_file(self, **kwargs):
        info = dict()
        info["name"] = self._name
        info["path"] = self._path
        info["info_file"] = self._info_path
        info["class"] = self.__class__.__name__
        info["created_at"] = datetime.datetime.now()

        info.update(kwargs)

        self._info.update(info)

        with open(self._info_path, "w") as info_file:
            yaml.dump(self._info, info_file)

    def exists(self):
        return os.path.exists(self._info_path)

    def get_info(self, attr):
        return self._info.get(attr, None)

    def set_role(self, role: Role, auth):
        self.__is_auth_user_admin(auth)
        self.update_info(role=role.name)

    def update_info(self, **kwargs):
        if not os.path.exists(self._info_path):
            self._create_info_file(**kwargs)
        else:
            self._info.update(kwargs)
            with open(self._info_path, "w") as info_file:
                yaml.dump(self._info, info_file)

    def __eq__(self, other):
        if isinstance(other, User):
            return other.name == self.name
        else:
            return other == self.name

    @staticmethod
    def __is_auth_user_admin(auth):

        if not isinstance(auth, Auth):
            raise Exception("User authorisation is require")

        if not auth or not auth.role.has("user_admin"):
            raise Exception("Not authorised to create")

        return True

    @property
    def thumbnail(self):
        if not self._thumbnail:
            path = os.path.join(self._path, ".thumbnail")
            if os.path.exists(path) and os.listdir(path):
                file_name = next(iter([f for f in os.listdir(path) if f.endswith(".png")]), "{}.png".format(self._name))
            else:
                file_name = "{}.png".format(self._name)
            self._thumbnail = os.path.join(path, file_name)

        return self._thumbnail

    @property
    def name(self):
        return self._name

    @property
    def position(self):
        return self.get_info("position")

    @property
    def full_name(self):
        return self.get_info("full_name")

    @property
    def password(self):
        return self._password

    @property
    def role(self):
        return self._role

    @property
    def info(self):
        return self._info


class Auth(object):
    __instance = None
    __on_auth = []
    __on_un_auth = []

    def __init__(self, user, password):
        super(Auth, self).__init__()
        self.__is_auth = None

        if self.__class__.__instance is None:
            self.__user = User(user)
            self.__password = Password(password)
            self.__class__.__instance = self

        elif user != self.__class__.__instance.user.name:
            raise Exception("Different user is authorized already")

    def un_authorise(self):
        self.__user = None
        self.__password = None
        self.__class__.__instance = None
        self.__is_auth = None

        for func in self.__on_un_auth:
            func()

    def __bool__(self):
        if self.__instance is not None:
            if self.__is_auth is None:
                return self.authorise()
            else:
                return self.__is_auth if self.__is_auth else False
        return False

    def authorise(self):
        if not any((self.__user, self.__password, self.__user and self.user.exists())):
            return False

        result = self.__password.verify(self.__user.password)
        if result:
            self.__is_auth = True
            for func in self.__on_auth:
                func()
        return result

    @property
    def user(self):
        return self.__user

    @property
    def role(self):
        return self.__user.role

    @classmethod
    def add_callback(cls, call_type, func):
        """Add call back on auth or on unauth
        args:
            call_type: on_auth | on_un_auth
            func: callable function
        """
        if not callable(func):
            return False
        if call_type == "on_auth":
            if func not in cls.__on_auth:
                cls.__on_auth.append(func)
        elif call_type == "on_un_auth":
            if func not in cls.__on_un_auth:
                cls.__on_un_auth.append(func)

    @classmethod
    def remove_callback(cls, call_type, func):
        """Remove call back on auth or on unauth
            args:
                call_type: on_auth | on_un_auth
                func: callable function
        """
        if not callable(func):
            return False
        if call_type == "on_auth":
            if func in cls.__on_auth:
                cls.__on_auth.remove(func)
        elif call_type == "on_un_auth":
            if func in cls.__on_un_auth:
                cls.__on_un_auth.remove(func)

    @classmethod
    def get_user(cls):
        return cls.__instance.user if cls.__instance else None

    @classmethod
    def get_auth(cls):
        return cls.__instance or None


def current_user():
    """ Returns current user"""
    return Auth.get_user()


def current_auth():
    """return current auth"""
    return Auth.get_auth()


def get_all_users(filters=None):
    """returns all users
    :arg
        filter(dict|callable): dict of props to filter. or callable filter method.
    """
    path = os.path.normpath(GlobalConfig.users_dir)
    for d in [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]:
        user = User(d)

        if isinstance(filters, dict):
            if all([user.get_info(k) == v for k, v in filters.items()]):
                yield user
        elif callable(filters):
            if filters(user):
                yield user
        else:
            yield user


