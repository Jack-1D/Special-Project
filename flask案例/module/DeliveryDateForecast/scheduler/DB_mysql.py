'''
目的: 資料庫中處理排程所需的資料
對資料庫的增刪查改
'''
import pymysql as MySQLdb
import pandas as pd
from datetime import timedelta, datetime

ll = list[list]
dataframe = pd.DataFrame

class Mysql(object):
    def __init__(self, host: str, user: str, password: str, db: str, port: int):
        try:
            self.conn = MySQLdb.connect(host=host,user=user,password=password,database=db,port=port)
        except MySQLdb.Error as e:
            errormsg = f"Connection error\nERROR({e.args[0],e.args[1]})"
            print(errormsg)
        self.cur = self.conn.cursor()
    
    def execute_line(self,command: str):
        try:
            self.cur.execute(command)
            self.conn.commit()
        except:
            self.conn.rollback()

    def __del__(self):
        self.conn.close()
        self.cur.close()
    # class 中的方法
    # 取得1G-POE訂單queue
    def get_1G_orderlist(self) -> tuple:
        self.execute_line("SELECT * FROM orderlist WHERE type='1G-POE' ORDER BY needdate")
        return self.cur.fetchall()
    # 取得10G訂單queue
    def get_10G_orderlist(self) -> tuple:
        self.execute_line("SELECT * FROM orderlist WHERE type='10G' ORDER BY needdate")
        return self.cur.fetchall()
    # 取得昨天的buffer
    def get_buffer(self, yesterday_date: str) -> tuple:
        self.execute_line(f"SELECT buffer1g, buffer10g FROM buffer WHERE date='{yesterday_date}'")
        return self.cur.fetchall()
    # 插入訂單
    def insert_orderlist(self, param: dict) -> int:
        self.execute_line(f"INSERT INTO orderlist(needdate,number,orderdate,type) SELECT * FROM ( SELECT \
        '{param['need_date']}',{param['number']},'{param['order_date']}','{param['type']}' ) AS tmp WHERE NOT \
        EXISTS (SELECT 1 FROM orderlist WHERE needdate='{param['need_date']}' AND number={param['number']} AND \
        orderdate='{param['order_date']}' AND type='{param['type']}')")
        return self.cur.lastrowid
    # 刪除訂單
    def delete_orderlist(self, param: dict) -> None:
        self.execute_line(f"DELETE FROM orderlist WHERE id={param['id']}")
        return
    # 刪除所有機台生產資料
    def delete_all_product(self) -> None:
        self.execute_line("DELETE FROM product")
        return
    # 插入機台生產資訊
    def insert_product(self, row: dataframe) -> None:
        self.execute_line(f"INSERT IGNORE INTO product VALUES('{getattr(row,'生產日期')}{getattr(row,'機台號')}\
                          {getattr(row,'班別')}','{getattr(row,'生產日期')}','{getattr(row,'機台號')}',\
                          '{getattr(row,'班別')}',{getattr(row,'產能')},{getattr(row,'OEE')},{getattr(row,'良率')})")
        return
    # 取得昨天1G生產量
    def get_1G_production(self, yesterday_date: str) -> tuple:
        self.execute_line(f"SELECT production FROM product WHERE date='{yesterday_date}' AND \
                     (machine='h06' OR machine='h14')")
        return self.cur.fetchall()
    # 取得昨天10G生產量
    def get_10G_production(self, yesterday_date: str) -> tuple:
        self.execute_line(f"SELECT production FROM product WHERE date='{yesterday_date}' AND\
                           (machine='h01' OR machine='h02'OR machine='h08'OR machine='h10'OR\
                           machine='h15'OR machine='h19')")
        return self.cur.fetchall()
    # 出貨完後更新buffer剩餘值
    def update_buffer(self, yesterday_date: str, buffer1G: int, buffer10G: int) -> None:
        self.execute_line(f"REPLACE INTO buffer VALUES('{yesterday_date}',{buffer1G},{buffer10G})")
        return
    # 插入完成訂單
    def insert_finishedorder(self, pq: ll) -> None:
        self.execute_line(f"INSERT INTO finishedorder(id,needdate,number,orderdate,type) VALUES({pq[0]},\
                            '{pq[1]}',{pq[2]},'{pq[3]}','{pq[4]}')")
        return
    # 取得完成清單
    def get_finishedorder(self) -> tuple:
        self.execute_line(f"SELECT * FROM finishedorder ORDER BY needdate DESC")
        return self.cur.fetchall()

    # 取得1G-POE、10G每日總產量
    def get_daily_production_sum(self) -> tuple:
        self.execute_line(f"SELECT date, SUM(production) FROM product WHERE (machine='h06' OR machine='h14') \
                            GROUP BY date")
        sum_1G = self.cur.fetchall()
        self.execute_line(f"SELECT date, SUM(production) FROM product WHERE (machine='h01' OR machine='h02' OR \
                            machine='h08' OR machine='h10' OR machine='h15' OR machine='h19') GROUP BY date")
        sum_10G = self.cur.fetchall()
        return sum_1G, sum_10G

    # 取得1G機台每日產量
    def get_1G_production_sum(self, day: str) -> tuple:
        self.execute_line(f"SELECT SUM(production) FROM product WHERE date='{day.date()}' AND \
                          (machine='h06' OR machine='h14')")
        return self.cur.fetchall()
    # 取得1G機台每日產量
    def get_10G_production_sum(self, day: str) -> tuple:
        self.execute_line(f"SELECT SUM(production) FROM product WHERE date='{day.date()}' AND \
                          (machine='h01' OR machine='h02' OR machine='h08' OR machine='h10' OR \
                          machine='h15' OR machine='h19')")
        return self.cur.fetchall()
    # 取得1G buffer每日值
    def get_1G_buffer(self, day: str) -> tuple:
        self.execute_line(f"SELECT buffer1g FROM buffer WHERE date='{day.date()}'")
        return self.cur.fetchall()
    # 取得10G buffer每日值
    def get_10G_buffer(self, day: str) -> tuple:
        self.execute_line(f"SELECT buffer10g FROM buffer WHERE date='{day.date()}'")
    # 取得前14天的機台數
    def get_num_machine(self, day: str) -> tuple:
        d = datetime.strptime(day,"%Y-%m-%d").date()
        self.execute_line(f"SELECT A.date, IFNULL(B.num,0) FROM (SELECT date FROM orderlist.product WHERE date \
        BETWEEN '{d-timedelta(days=14)}' AND '{d}' GROUP BY date) AS A LEFT JOIN (SELECT date, COUNT(*) AS num \
        FROM orderlist.product WHERE date BETWEEN '{d-timedelta(days=14)}' AND '{d}' AND (machine='h06' OR \
        machine='h14') AND production>=1500 GROUP BY date) AS B ON A.date = B.date")
        product_1G = self.cur.fetchall()
        self.execute_line(f"SELECT A.date, IFNULL(B.num,0) FROM (SELECT date FROM orderlist.product WHERE date \
        BETWEEN '{d-timedelta(days=14)}' AND '{d}' GROUP BY date) AS A LEFT JOIN (SELECT date, COUNT(*) AS num \
        FROM orderlist.product WHERE date BETWEEN '{d-timedelta(days=14)}' AND '{d}' AND (machine='h01' OR \
        machine='h02' OR machine='h08' OR machine='h10' OR machine='h15' OR machine='h19') AND production>=1500 \
        GROUP BY date) AS B ON A.date = B.date")
        product_10G = self.cur.fetchall()
        return product_1G, product_10G

    def search_order(self, ID: tuple) -> None:
        self.execute_line(f"SELECT * FROM orderlist WHERE id={ID}")
        return self.cur.fetchall()

    def update_delivery_date(self, param: tuple) -> None:
        self.execute_line(f"REPLACE INTO orderlist VALUES({param['id']},'{param['need_date']}',{param['number']},'{param['order_date']}','{param['type']}','{param['delivery_date']}')")
        return