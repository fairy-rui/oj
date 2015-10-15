#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'snow'

import time
import logging
import os
import shutil
import codecs
import sys
import db
from datetime import datetime
from config import configs


class PutTask(object):

    def __init__(self):
        db.create_engine(user=configs.db.user, password=configs.db.password, database=configs.db.database,
                         host=configs.db.host, port=configs.db.port)
    #    self.task = task
    #    self.result = result

    @staticmethod
    def _low_level():
        try:
            # 降低程序运行权限，防止恶意代码
            os.setuid(int(os.popen("id -u %s" % "nobody").read()))
        except:
            logging.error("please run this program as root!")
            sys.exit(-1)

    @staticmethod
    def _clean_work_dir(solution_id):
        """
        清理work目录，删除临时文件
        :param solution_id:
        :return:
        """
        dir_name = os.path.join(configs.oj.work_dir, str(solution_id))
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
        else:
            logging.info('the directory is not exist.')

    @staticmethod
    def _get_code(solution_id, pro_lang):
        """
        从数据库获取代码并写入work目录下对应的文件
        :param solution_id:
        :return:
        """
        file_name = {
            'c': 'main.c',
            'c++': 'main.cpp',
            'java': 'Main.java',
            'ruby': 'main.rb',
            'perl': 'main.pl',
            'pascal': 'main.pas',
            'go': 'main.go',
            'lua': 'main.lua',
            'python2': 'main.py',
            'python3': 'main.py',
            'haskell': 'main.hs'
        }
        code = db.select_one('select source from t_submission where submission_id=?', solution_id).get('source')
        if code is None:
            logging.error('cannot get code of runid %s' % solution_id)
            return False
        try:
            work_path = os.path.join(configs.oj.work_dir, str(solution_id))
            PutTask._low_level()
            os.mkdir(work_path)
        except OSError as e:
            if str(e).find('exist') > 0:    # 文件夹已经存在
                pass
            else:
                logging.error(e)
                return False
        try:
            real_path = os.path.join(configs.oj.work_dir, str(solution_id), file_name[pro_lang])
        except KeyError as e:
            logging.error(e)
            return False
        try:
            PutTask._low_level()
            f = codecs.open(real_path, 'w')
            try:
                f.write(code)
            except:
                logging.error('%s not write code to file' % solution_id)
                return False
            finally:
                f.close()
        except OSError as e:
            logging.error(e)
            return False
        size = os.path.getsize(real_path)
        db.update('update t_submission set code_length=? where submission_id=?', size, solution_id)
        return True
    '''
    def put_task_into_queue(self):
        """
        循环扫描数据库,将任务添加到队列
        :return:
        """
        while True:
            # 判断队列中任务数量,以此决定是否阻塞线程
            if self.task.qsize() >= configs.oj.queue_size:
                self.task.join()    # 阻塞程序,直到队列里面的任务全部完成
            data = db.select('select submission_id, problem_id, username, contest_id, language from t_submission where result=?',
                             configs.result_code.Waiting)
            time.sleep(0.2)  # 延时0.2秒,防止因速度太快不能获取代码
            for s in data:
                logging.debug(s)
                solution_id = s.get('submission_id')
                problem_id = s.get('problem_id')
                user_id = s.get('username')
                contest_id = s.get('contest_id')
                pro_lang = s.get('language')

                ret = self._get_code(solution_id, pro_lang)
                if ret is False:
                    # 防止因速度太快不能获取代码
                    time.sleep(0.5)
                    ret = self._get_code(solution_id, pro_lang)
                if ret is False:
                    db.update('update t_submission set result=? where submission_id=?', configs.result_code.SE, solution_id)
                    self._clean_work_dir(solution_id)
                    continue
                limit = db.select_one('select time_limit, memory_limit from t_problem where problem_id=?', problem_id)
                time_limit = limit.get('time_limit')
                memory_limit = limit.get('memory_limit')
                task = {
                    'solution_id': solution_id,
                    'problem_id': problem_id,
                    'contest_id': contest_id,
                    'user_id': user_id,
                    'pro_lang': pro_lang,
                    'time_limit': time_limit,
                    'memory_limit': memory_limit,
                }
                logging.debug(task)
                self.task.put(task)
                db.update('update t_submission set result=? where submission_id=?', configs.result_code.Judging, solution_id)
            time.sleep(0.5)
    '''
    @staticmethod
    def get_task():
        data = db.select('select submission_id, problem_id, username, contest_id, language from t_submission '
                         'where result=?', configs.result_code.Waiting)
        l_task = []
        for s in data:
            logging.debug(s)
            solution_id = s.get('submission_id')
            problem_id = s.get('problem_id')
            user_id = s.get('username')
            contest_id = s.get('contest_id')
            pro_lang = s.get('language')

            ret = PutTask._get_code(solution_id, pro_lang)
            if ret is False:
                # 防止因速度太快不能获取代码
                time.sleep(0.5)
                ret = PutTask._get_code(solution_id, pro_lang)
            if ret is False:
                db.update('update t_submission set result=? where submission_id=?', configs.result_code.SE, solution_id)
                PutTask._clean_work_dir(solution_id)
                continue
            limit = db.select_one('select time_limit, memory_limit from t_problem where problem_id=?', problem_id)
            time_limit = limit.get('time_limit')
            memory_limit = limit.get('memory_limit')
            remote_data_dir = os.path.join(os.getcwd(), configs.oj.work_dir, str(solution_id))    # 获得服务器端数据文件目录
            task = {
                'solution_id': solution_id,
                'problem_id': problem_id,
                'contest_id': contest_id,
                'user_id': user_id,
                'pro_lang': pro_lang,
                'time_limit': time_limit,
                'memory_limit': memory_limit,
                'remote_data_dir': remote_data_dir,
            }
            logging.debug(task)
            l_task.append(task)
            db.update('update t_submission set result=? where submission_id=?', configs.result_code.Judging, solution_id)
        return l_task
    '''
    def update_result(self):
        """
        将评判结果写入数据库
        :return:
        """
        while True:
            if self.result.empty():  # 队列为空，空闲
                logging.info('%s idle' % (current_process().name,))
            result = self.result.get()  # 获取结果，如果队列为空则阻塞
            logging.info('%s result %s' % (result['solution_id'], result['result']))
            db.update('update t_submission set memory_used=?, time_used=?, result=? where submission_id=?',
                    result['take_memory'], result['take_time'], result['result'], result['solution_id'])  # 将结果写入数据库

            self.result.task_done()
    '''
    @staticmethod
    def update_result(result):
        """
        将评判结果写入数据库
        :param result:
        :return:
        """
        logging.info('%s result %s' % (result['solution_id'], result['result']))
        db.update('update t_submission set memory_used=?, time_used=?, result=? , error=? where submission_id=?',
                  result['take_memory'], result['take_time'], result['result'], result['compile_error'],
                  result['solution_id'])  # 将结果写入数据库

        if configs.oj.auto_clean:  # 清理work目录
            PutTask._clean_work_dir(result['solution_id'])

    @staticmethod
    def _create_ranking_table(result):
        """
        创建比赛排名表及触发器
        db.update('drop table if exists t_?', result['contest_id'])
        :return:
        """
        sql_trigger1 = ["create trigger calculate_submission after insert on t_submission for each row "
                        "begin update t_problem set submit = submit + 1 where problem_id = new.problem_id; "
                        "update t_user set submit = submit + 1 where username = new.username; "
                        "if new.contest_id is not null then update t_contest_problem set submit = submit + 1 "
                        "where contest_id = new.contest_id and problem_id = new.problem_id; end if; end;"]
        sql_trigger2 = ["create trigger calculate_AC before update on t_submission for each row begin "
                        "declare num int; if new.result = ? then "
                        "set num = (select count(*) from t_submission where problem_id = new.problem_id and "
                        "username = new.username and result = ?); if num = 0 then "
                        "update t_problem set solved = solved + 1 where problem_id = new.problem_id; "
                        "update t_user set solved = solved + 1 where username = new.username;"
                        "end if; if new.contest_id is not null then "
                        "set num = (select count(*) from t_submission where problem_id = new.problem_id "
                        "and username = new.username and contest_id = new.contest_id and result = ?); "
                        "if num = 0 then "
                        "update t_contest_problem set solved = solved + 1 where contest_id = new.contest_id "
                        "and problem_id = new.problem_id; end if; end if; end if; end;"]
        sql_trigger3 = ["create trigger calculate_penalty_time before update on t_ranking for each row "
                        "begin set new.penalty = new.AC_time + (new.AC_time xor 0) * new.wrong_submit * 20;end;"]

        db.update('drop table if exists t_?', result['contest_id'])
        sql_table = ["create table if not exists t_? (ranking_id int(11) unsigned primary key auto_increment, "
                     "username char(30), solved int(11) default '0', total_time float unsigned default '0',"]
        sql_trigger = ["create trigger calculate_penalty before update on t_? for each row "
                       "begin declare total float; set total = "]
        l_problem = db.select('select problem_id from t_contest_problem where contest_id=?', result['contest_id'])
        table_param = [result['contest_id']]
        trigger_param = [result['contest_id']]
        for problem in l_problem:
            problem_id = problem.get('problem_id')
            table_param.extend([problem_id for i in range(2)])
            trigger_param.extend([problem_id for i in range(3)])
        sql_table.extend(["?_time float unsigned default '0', ?_wrong smallint(6) default '0',"] * len(l_problem))
        sql_table.append("foreign key (username) references t_user(username)) default charset=utf8")
        sql_trigger.append('+'.join(["new.?_time + (new.?_time xor 0) * new.?_wrong * 1200 "] * len(l_problem)))
        sql_trigger.append("; set new.total_time = total; end;")
        with db.transaction():
            db.update(' '.join(sql_table), *table_param)

            db.update('drop trigger if exists calculate_penalty')
            db.update(' '.join(sql_trigger), *trigger_param)

            db.update('drop trigger if exists calculate_submission')
            db.update(''.join(sql_trigger1))

            db.update('drop trigger if exists calculate_AC')
            db.update(''.join(sql_trigger2), configs.result_code.AC, configs.result_code.AC, configs.result_code.AC)

            db.update('drop trigger if exists calculate_penalty_time')
            db.update(''.join(sql_trigger3))

    @staticmethod
    def update_contest_ranking(result):
        """
        更新比赛统计数据
        :param result:
        :return:
        """
        rowcount = db.update("show tables like 't_?'", result['contest_id'])
        if rowcount == 0:
            PutTask._create_ranking_table(result)
        count = db.select_int('select count(*) from t_? where username=?', result['contest_id'], result['user_id'])
        if count == 0:
            user = dict(username=result['user_id'])
            db.insert('t_%s' % result['contest_id'], **user)
        p_time = db.select_one('select ?_time from t_? where username=?',
                               result['problem_id'], result['contest_id'], result['user_id'])\
            .get('%s_time' % result['problem_id'])
        if p_time == 0:  # 本题还没有AC
            if result['result'] == configs.result_code.AC:  # 本题初次AC
                with db.connection():
                    submit_time = db.select_one('select submit_time from t_submission where submission_id=?',
                                                result['solution_id']).get('submit_time')   # 提交时间, datetime类型
                    date_time = db.select_one('select contest_date, start_time from t_contest where contest_id=?',
                                              result['contest_id'])
                    c_date = date_time.get('contest_date')  # 比赛开始日期, date类型
                    c_time = date_time.get('start_time')    # 比赛开始时间, timedelta类型
                    # 转换为比赛开始时间, datetime类型
                    contest_time = datetime.strptime(c_date.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S') + c_time
                    ac_time = (submit_time - contest_time).total_seconds()  # 本题初次AC所用时间, 单位为秒, float类型
                    with db.transaction():
                        db.update('update t_? set solved = solved + 1 where username=?',
                                  result['contest_id'], result['user_id'])  # AC题数 + 1
                        db.update('update t_? set ?_time=? where username=?',
                                  result['contest_id'], result['problem_id'], ac_time, result['user_id'])   # AC题目所用时间
            else:
                db.update('update t_? set ?_wrong = ?_wrong + 1 where username=?',
                          result['contest_id'], result['problem_id'], result['problem_id'], result['user_id'])

    @staticmethod
    def update_contest_statistics(result):
        """
        更新比赛统计数据
        :param result:
        :return:
        """
        count = db.select_int('select count(*) from t_ranking where contest_id=? and problem_id=? and username=?',
                              result['contest_id'], result['problem_id'], result['user_id'])
        if count == 0:
            record = dict(contest_id=result['contest_id'], problem_id=result['problem_id'], username=result['user_id'])
            db.insert('t_ranking', **record)
        p_time = db.select_one('select AC_time from t_ranking where contest_id=? and problem_id=? and username=?',
                               result['contest_id'], result['problem_id'], result['user_id']).get('AC_time')
        if p_time == 0:  # 本题还没有AC
            if result['result'] == configs.result_code.AC:  # 本题初次AC
                with db.connection():
                    submit_time = db.select_one('select submit_time from t_submission where submission_id=?',
                                                result['solution_id']).get('submit_time')   # 提交时间, datetime类型
                    date_time = db.select_one('select contest_date, start_time from t_contest where contest_id=?',
                                              result['contest_id'])
                    c_date = date_time.get('contest_date')  # 比赛开始日期, date类型
                    c_time = date_time.get('start_time')    # 比赛开始时间, timedelta类型
                    # 转换为比赛开始时间, datetime类型
                    contest_time = datetime.strptime(c_date.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S') + c_time
                    ac_time = (submit_time - contest_time).total_seconds() / 60  # 本题初次AC所用时间, 单位为分钟, float类型
                    with db.transaction():
                        db.update('update t_ranking set AC_time=? where contest_id=? and problem_id=? and username=?',
                                  ac_time, result['contest_id'], result['problem_id'], result['user_id'])   # AC题目所用时间
            else:
                db.update('update t_ranking set wrong_submit = wrong_submit + 1 where contest_id=? and problem_id=? '
                          'and username=?', result['contest_id'], result['problem_id'], result['user_id'])

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # t = PutTask()
    '''
    t.update_contest_ranking(dict(contest_id=102, user_id='user2', problem_id=1042, solution_id=10001, result=1))   # AC前wrong
    t.update_contest_ranking(dict(contest_id=102, user_id='user2', problem_id=1042, solution_id=10001, result=0))   # 初次AC
    t.update_contest_ranking(dict(contest_id=102, user_id='user2', problem_id=1042, solution_id=10001, result=1))   # AC后wrong
    t.update_contest_ranking(dict(contest_id=102, user_id='user2', problem_id=1042, solution_id=10001, result=0))   # 多次AC
    '''
    # t._create_ranking_table(dict(contest_id=102))
    remote_data_dir = os.path.join(os.getcwd(), configs.oj.work_dir, '1001')
    print os.path.exists(remote_data_dir)