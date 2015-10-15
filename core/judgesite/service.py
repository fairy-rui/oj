#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'snow'

import logging
import pika
import json
from config import configs
from judgesite import JudgeTask


class JudgeSite(object):
    """
    The online judge site deal with judge task and put the result into the queue.
    """
    def __init__(self):
        self.connection = \
            pika.BlockingConnection(pika.ConnectionParameters(host=configs.dc.rmq_host, port=configs.dc.rmq_port,
                                                              virtual_host=configs.dc.virtual_host,
                                                              credentials=pika.PlainCredentials(configs.dc.rmq_user,
                                                                                                configs.dc.rmq_password
                                                                                                )
                                                              )
                                    )
        self.channel = self.connection.channel()
        # 定义发布任务的队列
        self.channel.queue_declare(queue=configs.dc.task_queue, durable=True)
        # 定义接收任务返回消息的队列
        self.channel.queue_declare(queue=configs.dc.result_queue, durable=True)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self._handle_task, queue=configs.dc.task_queue, no_ack=False)

    def __del__(self):
        self.connection.close()  # 关闭连接

    @staticmethod
    def _handle_task(ch, method, properties, body):
        task = json.loads(body)
        logging.debug(task)
        judge = JudgeTask(task)
        result = judge.go()
        # 将评判结果发送回任务控制中心
        ch.basic_publish(exchange='',
                         routing_key=properties.reply_to,
                         properties=pika.BasicProperties(
                             delivery_mode=2,   # make message persistent
                             content_type='application/json'
                         ),
                         body=json.dumps(result))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def run(self):
        self.channel.start_consuming()