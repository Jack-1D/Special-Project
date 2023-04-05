# 交期預測系統

# 主要模組
- 交期排程模組
- 產量預測模組

# 檔案目錄結構

* app.py : api 的程式進入點
* moduel: 模組
    * DeliveryDateForecast: 交期預測模組
        * scheduler: 交期排程模組
            * DB_mysql.py: 資料庫處理
            * FileProcess.py: csv 檔案處理
            * scheduler.py: 排程處理
        * OutputPrediction: 產量預測模組

# 套件安裝
## MysqlDB 安裝
```
$ pip3 install mysqlclient
```
### 參考資料
[Python3 + MySql: Error loading MySQLdb module: No module named 'MySQLdb'](https://stackoverflow.com/questions/26560973/python3-mysql-error-loading-mysqldb-module-no-module-named-mysqldb)