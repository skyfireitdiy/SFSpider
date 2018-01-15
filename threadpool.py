# coding=utf-8

import threading
import queue


class ThreadPool:
    """
    线程池类
    """

    class __RunTaskThread(threading.Thread):
        """
        线程池的任务执行类
        """

        def __init__(self, outter):
            threading.Thread.__init__(self)
            self.__outter = outter

        def run(self):
            """
            线程实现
            不断从任务列表中取出任务执行，并检测是否应该退出
            """
            while True:
                if self.__outter.exit_flag:
                    break
                if self.__outter.exit_when_no_task_flag:
                    if self.__outter.task_list.empty():
                        break
                if self.__outter.task_list.empty():
                    self.__outter.condition.acquire()
                    self.__outter.condition.wait()
                    self.__outter.condition.release()
                else:
                    try:
                        task = self.__outter.task_list.get(False)
                        if len(task) != 0:
                            task[0](*task[1:])
                        self.__outter.task_list.task_done()
                    except Exception as e:
                        print(e)
                        continue

    def __init__(self):
        self.task_list = queue.Queue()
        self.condition = threading.Condition()
        self.__thread_count = 1
        self.__started = False
        self.exit_flag = False
        self.exit_when_no_task_flag = False
        self.__thread_list = list()

    def set_work_thread_count(self, count):
        """
        设置线程数量（1~64）
        Args:
            count:线程数量
        此方法必须在start前调用，否则不会生效
        """
        if self.__started:
            print("Thread pool has started, can't change thread count")
            return
        if count <= 0:
            print("Thread count out of range (1~64) , set thread count to 1")
            count = 1
        elif count > 64:
            print("Thread count out of range (1~64) , set thread count to 64")
            count = 64
        self.__thread_count = count

    def __notify_all_thread(self):
        """
        唤醒所有在等待任务的线程，开始调度
        """
        self.condition.acquire()
        self.condition.notify_all()
        self.condition.release()

    def add_task(self, *task):
        """
        往线程池增加一个任务
        Args:
            task: 函数和对应的参数
        调用方法示例：
        def func(a, b):
            print(a+b)

        pool.add_task(func, 10, 5)
        """
        self.task_list.put(task)
        self.__notify_all_thread()

    def exit_when_no_task(self, flag=True):
        """
        设置没有任务时退出的标志
        Args:
            flag: 标志值
        """
        self.exit_when_no_task_flag = flag
        self.__notify_all_thread()

    def exit(self):
        """
        退出所有线程
        """
        self.exit_flag = True
        self.__notify_all_thread()

    def wait_exit(self, timeout=None):
        """
        等待所有线程退出，在此函数调用前应该先调用exit或者设置没有任务时退出的标志（exit_when_no_task）
        Args:
            timeout:每个线程等待的时间，如果为None说明为一直等待
        """
        for th in self.__thread_list:
            th.join(timeout)
        self.__started = False

    def start(self):
        """
        启动线程池，开始调度
        """
        for i in range(self.__thread_count):
            task_thread = self.__RunTaskThread(self)
            task_thread.setDaemon(True)
            task_thread.start()
            self.__thread_list.append(task_thread)
        self.__notify_all_thread()
        self.__started = True
