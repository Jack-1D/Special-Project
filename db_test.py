import pymysql

# 連結 SQL
connect_db =  pymysql.connect(host="localhost",user="pdclab",password="pdclab1234",database="orderlist",port=3306)

with connect_db.cursor() as cursor:
    sql = """
    SELECT * FROM orderlist ORDER BY NEEDDATE
    """
    
    # 執行 SQL 指令
    cursor.execute(sql)
    
    # 取出全部資料
    data = cursor.fetchall()
    print(data)

# 關閉 SQL 連線
connect_db.close()