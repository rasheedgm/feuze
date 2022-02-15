import inspect
import os
import subprocess
from functools import partial
from threading import Thread, Lock
from queue import Queue
import logging
import ctypes
import sys

from src.core.constant import THREAD_COUNT, APP_NAME, Location

logging.basicConfig()
logger = logging.getLogger("Frolic")
logger.setLevel(logging.INFO)


def _execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


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


def find_available_location(central_path, local_path):
    print(central_path, local_path)
    central = os.path.exists(central_path)
    local = os.path.exists(local_path)
    if all((central, local)):
        return Location.BOTH
    elif central:
        return Location.CENTRAL
    elif local:
        return Location.LOCAL
    else:
        return Location.NONE


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
    current_os = get_os()
    name = APP_NAME.title()
    if current_os == "windows":
        return os.path.join(
            os.environ["userprofile"],
            "Documents", name,
            "{}.yml".format(name)
        )
    elif current_os == "linux":
        return os.path.join(os.environ["HOME"], name, "{}.yml".format(name))
    elif current_os == "mac":
        return os.path.join(
            os.environ["HOME"], "Library", "Preferences", name, "{}.yml".format(name)
        )


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
        for i in range(THREAD_COUNT):
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

