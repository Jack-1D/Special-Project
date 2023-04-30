import json
from .ProcessDataX10G import *
from .ProcessDataX1G import *
import datetime
import pytz
import time

X10G_mean = getX10G_design_weight_mean()
X10G_len = getX10G_len()
X1G_mean = getX1G_design_weight_mean()
X1G_len = getX1G_len()
X10G_buffer = 0
X1G_buffer = 0
mode = 1
factor = 700 #設置future_machine_list有多長
X10G_max_machine_num = 6
X1G_max_machine_num = 9
X10G_cycle = 1 #10G只有日班
X1G_cycle = 2   #1G有日、夜班
X10G_oneday_max_production = X10G_mean*X10G_max_machine_num*X10G_cycle
X1G_oneday_max_production = X1G_mean*X1G_max_machine_num*X1G_cycle
threshold_day = 2 # mode2 mode3 距離需求日threshold

#設置today
def setToday():
    tz = pytz.timezone('Asia/Taipei')
    dt = datetime.datetime.fromtimestamp(time.time(), tz)
    today = dt.date()
    return today

today = setToday()

#模式選擇函數
def ChooseMode(new_mode):
    global mode
    if  new_mode == 1 : #mode 1 交期平均最短，機台全開
        mode = new_mode
    elif new_mode == 2: #mode 2 機台使用數最少並且訂單符合預定交期，機台使用無限制
        mode = new_mode
    elif new_mode == 3: #mode 3 機台使用數最少並且訂單符合預定交期，機台使用有限制
        mode = new_mode
    else:
        print('error')

#切割need_date函數，回傳年，月，日(type = int)
def SplitNeedDate(need_date):
    year = int(need_date[0:4])
    month = int(need_date[5:7])
    day = int(need_date[8:10])
    return year, month, day

#Mode2 若當日機台數滿了 填入下一天
def FillNextDay_Mode2(i, future_machine_list, max_machine_num):
    if future_machine_list[i + 1] < max_machine_num:
        future_machine_list[i + 1] = future_machine_list[i + 1] + 1
    else:
        FillNextDay_Mode2(i + 1, future_machine_list, max_machine_num)

# Mode3 若當日機台數滿了 往後填
def FillNextDay_Mode3(i, future_machine_list, future_machine_limit_list, final_index):
    if future_machine_list[i + 1] < list(future_machine_limit_list[i + 1].values())[0]['number']:
        if i+1 > final_index:
            final_index = i + 1
        future_machine_list[i + 1] = future_machine_list[i + 1] + 1
        return final_index
    else:
        return FillNextDay_Mode3(i + 1, future_machine_list, future_machine_limit_list, final_index)

#Mode3 若當日機台數滿了 往前填
def FillBeforeDay_Mode3(i, future_machine_list, future_machine_limit_list, final_index):
    for j in range(0, i):
        if future_machine_list[j] < list(future_machine_limit_list[j].values())[0]['number']:
            future_machine_list[j] = future_machine_list[j] + 1
            if j > final_index:
                final_index = j
            return final_index
    return FillNextDay_Mode3(i, future_machine_list, future_machine_limit_list, final_index)    #前面也都滿了，填入下一天

#Mode2填補未來需要的機台數
def FillUnit_Mode2(need_unit, future_machine_list, type, begin_index, end_index):
    if(type == "1G-POE"):
        max_machine_num = X1G_max_machine_num
    elif(type == "10G"):
        max_machine_num = X10G_max_machine_num
    while need_unit > 0:
        for i in range(begin_index, end_index):
            if need_unit <=0:
                begin_index = i
                break
            if future_machine_list[i] < max_machine_num:
                future_machine_list[i] = future_machine_list[i] + 1
            else:
                FillNextDay_Mode2(i, future_machine_list, max_machine_num)  #前面都填滿了，填入下一天，前面一定都是滿的
            need_unit = need_unit -1
        if(need_unit != 0):
            begin_index = 0
    return begin_index

#Mode3填補未來需要的機台數，並有每日機台上線
def FillUnit_Mode3(need_unit, future_machine_list, future_machine_limit_list, begin_index, end_index, final_index):
    while need_unit > 0:
        for i in range(begin_index, end_index):
            if need_unit <=0:
                begin_index = i
                break
            if future_machine_list[i] < list(future_machine_limit_list[i].values())[0]['number']:
                if i > final_index:
                    final_index = i
                future_machine_list[i] = future_machine_list[i] + 1
            else:
                final_index = FillBeforeDay_Mode3(i, future_machine_list, future_machine_limit_list, final_index)  #當天填滿，往前找是否有空缺，否則填入下一天，
            need_unit = need_unit -1
        if(need_unit !=0):
            begin_index = 0
    return begin_index, final_index

