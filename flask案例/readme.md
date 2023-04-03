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