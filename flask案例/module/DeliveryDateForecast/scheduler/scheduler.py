'''
目的: 處理交期排程
- API包裝
'''
import threading
from .DB_mysql import Mysql
from .FileProcess import read_file
from datetime import datetime, timedelta, timezone

orderorder = ['id','need_date','number','order_date','type','delivery_date']
datenumber = ['date','number']

ll = list[list]

buffer1G: int = 0
buffer10G: int = 0
pq1G: list = []
pq10G: list = []
finish_queue: list = []

db = Mysql("0.0.0.0","pdclab","pdclab1234","orderlist",3306)

today_date_unformated = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
yesterday_date = datetime.strftime(today_date_unformated-timedelta(days=1),'%Y-%m-%d')

# 回傳: Buffer1G
def get_buffer1G() -> int:
    return buffer1G

# 回傳: Buffer10G
def get_buffer10G() -> int:
    return buffer10G

# 回傳: finish_queue
def get_finish_queue() -> list:
    return finish_queue

# 重新開啟網頁時使用(資料庫讀出訂單、buffer值)
# mode初始為1
## 回傳: 訂單
def show_pq() -> dict:
    global pq1G, pq10G, finish_queue, buffer1G, buffer10G
    pq1G.clear()
    pq10G.clear()
    finish_queue.clear()
    for element in db.get_1G_orderlist():
        l = []
        l.append(int(element[0]))
        l.append(datetime.strftime(element[1],'%Y-%m-%d'))
        l.append(int(element[2]))
        l.append(datetime.strftime(element[3],'%Y-%m-%d'))
        l.append(element[4])
        l.append(None if element[5] == None else datetime.strftime(element[5],'%Y-%m-%d'))
        pq1G.append(l)
    for element in db.get_10G_orderlist():
        l = []
        l.append(int(element[0]))
        l.append(datetime.strftime(element[1],'%Y-%m-%d'))
        l.append(int(element[2]))
        l.append(datetime.strftime(element[3],'%Y-%m-%d'))
        l.append(element[4])
        l.append(None if element[5] == None else datetime.strftime(element[5],'%Y-%m-%d'))
        pq10G.append(l)
    for element in db.get_finishedorder():
        l = []
        l.append(int(element[0]))
        l.append(datetime.strftime(element[1],'%Y-%m-%d'))
        l.append(int(element[2]))
        l.append(datetime.strftime(element[3],'%Y-%m-%d'))
        l.append(element[4])
        finish_queue.append(l)
    for element in db.get_buffer(yesterday_date):
        buffer1G = element[0]
        buffer10G = element[1]
    l_1G = []
    for i in range(len(pq1G)):
        l_1G.append({pq1G[i][0]:dict(zip(orderorder,pq1G[i]))})
    l_10G = []
    for i in range(len(pq10G)):
        l_10G.append({pq10G[i][0]:dict(zip(orderorder,pq10G[i]))})
    l_l = []
    for i in range(len(finish_queue)):
        l_l.append({finish_queue[i][0]:dict(zip(orderorder,finish_queue[i]))})
    return {'pq_1G':l_1G,'pq_10G':l_10G,'finish_queue':l_l, 'machine_num_1G':None, 'machine_num_10G':None, "mode":1}

# 插入訂單 (訂單資訊插入資料庫、pq)
## 回傳: 插入後訂單
def insert_order(param: dict, path: str=None) -> dict:
    global pq1G, pq10G
    return_id = db.insert_orderlist(param=param)
    if return_id != 0:
        if param['type'] == '1G-POE':
            pq1G.append([return_id]+list(param.values()))
            pq1G.sort(key=lambda p:p[1])
        else:
            pq10G.append([return_id]+list(param.values()))
            pq10G.sort(key=lambda p:p[1])
    l_1G = []
    for i in range(len(pq1G)):
        l_1G.append({pq1G[i][0]:dict(zip(orderorder,pq1G[i]))})
    l_10G = []
    for i in range(len(pq10G)):
        l_10G.append({pq10G[i][0]:dict(zip(orderorder,pq10G[i]))})
    new_order = {"id":return_id}
    new_order.update(param)
    if path == None:
        return {"pq_1G":l_1G, "pq_10G":l_10G, "new_order":new_order, "machine_num_1G":None, "machine_num_10G":None, "mode":1}

