#!/usr/bin/python  
#encoding: utf8

import time
import MySQLdb as db 
import urllib2 
from dht import bencode, BTL

DB_CONFIG = ("localhost", "hexiong", "hexiong", "hexiong")

#mysql connection handler
conn = db.connect( *DB_CONFIG ) 
c = conn.cursor()
c.execute("set names utf8") 

c.connection.autocommit( True )

def get_torrent_from_xunlei( hash_info ):
    hash_info = hash_info.upper()
    h, t = hash_info[0: 2], hash_info[-2: ]
    url = "http://bt.box.n0808.com/%s/%s/%s.torrent" % (h, t, hash_info)
    try:
        res = urllib2.urlopen( url ).read()
        res = bencode.bdecode( res )
    except urllib2.HTTPError, e:
        return "404"  
    except BTL.BTFailure, e:
        return "BTFailure"  
    except:
        return "503" 
    return res

def get_max_id():
    global c
    sql = 'select max_id from t_max_id' 
    c.execute( sql )
    max_id = c.fetchone()[0] 
    return max_id

def update_max_id( max_id ):
    global c
    sql = 'update t_max_id set max_id = %s' % max_id
    c.execute( sql )
    
def update_torrent_info( t_id, t_hash_info, torrent_dict ):
    global c 
    name = torrent_dict["info"]["name"] 
    t_encoding = None
    print t_hash_info 
    create_time = torrent_dict.get("creation date", time.time()) 
    print create_time 
    try:
        create_time = time.strftime("%Y-%m-%d %X", time.gmtime( create_time ))
    except:
        pass 

    if torrent_dict.has_key("encoding"):
        t_encoding = torrent_dict["encoding"] 
    
    if torrent_dict["info"].has_key("name.utf-8"):
        name = torrent_dict["info"]["name.utf-8"]
        print "name.utf-8 ", name 
    else:
        if t_encoding: 
            try:
                name = name.decode(t_encoding).encode("utf8")
            except Exception, e:
                print e 

    is_dir = True if torrent_dict["info"].has_key("files") else False
    try:
        if is_dir:
            sql = '''insert into t_torrent_info (id, hash_info, is_dir, name, create_time) 
                     values (%s, "%s", 1, "%s", "%s") ''' % (t_id, t_hash_info, name, create_time)

            print sql 
            c.execute( sql )
            sql = '''insert into t_files (id, file_name, size) values'''
            for p in torrent_dict["info"]["files"]:
                if p.has_key("path.utf-8"):
                    file_name = " ".join( p["path.utf-8"] )
                else:
                    file_name = " ".join( p["path"] ) 
                    if t_encoding:
                        try:
                            file_name = file_name.decode(t_encoding).encode("utf8")
                        except Exception, e:
                            print e 

                file_size = p["length"]
                sql += '(%s, "%s", %s),' % (t_id, file_name, file_size) 
            sql = sql[:-1] 
            print sql 
            c.execute( sql )
        else:
            size = torrent_dict["info"]["length"]
            sql = '''insert into t_torrent_info (id, hash_info, name, size, create_time) 
                     values(%s, "%s", "%s", %s, "%s") ''' % (t_id, t_hash_info, name, size, create_time) 
            c.execute( sql )
    except db.Error, e:
        print "update_torrent_info ", e  

def get_next_hash_list( max_id ):
    global c 
    sql = 'select id, hash_info from t_hash_info where id > %s' % max_id
    c.execute( sql )
    rows = c.fetchall()
    return rows

def insert_retry_queue( infos ):
    global c 
    if not infos:
        return 
    try:
        t_id = infos[0]
        t_hash_info = infos[1]
        sql = '''insert into t_retry_queue (id, count, hash_info)
                 values (%s, 1, "%s")''' % (t_id, t_hash_info) 
        c.execute( sql )
    except db.Error, e:
        print "insert_retry_queue ", e  

def main():
    while True:
        max_id = get_max_id()
        print "current max id: %s" % max_id 
        rows = get_next_hash_list( max_id )  
 
        next_max_id = max_id 

        for row in rows:    
            t_id = row[0]

            if t_id > next_max_id:
                next_max_id = t_id
            
            t_hash_info = row[1]
            torrent_dict = get_torrent_from_xunlei( t_hash_info )

            if torrent_dict in ["404", "BTFailure", "503"]:
                insert_retry_queue( row )

                if torrent_dict == "503":
                    print "%s 503" % t_hash_info 

                continue    
        
            update_torrent_info(t_id, t_hash_info, torrent_dict) 

        update_max_id( next_max_id )

        print "next loop"
        time.sleep( 30 * 1 )

if __name__ == "__main__":
    main()




