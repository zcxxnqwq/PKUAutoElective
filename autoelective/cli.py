#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: cli.py
# modified: 2020-02-20

from optparse import OptionParser #命令行参数解析模块
from threading import Thread #多线程
from multiprocessing import Queue #在进程间传递数据
from . import __version__, __date__


def create_default_parser(): #解析命令行参数

    parser = OptionParser(
        description='PKU Auto-Elective Tool v%s (%s)' % (__version__, __date__),
        version=__version__,
    )

    ## custom input files

    parser.add_option( #指定配置文件
        '-c',
        '--config',
        dest='config_ini', #把用户传入参数存储到config.ini
        metavar="FILE", #显示帮助信息占位字符为 FILE
        help='custom config file encoded with utf8',
    )

    ## boolean (flag) options

    parser.add_option( # 是否启用运行监控线程
        '-m',
        '--with-monitor',
        dest='with_monitor',
        action='store_true', #用户提供指定命令行则 with_monitor=True，否则 False
        default=False,
        help='run the monitor thread simultaneously',
    )

    return parser


def setup_default_environ(options, args, environ): #根据命令行参数设置环境变量

    environ.config_ini = options.config_ini
    environ.with_monitor = options.with_monitor


def create_default_threads(options, args, environ): #创建并返回一个包含多个线程的列表

    # import here to ensure the singleton `config` will be init later than parse_args()
    from autoelective.loop import run_iaaa_loop, run_elective_loop
    from autoelective.monitor import run_monitor

    tList = []

    t = Thread(target=run_iaaa_loop, name="IAAA") #target为线程中调用的函数
    environ.iaaa_loop_thread = t
    tList.append(t)

    t = Thread(target=run_elective_loop, name="Elective")
    environ.elective_loop_thread = t
    tList.append(t)

    if options.with_monitor:
        t = Thread(target=run_monitor, name="Monitor")
        environ.monitor_thread = t
        tList.append(t)

    return tList


def run():

    from .environ import Environ

    environ = Environ()

    parser = create_default_parser()
    options, args = parser.parse_args() #我定义的参数 未被解析的参数

    setup_default_environ(options, args, environ)

    tList = create_default_threads(options, args, environ)

    for t in tList:
        t.daemon = True #守护线程，在主程序结束时会自动退出
        t.start()

    #
    # Don't use join() to block the main thread, or Ctrl + C in Windows can't work.
    #
    # for t in tList:
    #     t.join()
    #
    try:
        Queue().get()
    except KeyboardInterrupt as e:
        pass