# 刪除訂單 (訂單從資料庫、pq刪除)
## 回傳: 刪除後訂單
def delete_order(param: dict) -> dict:
    global pq1G, pq10G
    db.delete_orderlist(param=param)
    pq1G.clear()
    pq10G.clear()
    for element in db.get_1G_orderlist():
        l = []
        l.append(int(element[0]))
        l.append(datetime.strftime(element[1],'%Y-%m-%d'))
        l.append(int(element[2]))
        l.append(datetime.strftime(element[3],'%Y-%m-%d'))
        l.append(element[4])
        l.append(None if element[5] == None else datetime.strftime(element[5],'%Y-%m-%d'))
        pq1G.append(l)
    for element in db.get_10G_orderlist():
        l = []
        l.append(int(element[0]))
        l.append(datetime.strftime(element[1],'%Y-%m-%d'))
        l.append(int(element[2]))
        l.append(datetime.strftime(element[3],'%Y-%m-%d'))
        l.append(element[4])
        l.append(None if element[5] == None else datetime.strftime(element[5],'%Y-%m-%d'))
        pq10G.append(l)
    l_1G = []
    for i in range(len(pq1G)):
        l_1G.append({pq1G[i][0]:dict(zip(orderorder,pq1G[i]))})
    l_10G = []
    for i in range(len(pq10G)):
        l_10G.append({pq10G[i][0]:dict(zip(orderorder,pq10G[i]))})
    return {"pq_1G":l_1G, "pq_10G":l_10G, "mode":1}

# 換模式前都要先經過add_limit轉換資料
def add_limit(path: str=None) -> dict:
    if path == None:
        return {"machine_num_1G":None, "machine_num_10G":None}
    machine_num_list_1G = []
    machine_num_list_10G = []
    df = read_file(path=path)
    for row in df.itertuples():
        if getattr(row,'product') == '1G-POE':
            machine_num_list_1G.append([datetime.strptime(getattr(row,'date'),"%Y/%m/%d").strftime("%Y-%m-%d"), getattr(row,'number')])
        else:
            machine_num_list_10G.append([datetime.strptime(getattr(row,'date'),"%Y/%m/%d").strftime("%Y-%m-%d"), getattr(row,'number')])
    machine_num_1G = []
    machine_num_10G = []
    for i in range(len(machine_num_list_1G)):
        machine_num_1G.append({machine_num_list_1G[i][0]:dict(zip(datenumber,machine_num_list_1G[i]))})
    for i in range(len(machine_num_list_10G)):
        machine_num_10G.append({machine_num_list_10G[i][0]:dict(zip(datenumber,machine_num_list_10G[i]))})
    print("machine",machine_num_1G)
    return {"machine_num_1G":machine_num_1G, "machine_num_10G":machine_num_10G}

def insert_product_thread(row: dict) -> None:
    db = Mysql("0.0.0.0","pdclab","pdclab1234","orderlist",3306)
    for param in row.itertuples():
        db.insert_product(param)
    return