# 計算交期
def ComputeDeliveryDate(future_machine_list, order_need_unit_list):
    buffer = 0
    deliverydate_list = [0]*len(order_need_unit_list)
    tmp_index = 0   #當前檢查到哪裡
    for i in range(0, len(deliverydate_list)):
        for j in range(tmp_index, len(future_machine_list)):
            if buffer >= order_need_unit_list[i]:
                buffer = buffer - order_need_unit_list[i]
                delivery_date = today + datetime.timedelta(days=j)
                deliverydate_list[i] = f'{delivery_date}'
                tmp_index = j
                break
            else:
                buffer = buffer + future_machine_list[j]
                if buffer >= order_need_unit_list[i]:
                    buffer = buffer - order_need_unit_list[i]
                    delivery_date = today + datetime.timedelta(days=j + 1)  #下一日才能出貨
                    tmp_index = j + 1
                    deliverydate_list[i] = f'{delivery_date}'
                    break
    return deliverydate_list         

#mode 1
def UseMode1(data):
    Output = {
        'pq_1G': [],
        'pq_10G': [],
        'new_order':{},
        'machine_num_need_1G':[],
        'machine_num_need_10G' :[],
        }
    #1G預測
    tmp_buffer_1G = 0 #用來放滿足當前訂單還剩下多少
    day_begin_1G = 0 #訂單開始生產距離今天幾天
    day_end_1G = 0   #訂單結束生產距離今天幾天
    for order in data['pq_1G']:
        value = list(order.values())[0]
        year, month , day = SplitNeedDate(value['need_date'])
        need_date = datetime.date(year, month, day)
        need_production = value['number']
        need_day = int(((need_production - tmp_buffer_1G)/(X1G_oneday_max_production)) + 1) #需要幾天生產，補齊1天 +1
        day_begin_1G = day_end_1G
        day_end_1G = day_begin_1G + need_day
        tmp_buffer_1G = int((need_day*X1G_oneday_max_production + tmp_buffer_1G) - need_production) #滿足訂單後還剩下多少多的
        delivery_date = today + datetime.timedelta(days=day_end_1G)
        tmpOrder = {
            value['id']: {
                'id': value['id'],
                'need_date': value['need_date'],
                'number': value['number'],
                'order_date': value['order_date'],
                'type': value['type'],
                'delivery_date': f'{delivery_date}',
                'status':True
            }
        }
        if delivery_date > need_date:   #超出需求日
            tmpOrder[value['id']]['status'] = False
        Output['pq_1G'].append(tmpOrder)    #所有1G的訂單預測交期加入pq_1G
        if data.get('new_order') == None:
            continue
        if len(data.get('new_order')) != 0:
            if value['id'] == data['new_order']['id']:    #如果當前訂單是新訂單，另外存在new_order
                Output['new_order']= {
                    'id': value['id'],
                    'need_date': value['need_date'],
                    'number': value['number'],
                    'order_date': value['order_date'],
                    'type': value['type'],
                    'delivery_date': f'{delivery_date}'
                }
    #10G預測
    tmp_buffer_10G = 0 #用來放滿足當前訂單還剩下多少
    day_begin_10G = 0 #訂單開始生產距離今天幾天
    day_end_10G = 0   #訂單結束生產距離今天幾天
    for order in data['pq_10G']:
        value = list(order.values())[0]
        year, month , day = SplitNeedDate(value['need_date'])
        need_date = datetime.date(year, month, day)
        need_production = value['number']
        need_day = int(((need_production - tmp_buffer_10G)/(X10G_oneday_max_production)) + 1) #需要幾天生產，補齊1天 +1
        day_begin_10G = day_end_10G
        day_end_10G = day_begin_10G + need_day
        tmp_buffer_10G = int((need_day*X10G_oneday_max_production + tmp_buffer_10G) - need_production)  #滿足訂單後還剩下多少多的
        delivery_date = today + datetime.timedelta(days=day_end_10G)
        tmpOrder = {
            value['id']: {
                'id': value['id'],
                'need_date': value['need_date'],
                'number': value['number'],
                'order_date': value['order_date'],
                'type': value['type'],
                'delivery_date': f'{delivery_date}',
                'status':True
            }
        }
        if delivery_date > need_date:   #超出需求日
            tmpOrder[value['id']]['status'] = False
        Output['pq_10G'].append(tmpOrder)   #所有10G的訂單預測交期加入pq_10G
        if data.get('new_order') == None:
            continue
        if len(data.get('new_order')) != 0:
            if value['id'] == data['new_order']['id']:    #如果當前訂單是新訂單，另外存在new_order
                Output['new_order']= {
                    'id': value['id'],
                    'need_date': value['need_date'],
                    'number': value['number'],
                    'order_date': value['order_date'],
                    'type': value['type'],
                    'delivery_date': f'{delivery_date}'
                }
    #機台數
    if len(data['pq_1G']) >0:
        value = list(Output['pq_1G'][-1].values())[0]
        year, month , day = SplitNeedDate(value['delivery_date'])
        last_delivery_date = datetime.date(year, month, day)
        for i in range(0, (last_delivery_date - today).days):
            date = (today + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            tmpNum = {
                date: {
                    'date': date,
                    'number': X1G_max_machine_num
                }
            }
            Output['machine_num_need_1G'].append(tmpNum)

    if len(data['pq_10G']) >0:
        value = list(Output['pq_10G'][-1].values())[0]
        year, month , day = SplitNeedDate(value['delivery_date'])
        last_delivery_date = datetime.date(year, month, day)
        for i in range(0, (last_delivery_date - today).days):
            date = (today + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            tmpNum = {
                date: {
                    'date': date,
                    'number': X10G_max_machine_num
                }
            }
            Output['machine_num_need_10G'].append(tmpNum)
    return Output

#mode 2
def UseMode2(data):
    Output = {
        'pq_1G': [],
        'pq_10G': [],
        'new_order':{},
        'machine_num_need_1G':[],
        'machine_num_need_10G' :[],
        }
    #1G預測
    tmp_buffer_1G = 0 #用來放滿足當前訂單還剩下多少
    if(len(data['pq_1G']) > 0):
        year, month, day = SplitNeedDate(list(data['pq_1G'][-1].values())[0]['need_date'])
        last_need_date = datetime.date(year, month, day)
        total_day = (last_need_date - today).days
        future_machine_need_list_1G = [0]*factor  
        order_need_unit_list_1G = [0]*len(data['pq_1G'])
        begin_index_1G = 0
        for order in data['pq_1G']:
            value = list(order.values())[0]
            year, month , day = SplitNeedDate(value['need_date'])
            need_date = datetime.date(year, month, day)
            need_production = value['number']
            need_unit = int(((need_production - tmp_buffer_1G)/(X1G_mean*X1G_cycle)) + 1) #需要幾天生產，補齊1天 + 1
            tmp_buffer_1G = int((need_unit*X1G_mean*X1G_cycle + tmp_buffer_1G) - need_production) #滿足訂單後還剩下多少多的
            order_need_unit_list_1G[data['pq_1G'].index(order)] = need_unit
            if (need_date - today).days - threshold_day > 0:
                end_index_1G = (need_date - today).days - threshold_day   #最多可以填到future_machine_need_list_1G的哪個index(不包含)
            elif (need_date - today).days <= 0:
                end_index_1G = 1
            else:
                end_index_1G = (need_date - today).days
            begin_index_1G = FillUnit_Mode2(need_unit, future_machine_need_list_1G, value['type'], begin_index_1G , end_index_1G)   #填滿unit，並回傳下次要從哪裡開始填
        
        delivery_date_list_1G = ComputeDeliveryDate(future_machine_need_list_1G, order_need_unit_list_1G)
        for order in data['pq_1G']:
            value = list(order.values())[0]
            order_index = data['pq_1G'].index(order)
            year, month, day = SplitNeedDate(delivery_date_list_1G[order_index])
            delivery_date = datetime.date(year, month, day)
            year, month , day = SplitNeedDate(value['need_date'])
            need_date = datetime.date(year, month, day)
            tmpOrder = {
                value['id']: {
                    'id': value['id'],
                    'need_date': value['need_date'],
                    'number': value['number'],
                    'order_date': value['order_date'],
                    'type': value['type'],
                    'delivery_date': f'{delivery_date}',
                    'status':True
                }
            }
            if delivery_date > need_date:   #超出需求日
                tmpOrder[value['id']]['status'] = False
            Output['pq_1G'].append(tmpOrder)    #所有1G的訂單預測交期加入pq_1G
            if data.get('new_order') == None:
                continue
            if len(data.get('new_order')) != 0:
                if value['id'] == data['new_order']['id']:    #如果當前訂單是新訂單，另外存在new_order
                    Output['new_order']= {
                        'id': value['id'],
                        'need_date': value['need_date'],
                        'number': value['number'],
                        'order_date': value['order_date'],
                        'type': value['type'],
                        'delivery_date': f'{delivery_date}'
                    }
    #10G預測
    tmp_buffer_10G = 0 #用來放滿足當前訂單還剩下多少
    if(len(data['pq_10G']) > 0):
        year, month, day = SplitNeedDate(list(data['pq_10G'][-1].values())[0]['need_date'])
        last_need_date = datetime.date(year, month, day)
        total_day = (last_need_date - today).days
        future_machine_need_list_10G = [0]*factor  #開五倍用來處理可能會超出需求日的問題
        order_need_unit_list_10G = [0]*len(data['pq_10G'])
        begin_index_10G = 0
        for order in data['pq_10G']:
            value = list(order.values())[0]
            year, month , day = SplitNeedDate(value['need_date'])
            need_date = datetime.date(year, month, day)
            need_production = value['number']
            need_unit = int(((need_production - tmp_buffer_10G)/(X10G_mean*X10G_cycle)) + 1) #需要幾天生產，補齊1天 + 1
            tmp_buffer_10G = int((need_unit*X10G_mean*X10G_cycle + tmp_buffer_10G) - need_production) #滿足訂單後還剩下多少多的
            order_need_unit_list_10G[data['pq_10G'].index(order)] = need_unit
            if (need_date - today).days - threshold_day > 0:
                end_index_10G = (need_date - today).days - threshold_day   #最多可以填到future_machine_need_list_10G的哪個index(不包含)
            elif (need_date - today).days <= 0:
                end_index_10G = 1
            else:
                end_index_10G = (need_date - today).days
            begin_index_10G = FillUnit_Mode2(need_unit, future_machine_need_list_10G, value['type'], begin_index_10G , end_index_10G)   #填滿unit，並回傳下次要從哪裡開始填

        delivery_date_list_10G = ComputeDeliveryDate(future_machine_need_list_10G, order_need_unit_list_10G)
        for order in data['pq_10G']:
            value = list(order.values())[0]
            order_index = data['pq_10G'].index(order)
            year, month, day = SplitNeedDate(delivery_date_list_10G[order_index])
            delivery_date = datetime.date(year, month, day)
            year, month , day = SplitNeedDate(value['need_date'])
            need_date = datetime.date(year, month, day)
            tmpOrder = {
                value['id']: {
                    'id': value['id'],
                    'need_date': value['need_date'],
                    'number': value['number'],
                    'order_date': value['order_date'],
                    'type': value['type'],
                    'delivery_date': f'{delivery_date}',
                    'status':True
                }
            }
            if delivery_date > need_date:   #超出需求日
                tmpOrder[value['id']]['status'] = False
            Output['pq_10G'].append(tmpOrder)    #所有1G的訂單預測交期加入pq_1G
            if data.get('new_order') == None:
                continue
            if len(data.get('new_order')) != 0:
                if value['id'] == data['new_order']['id']:    #如果當前訂單是新訂單，另外存在new_order
                    Output['new_order']= {
                        'id': value['id'],
                        'need_date': value['need_date'],
                        'number': value['number'],
                        'order_date': value['order_date'],
                        'type': value['type'],
                        'delivery_date': f'{delivery_date}'
                    }
    #計算1G機台數
    if(len(data['pq_1G']) > 0):
        for i in range(0, len(future_machine_need_list_1G)): #計算距離今天i天的機台數
            if(future_machine_need_list_1G[i] == 0):
                break
            date = (today + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            tmpNum = {
                date: {
                    'date': date,
                    'number': future_machine_need_list_1G[i]
                }
            }
            Output['machine_num_need_1G'].append(tmpNum)
    #計算10G機台數
    if(len(data['pq_10G']) > 0):
        for i in range(0, len(future_machine_need_list_10G)): #計算距離今天i天的機台數
            if(future_machine_need_list_10G[i] == 0):
                break
            date = (today + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            tmpNum = {
                date: {
                    'date': date,
                    'number': future_machine_need_list_10G[i]
                }
            }
            Output['machine_num_need_10G'].append(tmpNum)
    return Output

#mode 3
def UseMode3(data):
    data = dealwith_machine_num(data)
    final_index_1G = 0
    final_index_10G = 0
    Output = {
        'pq_1G': [],
        'pq_10G': [],
        'new_order':{},
        'machine_num_need_1G':[],
        'machine_num_need_10G' :[],
        }
    #1G預測
    tmp_buffer_1G = 0 #用來放滿足當前訂單還剩下多少
    if(len(data['pq_1G']) > 0):
        year, month, day = SplitNeedDate(list(data['pq_1G'][-1].values())[0]['need_date'])
        last_need_date = datetime.date(year, month, day)
        total_day = (last_need_date - today).days
        future_machine_need_list_1G = [0]*factor  #開五倍用來處理可能會超出需求日的問題
        order_need_unit_list_1G = [0]*len(data['pq_1G'])
        begin_index_1G = 0
        future_machine_limit_list_1G = data['machine_num_1G']
        for i in range (len(future_machine_limit_list_1G), len(future_machine_need_list_1G)):
            future_machine_limit_list_1G.append(future_machine_limit_list_1G[-1])
        for order in data['pq_1G']:
            value = list(order.values())[0]
            year, month , day = SplitNeedDate(value['need_date'])
            need_date = datetime.date(year, month, day)
            need_production = value['number']
            need_unit = int(((need_production - tmp_buffer_1G)/(X1G_mean*X1G_cycle)) + 1) #需要幾天生產，補齊1天 + 1
            tmp_buffer_1G = int((need_unit*X1G_mean*X1G_cycle + tmp_buffer_1G) - need_production) #滿足訂單後還剩下多少多的
            order_need_unit_list_1G[data['pq_1G'].index(order)] = need_unit
            if (need_date - today).days - threshold_day > 0:
                end_index_1G = (need_date - today).days - threshold_day   #最多可以填到future_machine_need_list_1G的哪個index(不包含)
            elif (need_date - today).days <= 0:
                end_index_1G = 1
            else:
                end_index_1G = (need_date - today).days
            begin_index_1G , final_index_1G= FillUnit_Mode3(need_unit, future_machine_need_list_1G, future_machine_limit_list_1G, begin_index_1G , end_index_1G, final_index_1G)

        delivery_date_list_1G = ComputeDeliveryDate(future_machine_need_list_1G, order_need_unit_list_1G)
        for order in data['pq_1G']:
            value = list(order.values())[0]
            order_index = data['pq_1G'].index(order)
            year, month, day = SplitNeedDate(delivery_date_list_1G[order_index])
            delivery_date = datetime.date(year, month, day)
            year, month , day = SplitNeedDate(value['need_date'])
            need_date = datetime.date(year, month, day)
            tmpOrder = {
                value['id']: {
                    'id': value['id'],
                    'need_date': value['need_date'],
                    'number': value['number'],
                    'order_date': value['order_date'],
                    'type': value['type'],
                    'delivery_date': f'{delivery_date}',
                    'status':True
                }
            }
            if delivery_date > need_date:   #超出需求日
                tmpOrder[value['id']]['status'] = False
            Output['pq_1G'].append(tmpOrder)    #所有1G的訂單預測交期加入pq_1G
            if data.get('new_order') == None:
                continue
            if len(data.get('new_order')) != 0:
                if value['id'] == data['new_order']['id']:    #如果當前訂單是新訂單，另外存在new_order
                    Output['new_order']= {
                        'id': value['id'],
                        'need_date': value['need_date'],
                        'number': value['number'],
                        'order_date': value['order_date'],
                        'type': value['type'],
                        'delivery_date': f'{delivery_date}'
                    }
    #10G預測
    tmp_buffer_10G = 0 #用來放滿足當前訂單還剩下多少
    if(len(data['pq_10G']) > 0):
        year, month, day = SplitNeedDate(list(data['pq_10G'][-1].values())[0]['need_date'])
        last_need_date = datetime.date(year, month, day)
        total_day = (last_need_date - today).days
        future_machine_need_list_10G = [0]*factor  #開五倍用來處理可能會超出需求日的問題
        order_need_unit_list_10G = [0]*len(data['pq_10G'])
        begin_index_10G = 0
        future_machine_limit_list_10G = data['machine_num_10G']
        for i in range (len(future_machine_limit_list_10G), len(future_machine_need_list_10G)):
            future_machine_limit_list_10G.append(future_machine_limit_list_10G[-1])
        for order in data['pq_10G']:
            value = list(order.values())[0]
            year, month , day = SplitNeedDate(value['need_date'])
            need_date = datetime.date(year, month, day)
            need_production = value['number']
            need_unit = int(((need_production - tmp_buffer_10G)/(X10G_mean*X10G_cycle)) + 1) #需要幾天生產，補齊1天 + 1
            tmp_buffer_10G = int((need_unit*X10G_mean*X10G_cycle + tmp_buffer_10G) - need_production) #滿足訂單後還剩下多少多的
            order_need_unit_list_10G[data['pq_10G'].index(order)] = need_unit
            if (need_date - today).days - threshold_day > 0:
                end_index_10G = (need_date - today).days - threshold_day   #最多可以填到future_machine_need_list_10G的哪個index(不包含)
            elif (need_date - today).days <= 0:
                end_index_10G = 1
            else:
                end_index_10G = (need_date - today).days
            begin_index_10G , final_index_10G= FillUnit_Mode3(need_unit, future_machine_need_list_10G, future_machine_limit_list_10G, begin_index_10G , end_index_10G, final_index_10G)
        delivery_date_list_10G = ComputeDeliveryDate(future_machine_need_list_10G, order_need_unit_list_10G)
        for order in data['pq_10G']:
            value = list(order.values())[0]
            order_index = data['pq_10G'].index(order)
            year, month, day = SplitNeedDate(delivery_date_list_10G[order_index])
            delivery_date = datetime.date(year, month, day)
            year, month , day = SplitNeedDate(value['need_date'])
            need_date = datetime.date(year, month, day)
            tmpOrder = {
                value['id']: {
                    'id': value['id'],
                    'need_date': value['need_date'],
                    'number': value['number'],
                    'order_date': value['order_date'],
                    'type': value['type'],
                    'delivery_date': f'{delivery_date}',
                    'status':True
                }
            }
            if delivery_date > need_date:   #超出需求日
                tmpOrder[value['id']]['status'] = False
            Output['pq_10G'].append(tmpOrder)    #所有1G的訂單預測交期加入pq_1G
            if data.get('new_order') == None:
                continue
            if len(data.get('new_order')) != 0:
                if value['id'] == data['new_order']['id']:    #如果當前訂單是新訂單，另外存在new_order
                    Output['new_order']= {
                        'id': value['id'],
                        'need_date': value['need_date'],
                        'number': value['number'],
                        'order_date': value['order_date'],
                        'type': value['type'],
                        'delivery_date': f'{delivery_date}'
                    }
    #計算1G機台數
    if(len(data['pq_1G']) > 0):
        for i in range(0, final_index_1G + 1): #計算距離今天i天的機台數
            date = (today + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            tmpNum = {
                date: {
                    'date': date,
                    'number': future_machine_need_list_1G[i]
                }
            }
            Output['machine_num_need_1G'].append(tmpNum)
    #計算10G機台數
    if(len(data['pq_10G']) > 0):
        for i in range(0, final_index_10G + 1): #計算距離今天i天的機台數
            date = (today + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            tmpNum = {
                date: {
                    'date': date,
                    'number': future_machine_need_list_10G[i]
                }
            }
            Output['machine_num_need_10G'].append(tmpNum)
    return Output

#處理machine_num，把今天之前的資料移除
def dealwith_machine_num(data):
    end_index = 0
    for tmp in data['machine_num_1G']:
        value = list(tmp.values())[0]['date']
        end_index = end_index + 1
        if(value == str(today)):
            break
    del data['machine_num_1G'][0:end_index - 1]

    end_index = 0
    for tmp in data['machine_num_10G']:
        value = list(tmp.values())[0]['date']
        end_index = end_index + 1
        if(value == str(today)):
            break
    del data['machine_num_10G'][0:end_index - 1]
    return data

#交期預測函數
def PredictDeliveryDate(data):
    global today
    today = setToday()
    if data.get('mode') != None:
        ChooseMode(data['mode'])
    global mode
    if mode == 1:
        return UseMode1(data)
    if mode == 2:
        return UseMode2(data)
    if mode == 3:
        return UseMode3(data)