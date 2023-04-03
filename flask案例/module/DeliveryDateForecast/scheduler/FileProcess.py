'''
目的: 負責處理CSV檔案
- 回傳成 list 或 json 的檔案格式
'''
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
from .DB_mysql import Mysql

dataframe = pd.DataFrame

# 每日讀取機台產量
## 回傳: dataframe
def read_production(path: str) -> dataframe:
    return pd.read_csv(f"{path}",encoding='big5')

# 日期轉換
## 回傳: %Y-%m-%d 格式的日期
def start_end_transform(start_date: str, end_date: str) -> tuple:
    start_date = datetime.strptime(start_date,"%Y-%m-%d").date()
    end_date = datetime.strptime(end_date,"%Y-%m-%d").date()
    return start_date, end_date

# 畫圖
## 回傳: 無回傳值，將圖片存成.jpg檔
def draw_graph(start_date: str, end_date: str, db: Mysql, label: str, option: str) -> None:
    sumProduct: list = []
    start_date, end_date = start_end_transform(start_date=start_date, end_date=end_date)
    match option:
        case "1G production":
            for d in pd.date_range(start=start_date, end=end_date):
                sumProduct.append(db.get_1G_production_sum(d)[0][0])
        case "10G production":
            for d in pd.date_range(start=start_date, end=end_date):
                sumProduct.append(db.get_10G_production_sum(d)[0][0])
        case "1G buffer":
            for d in pd.date_range(start=start_date, end=end_date):
                sumProduct.append(db.get_1G_buffer(d)[0][0])
        case "10G buffer":
            for d in pd.date_range(start=start_date, end=end_date):
                sumProduct.append(db.get_10G_buffer(d)[0][0])
    date_index = [f'{x.date()}' for x in pd.date_range(start=start_date, end=end_date)]

    max_index=np.argmax(sumProduct)
    min_index=np.argmin(sumProduct)
    max_label=f'[{start_date+timedelta(days=int(max_index))},{sumProduct[max_index]}]'
    min_label=f'[{start_date+timedelta(days=int(min_index))},{sumProduct[min_index]}]'
    plt.figure(figsize=(12,7))
    plt.grid()
    plt.annotate(max_label,xytext=(max_index,sumProduct[max_index]),xy=(max_index,sumProduct[max_index]))
    plt.annotate(min_label,xytext=(min_index,sumProduct[min_index]),xy=(min_index,sumProduct[min_index]))
    plt.plot(max_index,sumProduct[max_index],'ro')
    plt.plot(min_index,sumProduct[min_index],'ro')
    plt.plot(date_index,sumProduct,label=f'{label}')
    plt.legend()
    plt.savefig(f'{label}.jpg')