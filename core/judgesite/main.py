#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'snow'

import logging
import sys
import threading

from config import configs
from service import JudgeSite
from daemon import Daemon


class JudgeDaemon(Daemon):
    def _run(self):
        #srv = JudgeSite()
        #srv.run()

        for count in xrange(configs.oj.count_thread):
            t = threading.Thread(target=lambda: JudgeSite().run(), name='publish_task%s' % count)
            t.daemon = True
            t.start()
        t.join()


'''
def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)-18s[line:%(lineno)3d] %(levelname)-6s %(message)s',
                        filename=configs.oj.logfile_name,
                        filemode='a')
    srv = JudgeSite()
    srv.run()
'''

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)-18s[line:%(lineno)3d] %(levelname)-6s %(message)s',
                        filename=configs.oj.logfile_name,
                        filemode='a')

    judge = JudgeDaemon('/tmp/daemon-judge.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            judge.start()
        elif 'stop' == sys.argv[1]:
            judge.stop()
        elif 'restart' == sys.argv[1]:
            judge.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
