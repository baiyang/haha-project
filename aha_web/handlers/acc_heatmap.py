#!/usr/bin/python
#encoding: utf8
from base import * 
from datetime import date, timedelta
import tornado.web 

class AccHeatMap(BaseHandler):
    def get(self):
        self.render( "acc_heatmap.html" ) 
        return 
