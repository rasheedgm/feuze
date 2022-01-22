import os
import subprocess
from threading import Thread, Lock
from queue import Queue
import logging
import ctypes
import sys

from constant import THREAD_COUNT


_log = logging.getLogger("Fold")


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


class TaskThreader:
    __instance = None
    __file_queue = Queue()
    __total_tasks = 0
    __completed_count = 0
    __lock = Lock()

    def __init__(self):
        if not self.__instance:
            self.__create_threads()
            __instance = self

    def __task_worker(self):
        while True:
            func, *args = self.__file_queue.get()
            try:
                func(*args,)
            except Exception as e:
                _log.error("Failed to run - {} : {}".format(str(func), e))
                pass
            with self.__lock:
                self.__completed_count += 1
                percent = (self.__completed_count * 100) / self.__total_tasks
                print("{} percent finished. {}/{}".format(percent, self.__completed_count, self.__total_tasks))
            self.__file_queue.task_done()

    def __create_threads(self):
        for i in range(THREAD_COUNT):
            t = Thread(target=self.__task_worker)
            t.daemon = True
            t.start()

    @classmethod
    def add_to_queue(cls, tasks):

        if isinstance(tasks, tuple):
            tasks = [tasks]
        elif not isinstance(tasks, list):
            return False

        if not cls.__instance:
            cls.__instance = cls()

        for task in tasks:
            with cls.__lock:
                cls.__file_queue.put(task)
                cls.__total_tasks += 1
        cls.__file_queue.join()

