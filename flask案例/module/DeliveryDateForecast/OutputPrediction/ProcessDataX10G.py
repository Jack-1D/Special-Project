import pandas as pd

# 參數
num_machine = 6
record_error_threshold = 200    #記錄錯誤threshold
stop_produce_threshold = 800    #兩天內停機產能下降threshold
machine_produce_error_threshold = 1500  #生產異常threshold

# Function
def getX10G_mean():
    return X10G_mean

def getX10G_len():
    return X10G_len

def getX10G_normal_mean():
    return X10G_normal_mean

def getX10G_normal_len():
    return X10G_normal_len

def getX10G_error_mean():
    return X10G_error_mean

def getX10G_error_len():
    return X10G_error_len

# 10G產量資料處理
df10G=pd.read_csv('10G_data.csv',encoding='big5')
#去除記錄錯誤
for i in df10G.index:
    if df10G.loc[i, '產能'] <= record_error_threshold:
        df10G.loc[i, '產能'] = 0
        df10G.loc[i, 'OEE'] = 0.0
        df10G.loc[i, '良率'] = 0.0

df01=df10G[df10G['機台號']=="h01"]
df02=df10G[df10G['機台號']=="h02"]
df08=df10G[df10G['機台號']=="h08"]
df10=df10G[df10G['機台號']=="h10"]
df15=df10G[df10G['機台號']=="h15"]
df19=df10G[df10G['機台號']=="h19"]
#去除重複資料
df01.reset_index(drop=True, inplace=True)
df01 = df01[df01.index%2==0]
df01.reset_index(drop=True, inplace=True)
df02.reset_index(drop=True, inplace=True)
df02 = df02[df02.index%2==0]
df02.reset_index(drop=True, inplace=True)
df08.reset_index(drop=True, inplace=True)
df08 = df08[df08.index%2==0]
df08.reset_index(drop=True, inplace=True)
df10.reset_index(drop=True, inplace=True)
df10 = df10[df10.index%2==0]
df10.reset_index(drop=True, inplace=True)
df15.reset_index(drop=True, inplace=True)
df15 = df15[df15.index%2==0]
df15.reset_index(drop=True, inplace=True)
df19.reset_index(drop=True, inplace=True)
df19 = df19[df19.index%2==0]
df19.reset_index(drop=True, inplace=True)
#去除因為兩天內因停機造成的產能下降異常
df10G_list = [df01, df02, df08, df10, df15, df19]
for tmp_df in df10G_list:
    for i in range((len(tmp_df) - 4)):
        if (tmp_df.loc[i, '產能'] <= stop_produce_threshold) & (tmp_df.loc[i + 2, '產能'] == 0 | tmp_df.loc[i + 4, '產能'] == 0): #因為有晚上，所以要+2
            tmp_df.loc[i, '產能'] = 0
            tmp_df.loc[i, 'OEE'] = 0.0
            tmp_df.loc[i, '良率'] = 0.0

df10G = pd.concat([df01, df02, df08, df10, df15, df19], axis=0)
df10G['生產日期'] = pd.to_datetime(df10G['生產日期'], format = '%Y/%m/%d')
df10G.sort_values(by=['生產日期','機台號'], inplace = True)
df10G.reset_index(drop=True, inplace=True)

X10G = pd.DataFrame(columns=['生產日期', '產能', 'OEE', '良率'])

#計算每日平均產量
for i in range(int(len(df10G)/(num_machine*2))):
    produce_machine_num = num_machine*2 - df10G.loc[i*num_machine*2 : i*num_machine*2 + num_machine*2 - 1,'產能'].eq(0).sum(axis = 0) #有在生產的機台數
    if produce_machine_num != 0:
        X10G.loc[i, '生產日期'] = df10G.loc[i*num_machine*2, '生產日期']
        X10G.loc[i, '產能'] = df10G.loc[i*num_machine*2 : i*num_machine*2 + num_machine*2 - 1, '產能'].sum(axis = 0)/produce_machine_num
        X10G.loc[i, 'OEE'] = df10G.loc[i*num_machine*2 : i*num_machine*2 + num_machine*2 - 1, 'OEE'].sum(axis = 0)/produce_machine_num
        X10G.loc[i, '良率'] = df10G.loc[i*num_machine*2 : i*num_machine*2 + num_machine*2 - 1, '良率'].sum(axis = 0)/produce_machine_num
    else:
        X10G.loc[i, '生產日期'] = df10G.loc[i*num_machine*2, '生產日期']
        X10G.loc[i, '產能'] = 0
        X10G.loc[i, 'OEE'] = 0
        X10G.loc[i, '良率'] = 0

#將平均產量為0去除
X10G = X10G[X10G['產能'] != 0]
X10G.reset_index(drop=True, inplace=True)

X10G['生產日期'] = pd.to_datetime(X10G['生產日期'], format = '%Y/%m/%d')

#統計正常生產與異常生產
X10G_error = X10G[X10G['產能'] <= machine_produce_error_threshold]
X10G_normal = X10G[X10G['產能'] >machine_produce_error_threshold]
X10G_error.reset_index(drop=True, inplace=True)
X10G_normal.reset_index(drop=True, inplace=True)

X10G_mean = X10G['產能'].mean()
X10G_len = len(X10G)
X10G_normal_mean = X10G_normal['產能'].mean()
X10G_normal_len = len(X10G_normal)
X10G_error_mean = X10G_error['產能'].mean()
X10G_error_len = len(X10G_error)