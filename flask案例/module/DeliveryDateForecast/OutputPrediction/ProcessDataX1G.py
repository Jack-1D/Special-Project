import pandas as pd

#####參數#####

num_machine = 9
record_error_threshold = 200    #記錄錯誤threshold
stop_produce_threshold = 800    #兩天內停機產能下降threshold
machine_produce_error_threshold = 1500  #生產異常threshold

#####Function#####

def getX1G_mean():
    return X1G_mean

def getX1G_len():
    return X1G_len

def getX1G_normal_mean():
    return X1G_normal_mean

def getX1G_normal_len():
    return X1G_normal_len

def getX1G_error_mean():
    return X1G_error_mean

def getX1G_error_len():
    return X1G_error_len

def getX1G_design_weight_mean():
    return X1G_design_weight_mean
#####1G產量資料處理#####

df1G=pd.read_csv('machine_status.csv',encoding='big5')
df1G['生產日期'] = pd.to_datetime(df1G['生產日期'], format = '%Y/%m/%d')
#去除記錄錯誤
for i in df1G.index:
    if df1G.loc[i, '產能'] <= record_error_threshold:
        df1G.loc[i, '產能'] = 0
        df1G.loc[i, 'OEE'] = 0.0
        df1G.loc[i, '良率'] = 0.0

df04=df1G[df1G['機台號']=="h04"]
df05=df1G[df1G['機台號']=="h05"]
df06=df1G[df1G['機台號']=="h06"]
df09=df1G[df1G['機台號']=="h09"]
df11=df1G[df1G['機台號']=="h11"]
df12=df1G[df1G['機台號']=="h12"]
df13=df1G[df1G['機台號']=="h13"]
df14=df1G[df1G['機台號']=="h14"]
df16=df1G[df1G['機台號']=="h16"]
#去除重複資料
df04.reset_index(drop=True, inplace=True)
df04 = df04[df04.index%2==0]
df04.reset_index(drop=True, inplace=True)
df05.reset_index(drop=True, inplace=True)
df05 = df05[df05.index%2==0]
df05.reset_index(drop=True, inplace=True)
df06.reset_index(drop=True, inplace=True)
df06 = df06[df06.index%2==0]
df06.reset_index(drop=True, inplace=True)
df09.reset_index(drop=True, inplace=True)
df09 = df09[df09.index%2==0]
df09.reset_index(drop=True, inplace=True)
df11.reset_index(drop=True, inplace=True)
df11 = df11[df11.index%2==0]
df11.reset_index(drop=True, inplace=True)
df12.reset_index(drop=True, inplace=True)
df12 = df12[df12.index%2==0]
df12.reset_index(drop=True, inplace=True)
df13.reset_index(drop=True, inplace=True)
df13 = df13[df13.index%2==0]
df13.reset_index(drop=True, inplace=True)
df14.reset_index(drop=True, inplace=True)
df14 = df14[df14.index%2==0]
df14.reset_index(drop=True, inplace=True)
df16.reset_index(drop=True, inplace=True)
df16 = df16[df16.index%2==0]
df16.reset_index(drop=True, inplace=True)

#針對機台轉線日期清除不屬於1G資料
df04_cutoff_date = pd.to_datetime('2023-03-11')
df04.loc[df04['生產日期'] <= df04_cutoff_date, '產能'] = 0
df05_cutoff_date = pd.to_datetime('2023-03-04')
df05.loc[df05['生產日期'] <= df05_cutoff_date, '產能'] = 0
df09_cutoff_date = pd.to_datetime('2023-02-09')
df09.loc[df09['生產日期'] <= df09_cutoff_date, '產能'] = 0
df11_cutoff_date = pd.to_datetime('2023-03-10')
df11.loc[df11['生產日期'] <= df11_cutoff_date, '產能'] = 0
df12_cutoff_date = pd.to_datetime('2023-03-06')
df12.loc[df12['生產日期'] <= df12_cutoff_date, '產能'] = 0
df13_cutoff_date = pd.to_datetime('2023-02-03')
df13.loc[df13['生產日期'] <= df13_cutoff_date, '產能'] = 0
df14_cutoff_date = pd.to_datetime('2022-09-14')
df14.loc[df14['生產日期'] <= df14_cutoff_date, '產能'] = 0
df16_cutoff_date = pd.to_datetime('2023-03-17')
df16.loc[df16['生產日期'] <= df16_cutoff_date, '產能'] = 0

