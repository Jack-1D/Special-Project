'''
目的: 處理排程所需的資料
1. buffer
- 儲存目前預算庫存
2. pq: priority queue
- 訂單資料

程式參考: https://blog.51cto.com/icenycmh/2118718
'''
import MySQLdb
import pandas as pd

ll = list[list]
dataframe = pd.DataFrame


#處理 XXX 在mysql 上
class Mysql(object):
    def __init__(self, host: str, user: str, password: str, db: str):
        try:
            self.conn = MySQLdb.connect(host,user,password,db)
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
    # 取得訂單queue
    def get_orderlist(self) -> tuple:
        self.execute_line("SELECT * FROM ORDERLIST ORDER BY NEEDDATE")
        return self.cur.fetchall()
    # 取得昨天的buffer
    def get_buffer(self, yesterday_date: str) -> tuple:
        self.execute_line(f"SELECT BUFFER1G, BUFFER10G FROM BUFFER WHERE DATE='{yesterday_date}'")
        return self.cur.fetchall()
    # 插入訂單
    def insert_orderlist(self, param: dict) -> None:
        self.execute_line(f"INSERT INTO ORDERLIST VALUES('{param['need_date']}',{param['number']},\
                          '{param['order_date']}','{param['type']}')")
        return
    # 刪除訂單
    def delete_orderlist(self, param: list) -> None:
        self.execute_line(f"DELETE FROM ORDERLIST WHERE NEEDDATE='{param['need_date']}' AND \
                          NUMBER={param['number']} AND ORDERDATE='{param['order_date']}' AND TYPE='{param['type']}'")
        return
    # 刪除所有機台生產資料
    def delete_all_product(self) -> None:
        self.execute_linee("DELETE FROM PRODUCT")
        return
    # 插入機台生產資訊
    def insert_product(self, row: dataframe) -> None:
        self.execute_line(f"INSERT IGNORE INTO PRODUCT VALUES('{getattr(row,'生產日期')}{getattr(row,'機台號')}\
                          {getattr(row,'班別')}','{getattr(row,'生產日期')}','{getattr(row,'機台號')}',\
                          '{getattr(row,'班別')}',{getattr(row,'產能')},{getattr(row,'OEE')},{getattr(row,'良率')})")
        return
    # 取得昨天1G生產量
    def get_1G_production(self, yesterday_date: str) -> tuple:
        self.execute(f"SELECT PRODUCTION FROM PRODUCT WHERE DATE='{yesterday_date}' AND \
                     (MACHINE='h06' OR MACHINE='h14')")
        return self.cur.fetchall()
    # 取得昨天10G生產量
    def get_10G_production(self, yesterday_date: str) -> tuple:
        self.execute_line(f"SELECT PRODUCTION FROM PRODUCT WHERE DATE='{yesterday_date}' AND\
                           (MACHINE='h01' OR MACHINE='h02'OR MACHINE='h08'OR MACHINE='h10'OR\
                           MACHINE='h15'OR MACHINE='h19')")
        return self.cur.fetchall()
    # 出貨完後更新buffer剩餘值
    def update_buffer(self, yesterday_date: str, buffer1G: int, buffer10G: int) -> None:
        self.execute_line(f"REPLACE INTO BUFFER VALUES('{yesterday_date}',{buffer1G},{buffer10G})")
        return
    # 插入完成訂單
    def insert_finishedorder(self, pq: ll) -> None:
        self.execute_line(f"INSERT INTO FINISHEDORDER VALUES('{pq[0][0]}','{pq[0][1]}','{pq[0][2]}',{pq[0][3]})")
        return
    # 取得完成清單
    def get_finishedorder(self) -> tuple:
        self.execute_line(f"SELECT * FROM FINISHEDORDER")
        return self.cur.fetchall()
    # 取得1G機台每日產量
    def get_1G_production_sum(self, day: int) -> tuple:
        self.execute_line(f"SELECT SUM(PRODUCTION) FROM PRODUCT WHERE DATE='{day.date()}' AND \
                          (MACHINE='h06' OR MACHINE='h14')")
        return self.cur.fetchall()
    # 取得1G機台每日產量
    def get_10G_production_sum(self, day: int) -> tuple:
        self.execute_line(f"SELECT SUM(PRODUCTION) FROM PRODUCT WHERE DATE='{day.date()}' AND \
                          (MACHINE='h01' OR MACHINE='h02' OR MACHINE='h08' OR MACHINE='h10' OR \
                          MACHINE='h15' OR MACHINE='h19')")
        return self.cur.fetchall()
    # 取得1G buffer每日值
    def get_1G_buffer(self, day: int) -> tuple:
        self.execute_line(f"SELECT BUFFER1G FROM BUFFER WHERE DATE='{day.date()}'")
        return self.cur.fetchall()
    # 取得10G buffer每日值
    def get_10G_buffer(self, day: int) -> tuple:
        self.execute_line(f"SELECT BUFFER10G FROM BUFFER WHERE DATE='{day.date()}'")
    ### 資料庫 class 的部分 應該可以直接用
    # def __init__(self,host,user,passwd,db,charset='utf8'):
        # 初始化 mysql 連接
        # try:
        #     self.conn = MySQLdb.connect(host=host,user=user,password=passwd,db=db)
        # except MySQLdb.Error as e:
        #     print("========= mysql connect error ==========")
        #     print(e)

    # def orderList(self):
    #     sql = "SELECT * FROM ORDERLIST ORDER BY NEEDDATE"
    #     self.cursor.execute(sql)
    #     return self.cursor.fetchall()