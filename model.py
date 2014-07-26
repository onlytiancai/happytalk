# -*- coding: utf-8 -*-
import os
import sys
import logging
import threading
import time
import pickle
import signal
from datetime import datetime, timedelta

import web

model_db_path = '/data/happytalk.model.test.db'
max_thread = 100
max_alive_time = timedelta(hours=24)

class TalkException(Exception):
    pass

def lockroot(func):
    def inner(*args, **kargs):
        try:
            root_lock.acquire()
            return func(*args, **kargs)
        finally:
            root_lock.release()
    return inner


class Model(object):
    def __init__(self):
        self.threads = []
        self.clientips = {}
        self.max_thread = 0
        self.max_user = 0

    @lockroot
    def check_safe(self, clientip, message):
        message = message.strip()
        if not message:
            raise TalkException(u'你到底吐还是不吐')
        if len(message) > 280:
            raise TalkException(u'你至于吐这么多吗')
        last_active_time = self.clientips.get(clientip)
        if last_active_time and datetime.now() - last_active_time < timedelta(minutes=1):
            raise TalkException(u"亲，你吐的太快了，让别人先吐会儿")
        if len(self.threads) > max_thread:
            raise TalkException(u'目前槽点均已吐满，请稍后再试')
        self.clientips[clientip] = datetime.now()

    @lockroot
    def insert_thread(self, clientip, message):
        user = self.get_user()  # RLock支持递归，可以放心调用
        logging.info("insert thread:%s %s", clientip, message)
        thread = web.storage(id=self.max_thread, user=user, message=message,
                             posttime=datetime.now())
        self.max_thread += 1
        self.threads.append(thread)

    @lockroot
    def get_user(self):
        user = web.cookies().get('user')
        if user:
            return user
        self.max_user += 1
        web.setcookie('user', self.max_user)
        return self.max_user

@lockroot
def save_model(signal, frame):
    logging.info("begin save model")
    with open(model_db_path, 'wb') as f:
        pickle.dump(model, f)
    logging.info("end save model")
    sys.exit(0)

@lockroot
def load_model():
    if not os.path.exists(model_db_path):
        logging.info("load new model")
        return Model()

    with open(model_db_path, 'rb') as f:
        model = pickle.load(f)
        logging.info("load exists model:%s %s", model.max_thread, model.max_user)
        return model

class CleanThread(threading.Thread):
    def __init__(self):
        super(CleanThread, self).__init__()
        self.setDaemon(True)
        self.name = 'Clean Thread'

    @lockroot
    def _clean_threads(self):
        now = datetime.now()
        remove_list = []
        for thread in model.threads:
            if now - thread.posttime > max_alive_time:
                remove_list.append(thread)
        for thread in remove_list:
            logging.info("clean thread remove:%s %s", thread.id, thread.message)
            model.threads.remove(thread)

    @lockroot
    def _clean_clientips(self):
        now = datetime.now()
        remove_list = []
        for ip, last_active_time in model.clientips.items():
            if now - last_active_time < timedelta(minutes=2):
                remove_list.append(ip)
        logging.info("clean thread remove clientip:%s", len(remove_list))
        for ip in remove_list:
            del model.clientips[ip]

    def _sync_model(self):
        u'每隔1小时同步下数据'
        now = datetime.now()
        if now.minute == 0:
            save_model()

    def run(self):
        while True:
            try:
                logging.info("clean thread runing")
                self._clean_threads()
                self._clean_clientips()
                self._sync_model()
            except:
                logging.exception("clean thread run error")
            finally:
                time.sleep(60)

def load_minganci():
    logging.info("loading minganci")
    for line in open('./minganci.txt'):
        word = line.strip().decode('utf-8')
        if word:
            yield word

def minganci_filter(message):
    for word in minganci_list:
        if message.find(word) != -1:
            return word
    return None

model = None
minganci_list = None
clean_thread = None
root_lock = threading.RLock()

def init():
    global model, minganci_list, clean_thread, root_lock
    model = load_model()
    minganci_list = list(load_minganci())

    clean_thread = CleanThread()
    clean_thread.start()

    signal.signal(signal.SIGTERM, save_model)
    signal.signal(signal.SIGINT, save_model)