#去除因為兩天內因停機造成的產能下降異常
df1G_list = [df04, df05, df06, df09, df11, df12, df13, df14, df16]
for tmp_df in df1G_list:
    for i in range((len(tmp_df) - 3)):
        if (tmp_df.loc[i, '產能'] <= stop_produce_threshold) & (tmp_df.loc[i + 1, '產能'] == 0 | tmp_df.loc[i + 2, '產能'] == 0 | tmp_df.loc[i + 3, '產能'] == 0): #考慮晚上，所以要+1
            tmp_df.loc[i, '產能'] = 0
            tmp_df.loc[i, 'OEE'] = 0
            tmp_df.loc[i, '良率'] =0

df1G = pd.concat([df04, df05, df06, df09, df11, df12, df13, df14, df16], axis=0)
df1G.sort_values(by=['生產日期','機台號'], inplace = True)
df1G.reset_index(drop=True, inplace=True)

X1G = pd.DataFrame(columns=['生產日期', '產能', 'OEE', '良率'])

#計算每日平均產量
for i in range(int(len(df1G)/(num_machine*2))):
    produce_machine_num = num_machine*2 - df1G.loc[i*num_machine*2 : i*num_machine*2 + num_machine*2 - 1,'產能'].eq(0).sum(axis = 0) #有在生產的機台數
    if produce_machine_num != 0:
        X1G.loc[i, '生產日期'] = df1G.loc[i*num_machine*2, '生產日期']
        X1G.loc[i, '產能'] = df1G.loc[i*num_machine*2 : i*num_machine*2 + num_machine*2 - 1, '產能'].sum(axis = 0)/produce_machine_num
        X1G.loc[i, 'OEE'] = df1G.loc[i*num_machine*2 : i*num_machine*2 + num_machine*2 - 1, 'OEE'].sum(axis = 0)/produce_machine_num
        X1G.loc[i, '良率'] = df1G.loc[i*num_machine*2 : i*num_machine*2 + num_machine*2 - 1, '良率'].sum(axis = 0)/produce_machine_num
    else:
        X1G.loc[i, '生產日期'] = df1G.loc[i*num_machine*2, '生產日期']
        X1G.loc[i, '產能'] = 0
        X1G.loc[i, 'OEE'] = 0
        X1G.loc[i, '良率'] = 0

#將平均產量為0去除
X1G = X1G[X1G['產能'] != 0]
X1G.reset_index(drop=True, inplace=True)

X1G['生產日期'] = pd.to_datetime(X1G['生產日期'], format = '%Y/%m/%d')

#統計正常生產與異常生產
X1G_error = X1G[X1G['產能'] <= machine_produce_error_threshold]
X1G_normal = X1G[X1G['產能'] >machine_produce_error_threshold]
X1G_error.reset_index(drop=True, inplace=True)
X1G_normal.reset_index(drop=True, inplace=True)

X1G_mean = X1G['產能'].mean()
X1G_len = len(X1G)
X1G_normal_mean = X1G_normal['產能'].mean()
X1G_normal_len = len(X1G_normal)
X1G_error_mean = X1G_error['產能'].mean()
X1G_error_len = len(X1G_error)

#設計權重計算產能
interval_1 = 5  #區間寬度n 最後n筆
interval_2 = 10 #區間寬度n interval_1之後的n筆
interval_3 = 10 #同上概念
interval_4 = 5  #同上概念
interva1_1_weitht = 0.4 #權重 interval_1最重要 因為最靠近預測當日
interval_2_weight = 0.3
interval_3_weight = 0.2
interval_4_weight = 0.1
interval_1_mean = X1G['產能'][-(interval_1 + 1):-1].mean()
interval_2_mean = X1G['產能'][-(interval_2 + interval_1 + 1):-(interval_1 + 1)].mean()
interval_3_mean = X1G['產能'][-(interval_3 + interval_2+ interval_1 + 1):-(interval_2 + interval_1 + 1)].mean()
interval_4_mean = X1G['產能'][-(interval_4 + interval_3 + interval_2+ interval_1 + 1):-(interval_3 + interval_2 + interval_1 + 1)].mean()
X1G_design_weight_mean = (interval_1_mean * interva1_1_weitht) + (interval_2_mean * interval_2_weight) + (interval_3_mean * interval_3_weight) + (interval_4_mean * interval_4_weight)