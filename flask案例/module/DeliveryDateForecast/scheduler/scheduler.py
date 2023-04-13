'''
目的: 處理交期排程
'''
from .DB_mysql import Mysql
from .FileProcess import read_file, draw_graph
from datetime import datetime

orderorder = ['id','need_date','number','order_date','type','delivery_date']
datenumber = ['date','number']

ll = list[list]

buffer1G: int = 0
buffer10G: int = 0
pq1G: list = []
pq10G: list = []
finish_queue: list = []

db = Mysql("0.0.0.0","pdclab","pdclab1234","orderlist",3306)


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
def show_pq(yesterday_date: str = '2022-12-24') -> dict:
    global pq1G, pq10G, buffer1G, buffer10G, finish_queue
    for element in db.get_1G_orderlist():
        l = []
        l.append(int(element[0]))
        l.append(datetime.strftime(element[1],'%Y-%m-%d'))
        l.append(int(element[2]))
        l.append(datetime.strftime(element[3],'%Y-%m-%d'))
        l.append(element[4])
        l.append(None if element[5] == None else datetime.strftime(element[5],'%Y-%m-%d'))
        if l not in pq1G:
            pq1G.append(l)
    for element in db.get_10G_orderlist():
        l = []
        l.append(int(element[0]))
        l.append(datetime.strftime(element[1],'%Y-%m-%d'))
        l.append(int(element[2]))
        l.append(datetime.strftime(element[3],'%Y-%m-%d'))
        l.append(element[4])
        l.append(None if element[5] == None else datetime.strftime(element[5],'%Y-%m-%d'))
        if l not in pq10G:
            pq10G.append(l)
    for element in db.get_finishedorder():
        l = []
        l.append(int(element[0]))
        l.append(datetime.strftime(element[1],'%Y-%m-%d'))
        l.append(int(element[2]))
        l.append(datetime.strftime(element[3],'%Y-%m-%d'))
        l.append(element[4])
        if l not in finish_queue:
            finish_queue.append(l)
    for element in db.get_buffer(fake_date):
        buffer1G = element[0]
        buffer10G = element[1]
    num_1G, num_10G = db.get_num_machine(fake_date)
    num_1G = list(num_1G)
    num_10G = list(num_10G)
    for idx in range(len(num_1G)):
        num_1G[idx] = [datetime.strftime(num_1G[idx][0],'%Y-%m-%d'), num_1G[idx][1]]
    for idx in range(len(num_10G)):
        num_10G[idx] = [datetime.strftime(num_10G[idx][0],'%Y-%m-%d'), num_10G[idx][1]]
    m_1G = []
    for i in range(len(num_1G)):
        m_1G.append({num_1G[i][0]:dict(zip(datenumber,num_1G[i]))})
    m_10G = []
    for i in range(len(num_10G)):
        m_10G.append({num_10G[i][0]:dict(zip(datenumber,num_10G[i]))})
    l_1G = []
    for i in range(len(pq1G)):
        l_1G.append({pq1G[i][0]:dict(zip(orderorder,pq1G[i]))})
    l_10G = []
    for i in range(len(pq10G)):
        l_10G.append({pq10G[i][0]:dict(zip(orderorder,pq10G[i]))})
    l_l = []
    for i in range(len(finish_queue)):
        l_l.append({finish_queue[i][0]:dict(zip(orderorder,finish_queue[i]))})
    return {'pq_1G':l_1G,'pq_10G':l_10G,'finish_queue':l_l, 'machine_num_1G':m_1G, 'machine_num_10G':m_10G}

# 插入訂單 (訂單資訊插入資料庫、pq)
## 回傳: 插入後訂單
def insert_order(param: dict, path: str=None) -> dict:
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
        return {"pq_1G":l_1G, "pq_10G":l_10G, "new_order":new_order, "machine_num_1G":None, "machine_num_10G":None}

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
    return {"pq_1G":l_1G, "pq_10G":l_10G, "new_order":new_order, "machine_num_1G":machine_num_1G, \
    "machine_num_10G":machine_num_10G}

# 刪除訂單 (訂單從資料庫、pq刪除)
## 回傳: 刪除後訂單
def delete_order(param: dict) -> dict:
    db.delete_orderlist(param=param)
    if param['type'] == '1G-POE':
        pq1G.remove(list(param.values()))
    else:
        pq10G.remove(list(param.values()))
    l_1G = []
    for i in range(len(pq1G)):
        l_1G.append({pq1G[i][0]:dict(zip(orderorder,pq1G[i]))})
    l_10G = []
    for i in range(len(pq10G)):
        l_10G.append({pq10G[i][0]:dict(zip(orderorder,pq10G[i]))})
    return {"pq_1G":l_1G,"pq_10G":l_10G}

# 每日從csv中讀取機台產量 (機台資訊塞進資料庫、增加前一天的生產量到buffer、檢查是否完成訂單、buffer寫回資料庫)
## 回傳: 所有已完成訂單list of list
def get_daily_total(path: str, yesterday_date: str = '2022-12-24') -> dict:
    global buffer1G, buffer10G, finish_queue
    db.delete_all_product()
    df = read_file(path=path)
    for row in df.itertuples():
        db.insert_product(row=row)
    for p in db.get_1G_production(yesterday_date):
        buffer1G += p[0]
    for p in db.get_10G_production(yesterday_date):
        buffer10G += p[0]
    while(len(pq1G)!=0 and buffer1G >= pq1G[0][2]):
        finish_queue.append(finish_order('1G-POE'))
    while(len(pq10G)!=0 and buffer10G >= pq10G[0][2]):
        finish_queue.append(finish_order('10G'))
    db.update_buffer(yesterday_date,buffer1G,buffer10G)
    
    num_1G, num_10G = db.get_num_machine(yesterday_date)
    num_1G = list(num_1G)
    num_10G = list(num_10G)
    for idx in range(len(num_1G)):
        num_1G[idx] = [datetime.strftime(num_1G[idx][0],'%Y-%m-%d'), num_1G[idx][1]]
    for idx in range(len(num_10G)):
        num_10G[idx] = [datetime.strftime(num_10G[idx][0],'%Y-%m-%d'), num_10G[idx][1]]
    m_1G = []
    for i in range(len(num_1G)):
        m_1G.append({num_1G[i][0]:dict(zip(datenumber,num_1G[i]))})
    m_10G = []
    for i in range(len(num_10G)):
        m_10G.append({num_10G[i][0]:dict(zip(datenumber,num_10G[i]))})
    l_1G = []
    for i in range(len(pq1G)):
        l_1G.append({pq1G[i][0]:dict(zip(orderorder,pq1G[i]))})
    l_10G = []
    for i in range(len(pq10G)):
        l_10G.append({pq10G[i][0]:dict(zip(orderorder,pq10G[i]))})
    l_l = []
    for i in range(len(finish_queue)):
        l_l.append({finish_queue[i][0]:dict(zip(orderorder,finish_queue[i]))})
    return {'pq_1G':l_1G,'pq_10G':l_10G,'finish_queue':l_l, 'machine_num_1G':m_1G, 'machine_num_10G':m_10G}

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

    
