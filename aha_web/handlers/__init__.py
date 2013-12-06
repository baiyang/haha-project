#!/usr/bin/python 
#encoding: utf8

import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db




