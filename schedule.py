import MySQLdb
from datetime import datetime
import pandas as pd

buffer1G : int = 0
buffer10G : int = 0
pq : list = []
# [needdate,orderdate,type,number]

# 重新開啟網頁時使用
def show_pq():
    global pq
    db = MySQLdb.connect(host="localhost",user="pdcuser",password="pdclab1234",db="orderlist")
    cur = db.cursor()
    cur.execute("SELECT * FROM ORDERLIST ORDER BY NEEDDATE")
    for element in cur.fetchall():
        l = []
        l.append(datetime.strftime(element[0],'%Y-%m-%d'))
        l.append(datetime.strftime(element[1],'%Y-%m-%d'))
        l.append(element[2])
        l.append(int(element[3]))
        pq.append(l)
    db.commit()
    db.close()
    return pq

def insert_order(param:list):
    db = MySQLdb.connect(host="localhost",user="pdcuser",password="pdclab1234",db="orderlist")
    cur = db.cursor()
    # print(f"INSERT INTO ORDERLIST VALUES('{param[0]}','{param[1]}','{param[2]}',{param[3]})")
    cur.execute(f"INSERT INTO ORDERLIST VALUES('{param[0]}','{param[1]}','{param[2]}',{param[3]})")
    db.commit()
    db.close()
    pq.append(param)
    pq.sort(key=lambda p:p[0])
    return pq

def delete_order(param:list):
    db = MySQLdb.connect(host="localhost",user="pdcuser",password="pdclab1234",db="orderlist")
    cur = db.cursor()
    cur.execute(f"DELETE FROM ORDERLIST WHERE NEEDDATE='{param[0]}' AND ORDERDATE='{param[1]}' AND TYPE='{param[2]}' AND NUMBER={param[3]}")
    db.commit()
    db.close()
    pq.remove(param)
    return pq

# def update_order(param:list, key:str, value:str):
#     db = MySQLdb.connect(host="localhost",user="pdcuser",password="pdclab1234",db="orderlist")
#     cur = db.cursor()
#     cur.execute("UPDATE ORDERLIST SET ")

def get_daily_total(path:str, today_date:str):
    global buffer1G
    global buffer10G
    df = pd.read_csv(f"{path}",encoding='big5')
    df06=df.loc[(df['機台號']=="h06") & (df['生產日期']==f"{today_date}")]
    df14=df.loc[(df['機台號']=="h14") & (df['生產日期']==f"{today_date}")]

    df01=df.loc[(df['機台號']=="h01") & (df['生產日期']==f"{today_date}") & (df['班別']=='D')]
    df02=df.loc[(df['機台號']=="h02") & (df['生產日期']==f"{today_date}") & (df['班別']=='D')]
    df08=df.loc[(df['機台號']=="h08") & (df['生產日期']==f"{today_date}") & (df['班別']=='D')]
    df10=df.loc[(df['機台號']=="h10") & (df['生產日期']==f"{today_date}") & (df['班別']=='D')]
    df15=df.loc[(df['機台號']=="h15") & (df['生產日期']==f"{today_date}") & (df['班別']=='D')]
    df19=df.loc[(df['機台號']=="h19") & (df['生產日期']==f"{today_date}") & (df['班別']=='D')]
    df1G = int((sum(df06["產能"])+sum(df14["產能"]))/2)
    df10G = int((sum(df01["產能"])+sum(df02["產能"])+sum(df08["產能"])+sum(df10["產能"])+sum(df15["產能"])+sum(df19["產能"]))/2)
    buffer1G += df1G
    buffer10G += df10G
    while(len(pq)!=0 and buffer1G >= pq[0][3] and pq[0][2]=='1G-POE'):
        finish_order()
    while(len(pq)!=0 and buffer10G >= pq[0][3] and buffer10G >= pq[0][2]=='10G'):
        finish_order()
    return

def finish_order():
    global buffer1G
    global buffer10G
    db = MySQLdb.connect(host="localhost",user="pdcuser",password="pdclab1234",db="orderlist")
    cur = db.cursor()
    if(pq[0][2]=='1G-POE'):
        buffer1G -= int(pq[0][3])
    elif(pq[0][2]=='10G'):
        buffer10G -= int(pq[0][3])
    cur.execute(f"DELETE FROM ORDERLIST WHERE NEEDDATE='{pq[0][0]}' AND ORDERDATE='{pq[0][1]}' AND TYPE='{pq[0][2]}' AND NUMBER={pq[0][3]}")
    db.commit()
    db.close()
    pq.pop(0)
    return


# test code

# while(True):
#     command = input("Action: ")
#     if(command=='1'):
#         show_pq()
#     elif(command=='2'):
#         l=input("list: ").split(" ")
#         insert_order(l)
#     elif(command=='3'):
#         l=input("list: ").split(" ")
#         delete_order(l)
#     elif(command=='4'):
#         path,date=input("path&date: ").split(" ")
#         get_daily_total(path=path,today_date=date)
#     print(f"pq:{pq}")
#     print(f"buffer1G: {buffer1G}")
#     print(f"buffer10G: {buffer10G}")