import json
from .ProcessDataX10G import *
from .ProcessDataX1G import *
import datetime

X10G_mean = getX10G_mean()
X10G_len = getX10G_len()
X1G_mean = getX1G_mean()
X1G_len = getX1G_len()
X10G_buffer = 0
X1G_buffer = 0
mode = 2
X10G_max_machine_num = 6
X1G_max_machine_num = 9
X10G_cycle = 1 #10G只有日班
X1G_cycle = 2   #1G有日、夜班
X10G_oneday_max_production = X10G_mean*X10G_max_machine_num*X10G_cycle
X1G_oneday_max_production = X1G_mean*X1G_max_machine_num*X1G_cycle
threshold_day = 2 # mode2 mode3 距離需求日threshold


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
def FillNextDay_Mode3(i, future_machine_list, future_machine_limit_list):
    if future_machine_list[i + 1] < list(future_machine_limit_list[i + 1].values())[0]['number']:
        future_machine_list[i + 1] = future_machine_list[i + 1] + 1
    else:
        FillNextDay_Mode3(i + 1, future_machine_list, future_machine_limit_list)

#Mode3 若當日機台數滿了 往前填
def FillBeforeDay_Mode3(i, future_machine_list, future_machine_limit_list):
    for j in range(0, i):
        if future_machine_list[j] < list(future_machine_limit_list[j].values())[0]['number']:
            future_machine_list[j] = future_machine_list[j] + 1
            return
    FillNextDay_Mode3(i, future_machine_list, future_machine_limit_list)    #前面也都滿了，填入下一天

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
def FillUnit_Mode3(need_unit, future_machine_list, future_machine_limit_list, begin_index, end_index):
    while need_unit > 0:
        for i in range(begin_index, end_index):
            if need_unit <=0:
                begin_index = i
                break
            #print(f"index {begin_index} to {end_index}")
            if future_machine_list[i] < list(future_machine_limit_list[i].values())[0]['number']:
                future_machine_list[i] = future_machine_list[i] + 1
            else:
                FillBeforeDay_Mode3(i, future_machine_list, future_machine_limit_list)  #當天填滿，往前找是否有空缺，否則填入下一天，
            need_unit = need_unit -1
        if(need_unit !=0):
            begin_index = 0
    return begin_index

# 計算交期
def ComputeDeliveryDate(future_machine_list, order_need_unit_list, today):
    buffer = 0
    deliverydate_list = [0]*len(order_need_unit_list)
    tmp_index = 0   #當前檢查到哪裡
    for i in range(0, len(deliverydate_list)):
        for j in range(tmp_index, len(future_machine_list)):
            buffer = buffer + future_machine_list[j]
            if buffer >= order_need_unit_list[i]:
                buffer = buffer - order_need_unit_list[i]
                delivery_date = today + datetime.timedelta(days=j + 1)  #下一日才能出貨
                tmp_index = j
                deliverydate_list[i] = f'{delivery_date}'
                break
    return deliverydate_list            

