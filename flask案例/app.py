from flask import Flask, request, jsonify
from module.DeliveryDateForecast.scheduler import scheduler as s
from datetime import date, timedelta
import json
app = Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET','POST'])
def show():
    return jsonify(s.show_pq())

@app.route('/insertorder', methods=['POST'])
def insert():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            return jsonify(s.insert_order(data))
    return "Fail"

@app.route('/deleteorder', methods=['POST'])
def delete():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            return jsonify(s.delete_order(data))
    return "Fail"

@app.route('/sum', methods=['POST'])
def summ():
    if request.method == 'POST':
        sum_1G, sum_10G = s.get_daily_product_sum()
        sum_1G.update(sum_10G)
        return jsonify(sum_1G)

@app.route('/test',methods=['POST'])
def test():
    if request.method == 'POST':
        jason = {"finish_queue":[{"4":{"id":4, "need_date":"2022-12-10", "number":2000, "order_date":"2022-12-01", "type":"1G-POE"},\
        "1":{"id":1, "need_date":"2022-12-05", "number":9000, "order_date":"2022-11-25", "type":"10G"}}],\
        "pq_10G":[{"5":{"id":5, "need_date":"2022-12-16", "number":6000, "order_date":"2022-11-14", "type":"10G"},\
        "7":{"id":7, "need_date":"2022-12-27", "number":1000, "order_date":"2022-11-22", "type":"10G"}}],\
        "pq_1G":[{"10":{"id":10, "need_date":"2022-12-19", "number":500, "order_date":"2022-11-29", "type":"1G-POE"},\
        "15":{"id":15, "need_date":"2022-12-27", "number":300, "order_date":"2022-11-09", "type":"1G-POE"}}],\
        "machine_num_10G":[{"2022-12-01":{"date":"2022-12-01", "number":6},\
        "2022-12-02":{"date":"2022-12-02", "number":6},\
        "2022-12-03":{"date":"2022-12-03", "number":6},\
        "2022-12-04":{"date":"2022-12-04", "number":6},\
        "2022-12-05":{"date":"2022-12-05", "number":6},\
        "2022-12-06":{"date":"2022-12-06", "number":5},\
        "2022-12-07":{"date":"2022-12-07", "number":4},\
        "2022-12-08":{"date":"2022-12-08", "number":4},\
        "2022-12-09":{"date":"2022-12-09", "number":4},\
        "2022-12-10":{"date":"2022-12-10", "number":4},\
        "2022-12-11":{"date":"2022-12-11", "number":3},\
        "2022-12-12":{"date":"2022-12-12", "number":3},\
        "2022-12-13":{"date":"2022-12-13", "number":1},\
        "2022-12-14":{"date":"2022-12-14", "number":1}}],
        "machine_num_1G":[{"2022-12-01":{"date":"2022-12-01", "number":5},\
        "2022-12-02":{"date":"2022-12-02", "number":6},\
        "2022-12-03":{"date":"2022-12-03", "number":2},\
        "2022-12-04":{"date":"2022-12-04", "number":6},\
        "2022-12-05":{"date":"2022-12-05", "number":6},\
        "2022-12-06":{"date":"2022-12-06", "number":5},\
        "2022-12-07":{"date":"2022-12-07", "number":4},\
        "2022-12-08":{"date":"2022-12-08", "number":3},\
        "2022-12-09":{"date":"2022-12-09", "number":4},\
        "2022-12-10":{"date":"2022-12-10", "number":4},\
        "2022-12-11":{"date":"2022-12-11", "number":6},\
        "2022-12-12":{"date":"2022-12-12", "number":3},\
        "2022-12-13":{"date":"2022-12-13", "number":1},\
        "2022-12-14":{"date":"2022-12-14", "number":5}}]}
        return jsonify(jason)


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
    app.run(host='0.0.0.0', port=8888)
    

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
    