# 每日從csv中讀取機台產量 (機台資訊塞進資料庫、增加前一天的生產量到buffer、檢查是否完成訂單、buffer寫回資料庫)
## 回傳: 所有已完成訂單list of list
def get_daily_total(path: str, yesterday_date: str = yesterday_date) -> dict:
    global buffer1G, buffer10G, finish_queue
    threads: list = []
    db.delete_all_product()
    df = read_file(path=path)
    for index in range(0, len(df.index), 60):
        threads.append(threading.Thread(target = insert_product_thread, args = (df.loc[index:index+59],)))
        threads[index//60].start()
    for i in range(len(threads)):
        threads[i].join()
    for p in db.get_1G_production(yesterday_date):
        buffer1G += p[0]
        print(buffer1G)
    for p in db.get_10G_production(yesterday_date):
        buffer10G += p[0]
        print(buffer10G)
    while(len(pq1G)!=0 and buffer1G >= pq1G[0][2]):
        finish_queue.append(finish_order('1G-POE'))
    while(len(pq10G)!=0 and buffer10G >= pq10G[0][2]):
        finish_queue.append(finish_order('10G'))
    db.update_buffer(yesterday_date,buffer1G,buffer10G)
    l_1G = []
    for i in range(len(pq1G)):
        l_1G.append({pq1G[i][0]:dict(zip(orderorder,pq1G[i]))})
    l_10G = []
    for i in range(len(pq10G)):
        l_10G.append({pq10G[i][0]:dict(zip(orderorder,pq10G[i]))})
    l_l = []
    for i in range(len(finish_queue)):
        l_l.append({finish_queue[i][0]:dict(zip(orderorder,finish_queue[i]))})
    return {'pq_1G':l_1G,'pq_10G':l_10G,'finish_queue':l_l, 'machine_num_1G':None, 'machine_num_10G':None,"mode":1}

# 處理已完成訂單 (減少buffer量、從資料庫和pq刪除訂單)
## 回傳: 一筆已完成訂單list
def finish_order(type: str) -> list:
    global buffer1G, buffer10G, pq1G, pq10G
    finish: list = []
    if(type=='1G-POE'):
        buffer1G -= pq1G[0][2]
        db.insert_finishedorder(pq=pq1G[0])
        db.delete_orderlist(param={'id':pq1G[0][0], 'need_date':pq1G[0][1], 'number':pq1G[0][2], 'order_date':pq1G[0][3], 'type':pq1G[0][4]})
        finish = pq1G.pop(0)
    elif(type=='10G'):
        buffer10G -= pq10G[0][2]
        db.insert_finishedorder(pq=pq10G[0])
        db.delete_orderlist(param={'id':pq10G[0][0], 'need_date':pq10G[0][1], 'number':pq10G[0][2], 'order_date':pq10G[0][3], 'type':pq10G[0][4]})
        finish = pq10G.pop(0)
    return finish

# 取得每日機台產量
## 回傳: 每日各機台產量
def get_daily_product_sum() -> tuple:
    sum_1G, sum_10G = [list(x) for x in db.get_daily_production_sum()]
    for idx in range(len(sum_1G)):
        sum_1G[idx] = [datetime.strftime(sum_1G[idx][0],'%Y-%m-%d'),int(sum_1G[idx][1])]
        sum_10G[idx] = [datetime.strftime(sum_10G[idx][0],'%Y-%m-%d'),int(sum_10G[idx][1])]
    l = []
    for i in range(len(sum_1G)):
        l.append(dict(zip(datenumber,sum_1G[i])))
    l_l = []
    for i in range(len(sum_10G)):
        l_l.append(dict(zip(datenumber,sum_10G[i])))
    return {'1G-POE':l}, {'10G':l_l}

# 尋找特定ID的訂單
## 回傳: 訂單資訊
def find_order(ID: int) -> tuple:
    if len(db.search_order(ID)) == 0:
        return {}
    result = db.search_order(ID)[0]
    return_tuple = (result[0], datetime.strftime(result[1],'%Y-%m-%d'), result[2], datetime.strftime(result[3],'%Y-%m-%d'), result[4], None if result[5] == None else datetime.strftime(result[5],'%Y-%m-%d'))
    return dict(zip(orderorder, return_tuple))

def update_delivery(params: tuple) -> None:
    for param in params['pq_1G']:
        for paramvalue in param.values():
            db.update_delivery_date(paramvalue)
    for param in params['pq_10G']:
        for paramvalue in param.values():
            db.update_delivery_date(paramvalue)
    return