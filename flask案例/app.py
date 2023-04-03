from flask import Flask, request, jsonify
from module.DeliveryDateForecast.scheduler import scheduler as s
from datetime import date, timedelta
import json
app = Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET','POST'])
def show():
    return jsonify(s.show_pq())

@app.route('/insertorder', methods=['GET','POST'])
def insert():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            return jsonify(s.insert_order(data))
    return "Fail"

@app.route('/deleteorder', methods=['GET','POST'])
def delete():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            return jsonify(s.delete_order(data))
    return "Fail"




@app.route('/login', methods=['POST'])
def login():
    if request.is_json: # 判斷是不是 JSON
        data = request.get_json() # 從資料中獲取值
        name1 = data.get('name1', None) # 解析資料，若不是 JSON，則返回 None

        ## 你撰寫完成的模組，引入方式
        ## name1，以JSON key 作為後續 API　的參數串接
        # result = scheduler.whoAreYou(name1)
    else:
        result = 'Not JSON Data'
    return result


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8089)

    # test code

    # while(True):
    #     command = input("Action: ")
    #     if(command=='1'):
    #         s.show_pq()
    #     elif(command=='2'):
    #         l=input("list: ").split(" ")
    #         s.insert_order(l)
    #     elif(command=='3'):
    #         l=input("list: ").split(" ")
    #         s.delete_order(l)
    #     elif(command=='4'):
    #         path,d=input("path&date: ").split(" ")
    #         yesterday_date = date.today()-timedelta(days=1)
    #         print(s.get_daily_total(path=path,yesterday_date=d))
    #     elif(command=='5'):
    #         print(s.show_finish_order())
    #     elif(command=='6'):
    #         start,end=input("Dates: ").split(" ")
    #         s.draw_1G_graph(start_date=start, end_date=end)
    #     elif(command=='7'):
    #         start,end=input("Dates: ").split(" ")
    #         s.draw_10G_graph(start_date=start, end_date=end)
    #     elif(command=='8'):
    #         start,end=input("Dates: ").split(" ")
    #         s.draw_buffer1G_graph(start_date=start, end_date=end)
    #     elif(command=='9'):
    #         start,end=input("Dates: ").split(" ")
    #         s.draw_buffer10G_graph(start_date=start, end_date=end)
    #     print(f"pq:{s.get_pq()}")
    #     print(f"buffer1G: {s.get_buffer1G()}")
    #     print(f"buffer10G: {s.get_buffer10G()}")
    