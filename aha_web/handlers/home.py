#!/usr/bin/python
#encoding: utf8
from base import * 
from datetime import date, timedelta
import tornado.web 

def humanreadable( size ):
    code = ["K", "M", "G"]
    for i in xrange(3):
        s = size / 1024.0
        if s < 1024.0:
            return "%.2f%s" % (s, code[i]) 
        size = s
    return "%.2f%s" % (size, "G") 

class HomeHandler(BaseHandler):
    def get(self):
        today = date.today()
        diff = timedelta(1)
        num = 3
        lines = []
        for i in xrange(num):
            ln = {}
            curr = today - diff * i 
            ln["time"] = curr.strftime("%Y-%m-%d") 
            sql = '''select count(*) as t from t_hash_info 
                     where date(found_time) = "%s"
                  ''' % ln["time"]  
            ln["cnt"] = self.db.get(sql)["t"] 
            sql = '''select count(*) as t from t_torrent_info
                     where date(found_time) = "%s"
                  ''' % ln["time"] 
            ln["new_cnt"] = self.db.get(sql)["t"] 
            lines.append( ln ) 
        sql = 'select count(*) as t from t_torrent_info'
        total = self.db.get(sql)["t"] 
        self.render("input.html", lines=lines, total=total) 

class Search(BaseHandler):
    def get(self):
        page_size = 23 

        t_keyword = self.get_argument("t_keyword", "") 
        t_page = self.get_argument("page", "0")

        t_page = int(t_page)

        t_start = page_size * t_page 
        if not t_keyword:
            self.redirect("/")
            return 

        remote_ip = self.request.remote_ip
        sql = '''insert into t_keyword(keyword, ip) values("%s", "%s")
              ''' % (t_keyword , remote_ip)  
        print sql 
        self.db.execute(sql) 

        t_keyword = self.seg.do_text_segmentation( t_keyword ) 
        t_keyword = " ".join( t_keyword ) 
        
        sql = '''select * from t_torrent_info 
                 where match (seg_name)  
                 against ("%s" in natural language mode) limit %s, %s 
              ''' % (t_keyword, t_start, page_size) 

        items = self.db.query( sql )
        for i in items:
            if i["size"]:
                i["size"] = humanreadable( i["size"] ) 
        
        sql = '''select * from t_torrent_info 
                 where match (seg_name)  
                 against ("%s" in natural language mode)
              ''' % t_keyword
        total_lines = self.db.execute_rowcount( sql )
        t_page_num = int(total_lines / page_size)
        
        settings = {}
        settings["t_page"] = t_page
        settings["t_keyword"] = t_keyword
        settings["t_page_num"] = t_page_num

        self.render("feeds.html", items=items, s=settings)  


class SearchByHashInfo(BaseHandler):
    def get(self):
        t_hash = self.get_argument("t_hash", "") 
        t_keyword = self.get_argument("t_keyword", "") 
        if not t_hash:
            return 

        sql = '''select * from t_torrent_info where hash_info="%s"''' % t_hash 
        desc = self.db.get( sql ) 
        if not desc:
            return 

        is_dir = desc["is_dir"] 
        files = []  
        if is_dir == 1:
            id = desc["id"] 
            sql = 'select * from t_files where id = "%s"' % id
            files = self.db.query( sql )
        else:
            if desc["size"]:
                desc["size"]  = humanreadable( desc["size"] ) 
            
        for i in files:
            i["size"] = humanreadable( i["size"] ) 
            
        s = {}
        s["t_keyword"] = t_keyword 
        self.render("download.html", desc=desc, files=files, s=s) 

