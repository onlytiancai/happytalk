# -*- coding: utf-8 -*-
import os
import sys
import signal
import pickle
import logging
from datetime import datetime, timedelta


import web

render = web.template.render('templates')

class TalkException(Exception):
    pass

class Model(object):
    def __init__(self):
        self.threads = []
        self.last_active_time = {}
        self.max_thread = 0
        self.max_user = 0

    def _check_safe(self, clientip):
        last_active_time = self.last_active_time.get(clientip)
        if last_active_time and datetime.now() - last_active_time < timedelta(minutes=1):
                raise TalkException(u"访问太快了亲")
        self.last_active_time[clientip] = datetime.now()

    def insert_thread(self, message, pid=0):
        user = self.get_user()
        clientip = web.ctx.ip
        self._check_safe(clientip)
        thread = web.storage(pid=pid, id=self.max_thread, user=user, message=message,
                             posttime=datetime.now())
        self.max_thread += 1
        self.threads.append(thread)

    def set_user(self):
        if not web.cookies().get('user'):
            self.max_user += 1
            web.setcookie('user', self.max_user)

    def get_user(self):
        return web.cookies().get('user', '0')


class IndexHandler(object):
    def GET(self):
        model.set_user()
        return render.index(model.get_user(), model.threads)

    def POST(self):
        data = web.input()
        model.insert_thread(data.message[:140], data.pid)
        return web.seeother('/')

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
    with open('model.db', 'wb') as f:
        pickle.dump(model, f)
    logging.info("end save model")
    sys.exit(0)

def load_model():
    if not os.path.exists('./model.db'):
        logging.info("load new model")
        return Model()

    with open('model.db', 'rb') as f:
        model = pickle.load(f)
        logging.info("load exists model:%s %s", model.max_thread, model.max_user)
        return model

urls = ["/", IndexHandler,
        ]

web.config.debug = False
init_logger('/data/log/happy_talk.log', 'debug', console=True)

model = load_model()

signal.signal(signal.SIGTERM, save_model)
signal.signal(signal.SIGINT, save_model)

app = web.application(urls, globals())
app.add_processor(my_processor)
app.notfound = notfound
app.internalerror = internalerror
wsgiapp = app.wsgifunc()

if __name__ == '__main__':
    app.run()
