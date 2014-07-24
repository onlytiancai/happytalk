# -*- coding: utf-8 -*-
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

model = Model()

class IndexHandler(object):
    def GET(self):
        model.set_user()
        return render.index(model.get_user(), model.threads)

    def POST(self):
        data = web.input()
        model.insert_thread(data.message[:140], data.pid)
        return web.seeother('/');

urls = ["/", IndexHandler,
       ]

app = web.application(urls, globals())
wsgiapp = app.wsgifunc()

if __name__ == '__main__':
    app.run()
