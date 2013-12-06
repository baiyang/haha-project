#!/usr/bin/env python
#encoding: utf8 
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os.path
import re
import torndb
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
import os, sys
import xmlrpclib

from tornado.options import define, options
sys.path.append( os.path.join( os.path.abspath("."), "handlers" ) ) 

from home import HomeHandler 
from home import Search 
from home import SearchByHashInfo 
from acc_heatmap import AccHeatMap 

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="blog database host")
define("mysql_database", default="hexiong", help="blog database name")
define("mysql_user", default="hexiong", help="blog database user")
define("mysql_password", default="hexiong", help="blog database password")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/search", Search),
            (r"/get", SearchByHashInfo), 
            (r"/acc_heatmap", AccHeatMap) 
        ]
        settings = dict(
            blog_title=u"搜电影,找哈哈",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # Have one global connection to the blog DB across all handlers
        self.db = torndb.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password) 
        self.db._db_args["init_command"] = ('set time_zone = "+8:00"')   
        self.db.reconnect() 
        self.db.execute( "set names utf8" ) 
        self.seg = xmlrpclib.ServerProxy("http://localhost:8080/")

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()


