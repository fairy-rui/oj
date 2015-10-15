#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'snow'

import logging
import os
import sys
import subprocess
import shlex
import shutil
import functools
import lorun
import paramiko
from config import configs


class JudgeTask(object):

    def __init__(self, task):
        self.solution_id = task['solution_id']
        self.problem_id = task['problem_id']
        self.user_id = task['user_id']
        self.language = task['pro_lang']
        self.time_limit = task['time_limit']
        self.memory_limit = task['memory_limit']
        self.contest_id = task['contest_id']
        self.remote_data_dir = task['remote_data_dir']
        self.result = {
            'solution_id': self.solution_id,
            'problem_id': self.problem_id,
            'user_id': self.user_id,
            'contest_id': self.contest_id,
            'take_time': 0,
            'take_memory': 0,
            'result': 4,
            'compile_error': '',
        }

    def _get_submit_code(self):
        """
        到服务器下载提交代码
        :return:
        """
        full_path = os.path.join(os.getcwd(), configs.oj.work_dir, str(self.solution_id))

        if not os.path.exists(full_path):
            self._low_level()
            os.mkdir(full_path)
            self._download_file(full_path)

    def _get_data_count(self):
        """
        获取测试数据的个数
        :return:
        """
        full_path = os.path.join(os.getcwd(), configs.oj.data_dir, str(self.problem_id))

        if not os.path.exists(full_path):   # 若不存在数据文件,到服务器下载
            self._low_level()
            os.mkdir(full_path)
            self._download_file(full_path)

        try:
            files = os.listdir(full_path)
        except OSError as e:
            logging.error(e)
            return 0
        count = 0
        for item in files:
            if item.endswith(".in") and item.startswith("data"):
                count += 1
        self.data_count = count

    def _download_file(self, local_data_dir):
        self._low_level()
        try:
            t = paramiko.Transport((configs.remote_server.host, configs.remote_server.port))
            t.connect(username=configs.remote_server.user, password=configs.remote_server.password)
            sftp = paramiko.SFTPClient.from_transport(t)

            files = sftp.listdir(self.remote_data_dir)
            for f in files:
                sftp.get(os.path.join(self.remote_data_dir, f), os.path.join(local_data_dir, f))
        except Exception as e:
            logging.error(e)
        try:
            t.close()
        except:
            pass

    @staticmethod
    def _low_level():
        try:
            # 降低程序运行权限，防止恶意代码
            os.setuid(int(os.popen("id -u %s" % "nobody").read()))
        except:
            logging.error("please run this program as root!")
            sys.exit(-1)

    def _clean_work_dir(self):
        """
        清理work目录，删除临时文件
        :return:
        """
        dir_name = os.path.join(configs.oj.work_dir, str(self.solution_id))
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
        else:
            logging.error('the directory is not exist.')

    def _check_dangerous_code(self):
        if self.language in ['python2', 'python3']:
            code = file('%s/%s/main.py' % (configs.oj.work_dir, self.solution_id)).readlines()
            support_modules = [
                're',  # 正则表达式
                'sys',  # sys.stdin
                'string',  # 字符串处理
                'scanf',  # 格式化输入
                'math',  # 数学库
                'cmath',  # 复数数学库
                'decimal',  # 数学库，浮点数
                'numbers',  # 抽象基类
                'fractions',  # 有理数
                'random',  # 随机数
                'itertools',  # 迭代函数
                'functools',
                # Higher order functions and operations on callable objects
                'operator',  # 函数操作
                'readline',  # 读文件
                'json',  # 解析json
                'array',  # 数组
                'sets',  # 集合
                'queue',  # 队列
                'types',  # 判断类型
            ]
            for line in code:
                if line.find('import') >= 0:
                    words = line.split()
                    tag = 0
                    for w in words:
                        if w in support_modules:
                            tag = 1
                            break
                    if tag == 0:
                        return False
            return True
        if self.language in ['c', 'c++']:
            try:
                code = file('%s/%s/main.c' % (configs.oj.work_dir, self.solution_id)).read()
            except:
                code = file('%s/%s/main.cpp' % (configs.oj.work_dir, self.solution_id)).read()
            if code.find('system') >= 0:
                return False
            return True
    #    if language == 'java':
    #        code = file('/work/%s/Main.java'%solution_id).read()
    #        if code.find('Runtime.')>=0:
    #            return False
    #        return True
        if self.language == 'go':
            code = file('%s/%s/main.go' % (configs.oj.work_dir, self.solution_id)).read()
            danger_package = [
                'os', 'path', 'net', 'sql', 'syslog', 'http', 'mail', 'rpc', 'smtp', 'exec', 'user',
            ]
            for item in danger_package:
                if code.find('"%s"' % item) >= 0:
                    return False
            return True

    def _compile_code(self):
        """
        将程序编译成可执行文件
        :return:
        """
        self._low_level()
        language = self.language.lower()
        dir_work = os.path.join(configs.oj.work_dir, str(self.solution_id))
        build_cmd = {
            'c':
            'gcc main.c -o main -Wall -lm -O2 -std=c99 --static -DONLINE_JUDGE',
            'c++': 'g++ main.cpp -O2 -Wall -lm --static -DONLINE_JUDGE -o main',
            'java': 'javac Main.java',
            'ruby': 'reek main.rb',
            'perl': 'perl -c main.pl',
            'pascal': 'fpc main.pas -O2 -Co -Ct -Ci',
            'go': '/opt/golang/bin/go build -ldflags "-s -w"  main.go',
            'lua': 'luac -o main main.lua',
            'python2': 'python2 -m py_compile main.py',
            'python3': 'python3 -m py_compile main.py',
            'haskell': 'ghc -o main main.hs',
        }
        if language not in build_cmd.keys():
            return False
        p = subprocess.Popen(
            build_cmd[language],
            shell=True,
            cwd=dir_work,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = p.communicate()  # 获取编译错误信息
        err_txt_path = os.path.join(configs.oj.work_dir, str(self.solution_id), 'error.txt')
        f = file(err_txt_path, 'w')
        f.write(err)
        f.write(out)
        f.close()
        if p.returncode == 0:  # 返回值为0,编译成功
            return True
        self.result['compile_error'] = err + out  # 编译失败,更新题目的编译错误信息
        return False

    def _judge_one_mem_time(self, data_num):
        """
        评测一组数据
        :param data_num:
        :return:
        """
        self._low_level()
        input_path = os.path.join(
            configs.oj.data_dir, str(self.problem_id), 'data%s.in' %
            data_num)
        try:
            input_data = file(input_path)
        except Exception as e:
            logging.error(e)
            return False
        output_path = os.path.join(
            configs.oj.work_dir, str(self.solution_id), 'out%s.txt' %
            data_num)
        temp_out_data = file(output_path, 'w')
        if self.language == 'java':
            cmd = 'java -cp %s Main' % (
                os.path.join(configs.oj.work_dir,
                             str(self.solution_id)))
            main_exe = shlex.split(cmd)
        elif self.language == 'python2':
            cmd = 'python2 %s' % (
                os.path.join(configs.oj.work_dir,
                             str(self.solution_id),
                             'main.pyc'))
            main_exe = shlex.split(cmd)
        elif self.language == 'python3':
            cmd = 'python3 %s' % (
                os.path.join(configs.oj.work_dir,
                             str(self.solution_id),
                             '__pycache__/main.cpython-33.pyc'))
            main_exe = shlex.split(cmd)
        elif self.language == 'lua':
            cmd = "lua %s" % (
                os.path.join(configs.oj.work_dir,
                             str(self.solution_id),
                             "main"))
            main_exe = shlex.split(cmd)
        elif self.language == "ruby":
            cmd = "ruby %s" % (
                os.path.join(configs.oj.work_dir,
                             str(self.solution_id),
                             "main.rb"))
            main_exe = shlex.split(cmd)
        elif self.language == "perl":
            cmd = "perl %s" % (
                os.path.join(configs.oj.work_dir,
                             str(self.solution_id),
                             "main.pl"))
            main_exe = shlex.split(cmd)
        else:
            main_exe = [os.path.join(configs.oj.work_dir, str(self.solution_id), 'main'), ]
        runcfg = {
            'args': main_exe,
            'fd_in': input_data.fileno(),
            'fd_out': temp_out_data.fileno(),
            'timelimit': self.time_limit,  # in MS
            'memorylimit': self.memory_limit,  # in KB

            #'trace': True,
            #'calls': [3, 4, 5, 6, 11, 33, 45, 85, 91, 122, 125, 162, 174, 175, 192, 197, 243, 252, ],    # system calls that could be used by testing programs
            #'files': {'/etc/ld.so.nohwcap': 0},
        }

        self._low_level()
        rst = lorun.run(runcfg)
        input_data.close()
        temp_out_data.close()
        logging.debug(rst)
        '''
        if rst['result'] == 0:
            correct_result = os.path.join(
                configs.oj.data_dir, str(self.problem_id), 'data%s.out' %
                data_num)
            corr_out_data = file(correct_result, 'r')
            temp_out_data = file(output_path, 'r')
            rst['result'] = lorun.check(corr_out_data.fileno(), temp_out_data.fileno())
        logging.info(rst)
        '''
        return rst

    def _judge_result(self, data_num):
        """
        对输出数据进行评测
        :param data_num:
        :return:
        """
        self._low_level()
        logging.debug("Judging result")
        correct_result = os.path.join(
            configs.oj.data_dir, str(self.problem_id), 'data%s.out' %
            data_num)
        user_result = os.path.join(
            configs.oj.work_dir, str(self.solution_id), 'out%s.txt' %
            data_num)

        if os.path.getsize(user_result) > 1024 * 1024:
            return 'OLE'
        try:
            corr = file(correct_result).read()
            user = file(user_result).read()
        except:
            return False
        if corr == user:  # 完全相同:AC
            return 'AC'
        corr = corr.replace('\r', '').rstrip()  # 删除\r,删除行末的空格和换行
        user = user.replace('\r', '').rstrip()
        if corr.split() == user.split():  # 除去空格,tab,换行相同:PE
            return 'PE'
        return 'WA'  # 其他WA

    def _judge(self):
        self._low_level()
        max_mem = 0
        max_time = 0
        if self.language in ["java", 'python2', 'python3', 'ruby', 'perl']:
            self.time_limit *= 2
            self.memory_limit *= 2

        for i in range(self.data_count):
            ret = self._judge_one_mem_time(i)
            if ret is False:
                continue
            if ret['result'] == 5:
                self.result['result'] = configs.result_code.RE
                return
            elif ret['result'] == 6:
                self.result['result'] = configs.result_code.OLE
                return
            elif ret['result'] == 2:
                self.result['result'] = configs.result_code.TLE
                self.result['take_time'] = self.time_limit
                return
            elif ret['result'] == 3:
                self.result['result'] = configs.result_code.MLE
                self.result['take_memory'] = self.memory_limit
                return
            if max_time < ret["timeused"]:
                max_time = ret['timeused']
            if max_mem < ret['memoryused']:
                max_mem = ret['memoryused']
            '''
            if ret['result'] == 4:
                self.result['result'] = configs.result_code.WA
                break
            elif ret['result'] == 1:
                self.result['result'] = configs.result_code.PE
            elif ret['result'] == 0:
                if self.result['result'] != configs.result_code.PE:
                    self.result['result'] = configs.result_code.AC
            else:
                logging.error("judge did not get result")
            '''
            result = self._judge_result(i)
            if result is False:
                continue
            if result == 'WA':
                self.result['result'] = configs.result_code[result]
                break
            elif result == 'OLE':
                self.result['result'] = configs.result_code[result]
                break
            elif result == 'PE':
                self.result['result'] = configs.result_code[result]
            elif result == 'AC':
                if self.result['result'] != 'PE':
                    self.result['result'] = configs.result_code[result]
            else:
                logging.error("judge did not get result")
            
        self.result['take_time'] = max_time
        self.result['take_memory'] = max_mem
        return

    def _run(self):
        """
        评判程序
        :return:
        """
        self._low_level()
        if self._check_dangerous_code() is False:
            self.result['result'] = configs.result_code.RE
            return
        if self._compile_code() is False:   # 编译错误
            self.result['result'] = configs.result_code.CE
            return
        if self.data_count == 0:  # 没有测试数据
            self.result['result'] = configs.result_code.SE
            return
        self._judge()
        logging.debug(self.result)
        return

    def go(self):
        self._get_submit_code()  # 获取提交代码
        self._get_data_count()  # 获取测试数据的个数

        logging.info('judging %s' % self.solution_id)

        self._run()  # 评判
        logging.info('%s result %s' % (self.result['solution_id'], self.result['result']))

        if configs.oj.auto_clean:  # 清理work目录
            self._clean_work_dir()

        return self.result
