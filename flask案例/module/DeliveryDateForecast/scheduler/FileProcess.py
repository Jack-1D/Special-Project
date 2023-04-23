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
def read_file(path: str) -> dataframe:
    return pd.read_csv(f"{path}",encoding='big5')

# 日期轉換
## 回傳: %Y-%m-%d 格式的日期
def start_end_transform(start_date: str, end_date: str) -> tuple:
    start_date = datetime.strptime(start_date,"%Y-%m-%d").date()
    end_date = datetime.strptime(end_date,"%Y-%m-%d").date()
    return start_date, end_date