# -*- coding: utf-8 -*-
import os
import sys
import signal
import pickle
import logging
import threading
import time
from datetime import datetime, timedelta

import web

class TalkException(Exception):
    pass

class Model(object):
    def __init__(self):
        self.threads = []
        self.clientips = {}
        self.max_thread = 0
        self.max_user = 0

    def _check_safe(self, clientip, message):
        message = message.strip()
        if not message:
            raise TalkException(u'你到底吐还是不吐')
        last_active_time = self.clientips.get(clientip)
        if last_active_time and datetime.now() - last_active_time < timedelta(minutes=1):
            raise TalkException(u"亲，你吐的太快了，让别人先吐会儿")
        if len(self.threads) > max_thread:
            raise TalkException(u'目前槽点均已吐满，请稍后再试')
        if minganci_filter(message):
            raise TalkException(u'亲，不该吐的不要吐, 你懂的')
        self.clientips[clientip] = datetime.now()

    def insert_thread(self, message):
        user = self.get_user()
        clientip = web.ctx.env.get('HTTP_X_REAL_IP', web.ctx.ip)
        self._check_safe(clientip, message)
        logging.info("insert thread:%s %s", clientip, message)
        thread = web.storage(id=self.max_thread, user=user, message=message,
                             posttime=datetime.now())
        self.max_thread += 1
        self.threads.append(thread)

    def get_user(self):
        user = web.cookies().get('user')
        if user:
            return user
        self.max_user += 1
        web.setcookie('user', self.max_user)
        return self.max_user


class IndexHandler(object):
    def GET(self):
        user = model.get_user()
        threads = sorted(model.threads, key=lambda x: x.posttime, reverse=True)
        return render.index(user, threads)

    def POST(self):
        data = web.input()
        model.insert_thread(data.message[:140])
        return web.seeother('/')

class AboutHandler(object):
    def GET(self):
        return render.about()

def my_processor(handler):
        return handler()

def notfound():
    web.ctx.status = '404 Not Found'
    return web.notfound(str(render._404()))


def internalerror():
    web.ctx.status = '500 Internal Server Error'
    ex_type, ex, tback = sys.exc_info()
    message = ex.message if hasattr(ex, 'message') else 'server error'
    return web.internalerror(str(render._500(message)))


def init_logger(logpath, level='info', console=False):
    import logging.handlers

    level = logging._levelNames.get(level, logging.INFO)

    logger = logging.getLogger()
    logger.propagate = False
    logger.setLevel(level)

    handler = logging.handlers.RotatingFileHandler(logpath, maxBytes=100 * 1000 * 1000, backupCount=10)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if console:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(formatter)
        logger.addHandler(consoleHandler)

def save_model(signal, frame):
    logging.info("begin save model")
    with open(model_db_path, 'wb') as f:
        pickle.dump(model, f)
    logging.info("end save model")
    sys.exit(0)

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

    def _clean_threads(self):
        now = datetime.now()
        remove_list = []
        for thread in model.threads:
            if now - thread.posttime > max_alive_time:
                remove_list.append(thread)
        for thread in remove_list:
            logging.info("clean thread remove:%s %s", thread.id, thread.message)
            model.threads.remove(thread)

    def _clean_clientips(self):
        remove_list = []
        for ip, last_active_time in model.clientips.items():
            if datetime.now() - last_active_time < timedelta(minutes=2):
                remove_list.append(ip)
        logging.info("clean thread remove clientip:%s", len(remove_list))
        for ip in remove_list:
            del model.clientips[ip]

    def run(self):
        while True:
            try:
                logging.info("clean thread runing")
                self._clean_threads()
            except:
                logging.exception("clean thread run error")
            finally:
                time.sleep(60)

def timeinfo(time):
    diff = time + max_alive_time - datetime.now()
    if diff > timedelta(hours=1):
        return u"%s小时" % int(diff.total_seconds() / 60 / 60)
    return u"%s分钟" % int(diff.total_seconds() / 60)

def load_minganci():
    for line in open('./minganci.txt'):
        word = line.strip().decode('utf-8')
        if word:
            yield word

def minganci_filter(message):
    for word in minganci_list:
        if message.find(word) != -1:
            return word
    return None

urls = ["/", IndexHandler,
        "/about", AboutHandler,
        ]

# configurage
web.config.debug = False
tpl_globals = {'timeinfo': timeinfo}
render = web.template.render('templates', base='layout', cache=False, globals=tpl_globals)
init_logger('/data/log/happy_talk.log', 'debug', console=True)
model_db_path = '/data/happytalk.model.db'
max_thread = 100
max_alive_time = timedelta(hours=24)

# init
model = load_model()
minganci_list = list(load_minganci())
clean_thread = CleanThread()
clean_thread.start()

signal.signal(signal.SIGTERM, save_model)
signal.signal(signal.SIGINT, save_model)
signal.signal(signal.SIGHUP, save_model)

app = web.application(urls, globals())
app.add_processor(my_processor)
app.notfound = notfound
app.internalerror = internalerror

wsgiapp = app.wsgifunc()

if __name__ == '__main__':
    app.run()
