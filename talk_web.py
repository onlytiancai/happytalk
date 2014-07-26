# -*- coding: utf-8 -*-
import sys
from datetime import datetime, timedelta
import web
import model


web.config.debug = False
log_path = '/data/log/happy_talk.log'
log_level = 'debug'


class IndexHandler(object):
    def GET(self):
        user = model.model.get_user()
        threads = sorted(model.model.threads, key=lambda x: x.posttime, reverse=True)
        return render.index(user, threads)

    def POST(self):
        data = web.input(message='')
        clientip = web.ctx.env.get('HTTP_X_REAL_IP', web.ctx.ip)

        model.model.check_safe(clientip, data.message)
        if model.minganci_filter(data.message):  # 这个不用加锁而且耗时
            raise model.TalkException(u'亲，不该吐的不要吐, 你懂的')

        model.model.insert_thread(clientip, data.message)
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
    formatter = logging.Formatter('%(levelname)s %(asctime)s- [%(module)s.%(funcName)s](%(thread)d): %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if console:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(formatter)
        logger.addHandler(consoleHandler)

def timeinfo(time):
    diff = time + model.max_alive_time - datetime.now()
    if diff > timedelta(hours=1):
        return u"%s小时" % int(diff.total_seconds() / 60 / 60)
    return u"%s分钟" % int(diff.total_seconds() / 60)

urls = ["/", IndexHandler,
        "/about", AboutHandler,
        ]

init_logger(log_path, log_level, console=True)
model.init()
tpl_globals = {'timeinfo': timeinfo}
render = web.template.render('templates', base='layout', cache=False, globals=tpl_globals)

app = web.application(urls, globals())
app.add_processor(my_processor)
app.notfound = notfound
app.internalerror = internalerror

wsgiapp = app.wsgifunc()

if __name__ == '__main__':
    app.run()
