'''
目的: 處理交期排程
'''
from .DB_mysql import Mysql
from .FileProcess import read_production, draw_graph
from datetime import datetime

orderorder = ['need_date','number','order_date','type']

ll = list[list]

buffer1G: int = 0
buffer10G: int = 0
pq: list = []
finish_queue: list = []

db = Mysql("localhost","pdcuser","pdclab1234","orderlist")


fake_date = "2022-12-24"

# 回傳: Buffer1G
def get_buffer1G() -> int:
    return buffer1G

# 回傳: Buffer10G
def get_buffer10G() -> int:
    return buffer10G

# 回傳: pq
def get_pq() -> list:
    return pq

# 回傳: finish_queue
def get_finish_queue() -> list:
    return finish_queue

# 重新開啟網頁時使用(資料庫讀出訂單、buffer值)
## 回傳: 訂單
def show_pq(yesterday_date: str = '2022-12-24') -> ll:
    global pq, buffer1G, buffer10G, finish_queue
    for element in db.get_orderlist():
        l = []
        l.append(datetime.strftime(element[0],'%Y-%m-%d'))
        l.append(int(element[1]))
        l.append(datetime.strftime(element[2],'%Y-%m-%d'))
        l.append(element[3])
        pq.append(l)
    for element in db.get_finishedorder():
        l = []
        l.append(datetime.strftime(element[0],'%Y-%m-%d'))
        l.append(int(element[1]))
        l.append(datetime.strftime(element[2],'%Y-%m-%d'))
        l.append(element[3])
        finish_queue.append(l)
    for element in db.get_buffer(fake_date):
        buffer1G = element[0]
        buffer10G = element[1]
    l = []
    for i in range(len(pq)):
        l.append(dict(zip(orderorder,pq[i])))
    l_l = []
    for i in range(len(finish_queue)):
        l_l.append(dict(zip(orderorder,finish_queue[i])))
    return {'pq':l,'finish_queue':l_l}

# 插入訂單 (訂單資訊插入資料庫、pq)
## 回傳: 插入後訂單
def insert_order(param: dict) -> dict:
    db.insert_orderlist(param=param)
    pq.append(list(param.values()))
    pq.sort(key=lambda p:p[0])
    l = []
    for i in range(len(pq)):
        l.append(dict(zip(orderorder,pq[i])))
    return {"pq":l}

# 刪除訂單 (訂單從資料庫、pq刪除)
## 回傳: 刪除後訂單
def delete_order(param: dict) -> ll:
    db.delete_orderlist(param=param)
    pq.remove(list(param.values()))
    l = []
    for i in range(len(pq)):
        l.append(dict(zip(orderorder,pq[i])))
    return {"pq":l}

# 每日從csv中讀取機台產量 (機台資訊塞進資料庫、增加前一天的生產量到buffer、檢查是否完成訂單、buffer寫回資料庫)
## 回傳: 所有已完成訂單list of list
def get_daily_total(path: str, yesterday_date: str = '2022-12-26') -> ll:
    global buffer1G
    global buffer10G
    db.delete_all_product()
    df = read_production(path=path)
    for row in df.itertuples():
        db.insert_product(row=row)
    for p in db.get_1G_production(yesterday_date=fake_date):
        buffer1G += p[0]
    for p in db.get_10G_production(yesterday_date=fake_date):
        buffer10G += p[0]
    finish: list = []
    while(len(pq)!=0 and buffer1G >= pq[0][3] and pq[0][2]=='1G-POE'):
        finish.append(finish_order())
    while(len(pq)!=0 and buffer10G >= pq[0][3] and buffer10G >= pq[0][2]=='10G'):
        finish.append(finish_order())
    db.update_buffer(yesterday_date=fake_date,buffer1G=buffer1G,buffer10G=buffer10G)
    return finish

# 處理已完成訂單 (減少buffer量、從資料庫和pq刪除訂單)
## 回傳: 一筆已完成訂單list
def finish_order() -> list:
    global buffer1G
    global buffer10G
    finish: list = []
    if(pq[0][2]=='1G-POE'):
        buffer1G -= int(pq[0][3])
    elif(pq[0][2]=='10G'):
        buffer10G -= int(pq[0][3])
    db.insert_finishedorder(pq=pq)
    db.delete_orderlist(param=pq)
    finish = pq.pop(0)
    return finish

# 繪製1G機台每日產量圖
## 圖片存成jpg
def draw_1G_graph(start_date: str, end_date: str) -> None:
    draw_graph(start_date, end_date, db, '1G-POE_production', "1G production")

# 繪製10G機台每日產量圖
## 圖片存成jpg
def draw_10G_graph(start_date: str, end_date: str) -> None:
    draw_graph(start_date, end_date, db, '10G_production', "10G production")

# 繪製1G buffer每日剩餘圖
## 圖片存成jpg
def draw_buffer1G_graph(start_date: str, end_date: str) -> None:
    draw_graph(start_date, end_date, db, '1G-POE_buffer', "1G buffer")

# 繪製10G buffer每日剩餘圖
## 圖片存成jpg
def draw_buffer10G_graph(start_date: str, end_date: str) -> None:
    draw_graph(start_date, end_date, db, '10G_buffer', "10G buffer")