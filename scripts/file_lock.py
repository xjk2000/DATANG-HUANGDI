#!/usr/bin/env python3
"""
文件锁 · 防多 Agent 并发写入

使用 fcntl 文件锁实现跨进程互斥访问。
支持超时机制，避免死锁。
"""

import fcntl
import os
import time
import contextlib


class FileLockTimeout(Exception):
    """文件锁获取超时"""
    pass


class FileLock:
    """基于 fcntl 的文件锁"""

    def __init__(self, lock_path, timeout=10):
        """
        :param lock_path: 锁文件路径
        :param timeout: 获取锁的超时时间（秒），0 表示不等待
        """
        self.lock_path = lock_path
        self.timeout = timeout
        self._fd = None

    def acquire(self):
        """获取文件锁"""
        os.makedirs(os.path.dirname(self.lock_path) or '.', exist_ok=True)
        self._fd = open(self.lock_path, 'w')

        if self.timeout <= 0:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (IOError, OSError):
                self._fd.close()
                self._fd = None
                raise FileLockTimeout(f"无法立即获取锁: {self.lock_path}")
            return

        deadline = time.monotonic() + self.timeout
        interval = 0.05
        while True:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except (IOError, OSError):
                if time.monotonic() >= deadline:
                    self._fd.close()
                    self._fd = None
                    raise FileLockTimeout(
                        f"获取锁超时 ({self.timeout}s): {self.lock_path}"
                    )
                time.sleep(interval)
                interval = min(interval * 1.5, 0.5)

    def release(self):
        """释放文件锁"""
        if self._fd is not None:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            finally:
                self._fd.close()
                self._fd = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


@contextlib.contextmanager
def locked_json_rw(json_path, lock_dir=None, timeout=10):
    """
    上下文管理器：加锁读写 JSON 文件。

    用法：
        with locked_json_rw('data/tasks.json') as (data, save):
            data.append(new_task)
            save(data)
    """
    import json

    if lock_dir is None:
        lock_dir = os.path.dirname(json_path) or '.'
    lock_path = os.path.join(lock_dir, '.lock_' + os.path.basename(json_path))

    with FileLock(lock_path, timeout=timeout):
        # 读取
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []

        saved = [False]

        def save(new_data):
            tmp_path = json_path + f'.tmp-{os.getpid()}-{int(time.time())}'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, json_path)
            saved[0] = True

        yield data, save

        if not saved[0]:
            pass  # 未调用 save，不写入
