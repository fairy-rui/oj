#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'snow'

"""
Default configurations.
"""

configs = {
    'db': {
        'host': '192.168.0.110',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'online judge system',
    },
    'oj': {
        'count_thread': 1,   # 开启评测线程数目
        'queue_size': 4,    # 评测程序队列容量
        'work_dir': '../../work_dir',  # work评判目录
        'data_dir': '../../data_dir',  # data测试数据目录
        'auto_clean': False,  # 自动清理work目录
        'logfile_name': '../../log/judge.log',  # 输出日志文件
    },
    'result_code': {
        'AC': 0,  # Accepted
        'PE': 1,  # Presentation Error
        'TLE': 2,  # Time Limit Exceeded
        'MLE': 3,  # Memory Limit Exceeded
        'WA': 4,  # Wrong Answer
        'RE': 5,  # Runtime Error
        'OLE': 6,  # Output limit Exceeded
        'CE': 7,  # Compile Error
        'SE': 8,  # System Error
        'Waiting': 9,
        'Judging': 10,
    },
    'dc': {
        'rmq_host': 'localhost',    # rabbitmq服务器地址
        'rmq_port': 5672,   # rabbitmq服务器端口
        'virtual_host': '/',
        'rmq_user': 'guest',
        'rmq_password': 'guest',
        'task_queue': 'task_queue',  # 任务队列
        'result_queue': 'result_queue',  # 结果队列
    },
    'remote_server': {
        'host': '127.0.0.1',
        'port': 22,
        'user': 'snow',
        'password': 'root',
    },
}