#mode 1
def UseMode1(data):
    today = datetime.date.today() #今天日期
    Output = {
        'pq_1G': [],
        'pq_10G': [],
        'new_order':{},
        'machine_num_need_1G':[],
        'machine_num_need_10G' :[],
        'status':True
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
        #print(f'buffer begin: {tmp_buffer_1G}')
        tmp_buffer_1G = int((need_day*X1G_oneday_max_production + tmp_buffer_1G) - need_production) #滿足訂單後還剩下多少多的
        delivery_date = today + datetime.timedelta(days=day_end_1G)
        '''
        print(f'begin: {today + datetime.timedelta(days=day_begin_1G)}')
        print(f'end: {today + datetime.timedelta(days=day_end_1G)}')
        print(f'delivery date: { delivery_date}')
        print(f'buffer end: {tmp_buffer_1G}')
        print(f'need: {need_production}')
        print(f'need day: {need_day}')
        print(f'produce: {need_day*X1G_oneday_max_production}')
        print("==========")
        '''
        if delivery_date > need_date:   #超出需求日
            Output['status'] = False
        tmpOrder = {
            value['id']: {
                'id': value['id'],
                'need_date': value['need_date'],
                'number': value['number'],
                'order_date': value['order_date'],
                'type': value['type'],
                'delivery_date': f'{delivery_date}'
            }
        }
        Output['pq_1G'].append(tmpOrder)    #所有1G的訂單預測交期加入pq_1G
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
        #print(f'buffer begin: {tmp_buffer_10G}')
        tmp_buffer_10G = int((need_day*X10G_oneday_max_production + tmp_buffer_10G) - need_production)  #滿足訂單後還剩下多少多的
        delivery_date = today + datetime.timedelta(days=day_end_10G)
        '''
        print(f'begin: {today + datetime.timedelta(days=day_begin_10G)}')
        print(f'end: {today + datetime.timedelta(days=day_end_10G)}')
        print(f'delivery date: { delivery_date}')
        print(f'buffer end: {tmp_buffer_10G}')
        print(f'need: {need_production}')
        print(f'need day: {need_day}')
        print(f'produce: {need_day*X10G_oneday_max_production}')
        print("==========")
        '''
        if delivery_date > need_date:   #超出需求日
            Output['status'] = False
        tmpOrder = {
            value['id']: {
                'id': value['id'],
                'need_date': value['need_date'],
                'number': value['number'],
                'order_date': value['order_date'],
                'type': value['type'],
                'delivery_date': f'{delivery_date}'
            }
        }
        Output['pq_10G'].append(tmpOrder)   #所有10G的訂單預測交期加入pq_10G
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
    today = datetime.date.today() #今天日期
    Output = {
        'pq_1G': [],
        'pq_10G': [],
        'new_order':{},
        'machine_num_need_1G':[],
        'machine_num_need_10G' :[],
        'status':True
        }
    #1G預測
    tmp_buffer_1G = 0 #用來放滿足當前訂單還剩下多少
    if(len(data['pq_1G']) > 0):
        year, month, day = SplitNeedDate(list(data['pq_1G'][-1].values())[0]['need_date'])
        last_need_date = datetime.date(year, month, day)
        total_day = (last_need_date - today).days
        future_machine_need_list_1G = [0]*total_day*5  #開五倍用來處理可能會超出需求日的問題
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
            end_index_1G = (need_date - today).days - threshold_day   #最多可以填到future_machine_need_list_1G的哪個index(不包含)
            #print(f'begin: {begin_index_1G}')
            #print(f'end: {end_index_1G}')
            begin_index_1G = FillUnit_Mode2(need_unit, future_machine_need_list_1G, value['type'], begin_index_1G , end_index_1G)   #填滿unit，並回傳下次要從哪裡開始填
            #print(f'buffer begin: {tmp_buffer_1G}')
        
        delivery_date_list_1G = ComputeDeliveryDate(future_machine_need_list_1G, order_need_unit_list_1G, today)
        for order in data['pq_1G']:
            value = list(order.values())[0]
            order_index = data['pq_1G'].index(order)
            year, month, day = SplitNeedDate(delivery_date_list_1G[order_index])
            delivery_date = datetime.date(year, month, day)
            if delivery_date > need_date:
                Output['status'] = False
            tmpOrder = {
                value['id']: {
                    'id': value['id'],
                    'need_date': value['need_date'],
                    'number': value['number'],
                    'order_date': value['order_date'],
                    'type': value['type'],
                    'delivery_date': f'{delivery_date}'
                }
            }
            Output['pq_1G'].append(tmpOrder)    #所有1G的訂單預測交期加入pq_1G
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
        future_machine_need_list_10G = [0]*total_day*5  #開五倍用來處理可能會超出需求日的問題
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
            end_index_10G = (need_date - today).days - threshold_day  #最多可以填到future_machine_need_list_1G的哪個index(不包含)
            #print(f'begin: {begin_index_10G}')
            #print(f'end: {end_index_10G}')
            begin_index_10G = FillUnit_Mode2(need_unit, future_machine_need_list_10G, value['type'], begin_index_10G , end_index_10G)   #填滿unit，並回傳下次要從哪裡開始填
            #print(f'buffer begin: {tmp_buffer_10G}')
        
        delivery_date_list_10G = ComputeDeliveryDate(future_machine_need_list_10G, order_need_unit_list_10G, today)
        for order in data['pq_10G']:
            value = list(order.values())[0]
            order_index = data['pq_10G'].index(order)
            year, month, day = SplitNeedDate(delivery_date_list_10G[order_index])
            delivery_date = datetime.date(year, month, day)
            if delivery_date> need_date:
                Output['status'] = False
            tmpOrder = {
                value['id']: {
                    'id': value['id'],
                    'need_date': value['need_date'],
                    'number': value['number'],
                    'order_date': value['order_date'],
                    'type': value['type'],
                    'delivery_date': f'{delivery_date}'
                }
            }
            Output['pq_10G'].append(tmpOrder)    #所有1G的訂單預測交期加入pq_1G
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
    today = datetime.date.today() #今天日期
    Output = {
        'pq_1G': [],
        'pq_10G': [],
        'new_order':{},
        'machine_num_need_1G':[],
        'machine_num_need_10G' :[],
        'status':True
        }
    #1G預測
    tmp_buffer_1G = 0 #用來放滿足當前訂單還剩下多少
    if(len(data['pq_1G']) > 0):
        year, month, day = SplitNeedDate(list(data['pq_1G'][-1].values())[0]['need_date'])
        last_need_date = datetime.date(year, month, day)
        total_day = (last_need_date - today).days
        future_machine_need_list_1G = [0]*total_day*5  #開五倍用來處理可能會超出需求日的問題
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
            end_index_1G = (need_date - today).days - threshold_day   #最多可以填到future_machine_need_list_1G的哪個index(不包含)
            #print(f'begin: {begin_index_1G}')
            #print(f'end: {end_index_1G}')
            begin_index_1G = FillUnit_Mode3(need_unit, future_machine_need_list_1G, future_machine_limit_list_1G, begin_index_1G , end_index_1G)
            #print(f'buffer begin: {tmp_buffer_1G}')
        
        delivery_date_list_1G = ComputeDeliveryDate(future_machine_need_list_1G, order_need_unit_list_1G, today)
        for order in data['pq_1G']:
            value = list(order.values())[0]
            order_index = data['pq_1G'].index(order)
            year, month, day = SplitNeedDate(delivery_date_list_1G[order_index])
            delivery_date = datetime.date(year, month, day)
            if delivery_date > need_date:
                Output['status'] = False
            tmpOrder = {
                value['id']: {
                    'id': value['id'],
                    'need_date': value['need_date'],
                    'number': value['number'],
                    'order_date': value['order_date'],
                    'type': value['type'],
                    'delivery_date': f'{delivery_date}'
                }
            }
            Output['pq_1G'].append(tmpOrder)    #所有1G的訂單預測交期加入pq_1G
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
        future_machine_need_list_10G = [0]*total_day*5  #開五倍用來處理可能會超出需求日的問題
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
            end_index_10G = (need_date - today).days - threshold_day  #最多可以填到future_machine_need_list_1G的哪個index(不包含)
            #print(f'begin: {begin_index_10G}')
            #print(f'end: {end_index_10G}')
            begin_index_10G = FillUnit_Mode3(need_unit, future_machine_need_list_10G, future_machine_limit_list_10G, begin_index_10G , end_index_10G)
            #print(f'buffer begin: {tmp_buffer_10G}')
        
        delivery_date_list_10G = ComputeDeliveryDate(future_machine_need_list_10G, order_need_unit_list_10G, today)
        for order in data['pq_10G']:
            value = list(order.values())[0]
            order_index = data['pq_10G'].index(order)
            year, month, day = SplitNeedDate(delivery_date_list_10G[order_index])
            delivery_date = datetime.date(year, month, day)
            if delivery_date> need_date:
                Output['status'] = False
            tmpOrder = {
                value['id']: {
                    'id': value['id'],
                    'need_date': value['need_date'],
                    'number': value['number'],
                    'order_date': value['order_date'],
                    'type': value['type'],
                    'delivery_date': f'{delivery_date}'
                }
            }
            Output['pq_10G'].append(tmpOrder)    #所有1G的訂單預測交期加入pq_1G
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

#交期預測函數
def PredictDeliveryDate(data):
    # data = json.load(myJson)
    if data.get('new_order') != None:
        newOrder = {
            data['new_order']['id']: {
                'id': data['new_order']['id'],
                'need_date': data['new_order']['need_date'],
                'number': data['new_order']['number'],
                'order_date': data['new_order']['order_date'],
                'type': data['new_order']['type']
            }
        }
    global mode
    if mode == 1:
        return UseMode1(data)
    if mode == 2:
        return UseMode2(data)
    if mode == 3:
        return UseMode3(data)