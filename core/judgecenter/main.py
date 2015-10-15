#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'snow'

import logging
import sys
from config import configs
from service import JudgeCenter
from daemon import Daemon


class TaskDaemon(Daemon):
    def _run(self):
        srv = JudgeCenter()
        srv.run()

'''
def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)-18s[line:%(lineno)3d] %(levelname)-6s %(message)s',
                        filename=configs.oj.logfile_name,
                        filemode='a')
    srv = JudgeCenter()
    srv.run()
'''

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)-18s[line:%(lineno)3d] %(levelname)-6s %(message)s',
                        filename=configs.oj.logfile_name,
                        filemode='a')

    task = TaskDaemon('/tmp/daemon-task.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            task.start()
        elif 'stop' == sys.argv[1]:
            task.stop()
        elif 'restart' == sys.argv[1]:
            task.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)