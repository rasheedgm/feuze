import os
import shutil
import sys
import subprocess
import logging
import ctypes
import yaml

from functools import partial
from threading import Thread, Lock
from queue import Queue

from feuze.core import constant


def get_os():
    """Linux 'linux'  Windows 'win32' Windows / Cygwin 'cygwin'  Mac OS X 'darwin'
    """
    _os_map = {
        "linux": "linux",
        "win32": "windows",
        "cygwin": "windows",
        "darwin": "mac"
    }
    return _os_map.get(sys.platform)


def get_user_config_dir():
    current_os = get_os()
    name = constant.APP_NAME.title()
    if current_os == "windows":
        return os.path.join(
            os.environ["userprofile"],
            "Documents", name,
        )
    elif current_os == "linux":
        return os.path.join(os.environ["HOME"], name)
    elif current_os == "mac":
        return os.path.join(
            os.environ["HOME"], "Library", "Preferences", name
        )


def get_logger():
    format_str = "[%(asctime)s][%(levelname)s]\t| %(name)s :  %(message)s"
    log_path = get_user_config_dir()
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    logging.basicConfig(
        filename=os.path.join(log_path, "logs.log"),
        filemode="w",
        level=logging.DEBUG,
        format=format_str
    )
    _logger = logging.getLogger(constant.APP_NAME.title())
    _logger.addHandler(logging.StreamHandler())
    for handler in _logger.handlers:
        handler.setFormatter(logging.Formatter(format_str))
    return _logger


# Logger
logger = get_logger()


def _execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def find_available_location(central_path, local_path):
    central = os.path.exists(central_path)
    local = os.path.exists(local_path)
    if all((central, local)):
        return constant.Location.BOTH
    elif central:
        return constant.Location.CENTRAL
    elif local:
        return constant.Location.LOCAL
    else:
        return constant.Location.NONE


def create_symlink(src, dest):
    if os.path.exists(dest):
        if not os.listdir(dest):
            os.rmdir(dest)
        else:
            raise Exception("Destination folder has files in it")
    _current_os = get_os()
    # for windows create jump
    if _current_os == "windows":
        subprocess.check_call("mklink /j {} {}".format(dest, src), shell=True)
    elif _current_os == "linux":
        os.symlink(src, dest, target_is_directory=True)
    # TODO test for linux and mac


def is_sym_link(path):
    if get_os() == "windows":
        file_attribute_reparse_point = 0x0400
        return bool(os.path.isdir(path) and (ctypes.windll.kernel32.GetFileAttributesW(path) & file_attribute_reparse_point))
    else:
        return os.path.islink(path)
    # TODO test it in in linux and mac


def get_args_count(func):
    if isinstance(func, partial):
        return func.func.__code__.co_argcount - (len(func.args) + len(func.keywords))
    else:
        return func.__code__.co_argcount


def get_user_config_file():
    name = constant.APP_NAME.title()
    return os.path.join(
        get_user_config_dir(),
        "{}.yml".format(name)
    )


def read_info_yaml(path):
    _info = {}
    info_file = os.path.join(path, "info.yaml")
    if os.path.exists(info_file):
        with open(info_file, "r") as file:
            try:
                _info = yaml.safe_load(file)
            except yaml.YAMLError as e:
                logger.info("Error reding info file: {}\n{}".format(info_file, e))

    return _info, info_file


def write_info_yaml(file_path, data):
    temp_file_bak  = None
    if os.path.exists(file_path):
        temp_file_bak = os.path.join(os.path.dirname(file_path), ".info_bak.yaml")
        shutil.copy(file_path, temp_file_bak)
    try:
        with open(file_path, "w") as info_file:
            yaml.dump(data, info_file)
    except Exception as e:
        logger.error("Problem writing file {0}|{1}".format(file_path, e))
        if temp_file_bak:
            shutil.copy(temp_file_bak, file_path)
        raise e


class TaskThreader:
    __instance = None
    __task_queue = Queue()
    __total_tasks = 0
    __completed_count = 0
    __lock = Lock()
    __callbacks = {"__all": [lambda x, y, z: logger.info("{} : {}/{} finished".format(x, y, z))]}

    def __init__(self):
        if not self.__instance:
            self.__create_threads()
            __instance = self
            self._back_thread = None

    def __task_worker(self):
        while True:
            func, *args = self.__task_queue.get()
            try:
                func(*args,)
                name = func.__name__
            except Exception as e:
                logger.error("Failed to run - {} : {}".format(str(func), e))
                name = str(func)
                pass
            with self.__lock:
                self.__completed_count += 1
                # percent = (self.__completed_count * 100) / self.__total_tasks
                potential_args = [name, self.__completed_count, self.__total_tasks, tuple(args)]
                callbacks = self.__callbacks.get(name) + self.__callbacks.get("__all") \
                    if name in self.__callbacks.keys() else self.__callbacks.get("__all")
                for callback in callbacks:
                    try:
                        args_count = get_args_count(callback)
                        if args_count:
                            callback(*potential_args[:args_count])
                        else:
                            callback()
                    except Exception as e:
                        logger.error(e)

            self.__task_queue.task_done()

    def __create_threads(self):
        for i in range(constant.THREAD_COUNT):
            t = Thread(target=self.__task_worker)
            t.daemon = True
            t.start()

    @classmethod
    def add_callback(cls, call, work_name="__all"):
        if not callable(call):
            return None
        if work_name in cls.__callbacks.keys():
            cls.__callbacks[work_name].append(call)
        else:
            cls.__callbacks[work_name] = [call]

    @classmethod
    def remove_callback(cls, call, work_name="__all"):
        if callable(call):
            if call in cls.__callbacks.get(work_name, []):
                cls.__callbacks[work_name].remove(call)
                return True

        elif isinstance(call, str):
            for func in cls.__callbacks.get(work_name, []):
                if func.__name__ == call:
                    cls.__callbacks[work_name].remove(func)
                    return True
        else:
            raise Exception("Invalid call/callback name")

        return False

    @classmethod
    def add_to_queue(cls, tasks, wait=True):

        if isinstance(tasks, tuple):
            tasks = [tasks]
        elif not isinstance(tasks, list):
            return False

        if not cls.__instance:
            cls.__instance = cls()

        for task in tasks:
            with cls.__lock:
                cls.__task_queue.put(task, wait)
                cls.__total_tasks += 1

        if wait:
            cls.__task_queue.join()

