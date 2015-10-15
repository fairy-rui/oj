#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'snow'

import pika
import logging
import time
import threading
import json
from config import configs
from center import PutTask


class JudgeCenter(object):
    """
    The online judge center put judge task into the queue
    and deal with the result from the queue.
    """

    def __init__(self):
        self.put_task = PutTask()
        self.interval_time = configs.scan_db.min_time   # 扫描数据库时间间隔

        self.task_connection = \
            pika.BlockingConnection(pika.ConnectionParameters(host=configs.dc.rmq_host, port=configs.dc.rmq_port,
                                                              virtual_host=configs.dc.virtual_host,
                                                              credentials=pika.PlainCredentials(configs.dc.rmq_user,
                                                                                                configs.dc.rmq_password
                                                                                                )
                                                              )
                                    )

        self.task_channel = self.task_connection.channel()
        # 定义发布任务的队列
        self.task_channel.queue_declare(queue=configs.dc.task_queue, durable=True)

        self.result_connection = \
            pika.BlockingConnection(pika.ConnectionParameters(host=configs.dc.rmq_host, port=configs.dc.rmq_port,
                                                              virtual_host=configs.dc.virtual_host,
                                                              credentials=pika.PlainCredentials(configs.dc.rmq_user,
                                                                                                configs.dc.rmq_password
                                                                                                )
                                                              )
                                    )
        self.result_channel = self.result_connection.channel()
        # 定义接收任务返回消息的队列
        self.result_channel.queue_declare(queue=configs.dc.result_queue, durable=True)

        self.result_channel.basic_qos(prefetch_count=1)
        self.result_channel.basic_consume(self._handle_task_result, queue=configs.dc.result_queue, no_ack=False)

    def __del__(self):
        self.task_connection.close()  # 关闭连接
        self.result_connection.close()

    def _handle_task_result(self, ch, method, properties, body):
        result = json.loads(body)
        self.put_task.update_result(result)   # 更新任务处理结果
        if result['contest_id'] != 0:
            self.put_task.update_contest_statistics(result)    # 更新比赛统计数据
        ch.basic_ack(delivery_tag=method.delivery_tag)  # 发送任务完成确认ACK

    def run(self):
        self._start_publish_task()
        self.result_channel.start_consuming()

    def _adjust_scan_frequency(self, count):
        """
        调整扫描数据库频率
        :param count:任务数量
        :return:时间间隔
        """
        '''
        self.interval_time -= configs.scan_db.step_time if configs.scan_db.threshold_num < \
            count < configs.scan_db.max_num else 0
        self.interval_time += configs.scan_db.step_time if count == configs.scan_db.min_num and \
            self.interval_time <= configs.scan_db.threshold_time else 0
        self.interval_time = configs.scan_db.min_time if count >= configs.scan_db.max_num and \
            self.interval_time <= configs.scan_db.threshold_time else self.interval_time
        self.interval_time *= 2 if count == configs.scan_db.min_num and \
            self.interval_time > configs.scan_db.threshold_time else 1
        self.interval_time /= 2 if count >= configs.scan_db.max_num and \
            self.interval_time > configs.scan_db.threshold_time else 1
        '''
        if configs.scan_db.threshold_num < count < configs.scan_db.max_num:
            self.interval_time -= configs.scan_db.step_time
        elif count == configs.scan_db.min_num and self.interval_time <= configs.scan_db.threshold_time:
            self.interval_time += configs.scan_db.step_time
        elif count >= configs.scan_db.max_num and self.interval_time <= configs.scan_db.threshold_time:
            self.interval_time = configs.scan_db.min_time
        elif count == configs.scan_db.min_num and self.interval_time > configs.scan_db.threshold_time:
            self.interval_time *= 2
        elif count >= configs.scan_db.max_num and self.interval_time > configs.scan_db.threshold_time:
            self.interval_time /= 2

        if self.interval_time < configs.scan_db.min_time:
            self.interval_time = configs.scan_db.min_time
        if self.interval_time > configs.scan_db.max_time:
            self.interval_time = configs.scan_db.max_time

        return self.interval_time

    def _publish_task(self):
        while True:
            l_task = self.put_task.get_task()

            for task in l_task:
                # 发布任务,并声明返回队列
                self.task_channel.basic_publish(exchange='',
                                                routing_key=configs.dc.task_queue,
                                                properties=pika.BasicProperties(
                                                    reply_to=configs.dc.result_queue,
                                                    delivery_mode=2,  # make message persistent
                                                    content_type='application/json'
                                                ),
                                                body=json.dumps(task))
                logging.info('put task %s' % (task['solution_id']))
            # self.connection.sleep(1)
            time.sleep(self._adjust_scan_frequency(len(l_task)))

    def _start_publish_task(self):
        t = threading.Thread(target=self._publish_task, name='publish_task')
        t.daemon = True
        t.start()

    """
    def _handle_contest_ranking(self, result):
        t = threading.Thread(target=self.put_task.update_contest_ranking, args=(result,), name='handle_contest_ranking')
        t.daemon = True
        t.start()
    """