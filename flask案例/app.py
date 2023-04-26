from flask import Flask, request, jsonify
from module.DeliveryDateForecast.scheduler import scheduler as s
from module.DeliveryDateForecast.OutputPrediction import Function as func
from datetime import timedelta, datetime, timezone
from werkzeug.utils import secure_filename
import os, copy
app = Flask(__name__)
app.config["DEBUG"] = False
show_date_length = 14
today_date_unformated = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
yesterday_date = datetime.strftime(today_date_unformated-timedelta(days=1),'%Y-%m-%d')

# 預設machine_num_need是mode 1
@app.route('/', methods=['GET','POST'])
def show():
    return_value = s.show_pq()
    print("origin:",return_value)
    return_value.update(func.PredictDeliveryDate(return_value))
    print("predict:",return_value)
    s.update_delivery(return_value)
    return jsonify(return_value)

@app.route('/insertorder', methods=['POST'])
def insert():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            return_value = func.PredictDeliveryDate(s.insert_order(data))
            s.update_delivery(return_value)
            return jsonify(return_value)
    return "Fail"

@app.route('/deleteorder', methods=['POST'])
def delete():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            return_value = func.PredictDeliveryDate(s.delete_order(data))
            s.update_delivery(return_value)
            return jsonify(return_value)
    return "Fail"

@app.route('/sum', methods=['POST'])
def summ():
    if request.method == 'POST':
        sum_1G, sum_10G = s.get_daily_product_sum()
        sum_1G.update(sum_10G)
        return jsonify(sum_1G)
        
@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        data = request.get_json()
        return jsonify(s.find_order(data['id']))

# mode 3會用 default的檔案
@app.route('/change', methods=['POST'])
def changemode():
    if request.method == 'POST':
        data = request.get_json()
        return_value = s.show_pq()
        return_value['mode'] = data['mode']
        return_value['start_date'] = data['start_date']
        if data['mode'] == 3:
            return_value['machine_num_1G'] = s.add_limit('machine_num.csv')['machine_num_1G']
            return_value['machine_num_10G'] = s.add_limit('machine_num.csv')['machine_num_10G']
        else:
            return_value['machine_num_1G'] = s.add_limit()['machine_num_1G']
            return_value['machine_num_10G'] = s.add_limit()['machine_num_10G']
        return_copy = copy.deepcopy(return_value)
        predict_result = func.PredictDeliveryDate(return_copy)
        
        return_value['pq_1G'] = predict_result['pq_1G']
        return_value['pq_10G'] = predict_result['pq_10G']
        return_value['machine_num_need_1G'] = predict_result['machine_num_need_1G']
        return_value['machine_num_need_10G'] = predict_result['machine_num_need_10G']
        s.update_delivery(return_value)
        # 只回傳時間內的需求機台數
        date_range = [datetime.strptime(data['start_date'],"%Y-%m-%d") + timedelta(days=idx) for idx in range(show_date_length)]
        return_machine_need = [{datetime.strftime(datetime.strptime(data['start_date'],"%Y-%m-%d") + \
                                timedelta(days=idx),"%Y-%m-%d"):{'date':datetime.strftime(datetime.strptime\
                                (data['start_date'],"%Y-%m-%d") + timedelta(days=idx),"%Y-%m-%d"), 'number':0}} \
                                    for idx in range(14)]
        for _, row in enumerate(return_value['machine_num_need_1G']):
            for element in row.items():
                if datetime.strptime(element[0],"%Y-%m-%d") in date_range:
                    return_machine_need[return_machine_need.index({element[0]:{"date":element[0],"number":0}})] = \
                        {element[0]:element[1]}
        return_value['machine_num_need_1G'] = return_machine_need

        return_machine_need = [{datetime.strftime(datetime.strptime(data['start_date'],"%Y-%m-%d") + \
                                timedelta(days=idx),"%Y-%m-%d"):{'date':datetime.strftime(datetime.strptime\
                                (data['start_date'],"%Y-%m-%d") + timedelta(days=idx),"%Y-%m-%d"), 'number':0}} \
                                    for idx in range(14)]
        for _, row in enumerate(return_value['machine_num_need_10G']):
            for element in row.items():
                if datetime.strptime(element[0],"%Y-%m-%d") in date_range:
                    return_machine_need[return_machine_need.index({element[0]:{"date":element[0],"number":0}})] = \
                        {element[0]:element[1]}
        return_value['machine_num_need_10G'] = return_machine_need
        return return_value

UPLOAD_FOLDER = '/home/pdclab/Special-Project/flask案例'
ALLOWED_EXTENSIONS = set(['csv'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            if filename == 'machine_status.csv':
                return_value = func.PredictDeliveryDate(s.get_daily_total('machine_status.csv',yesterday_date))
                s.update_delivery(return_value)
            return "Success"
    return "Fail"

@app.route('/test', methods=['POST'])
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
        "2022-12-14":{"date":"2022-12-14", "number":5}}],\
        "machine_num_need_10G": [],\
        "machine_num_need_1G": [{"2023-04-14": {"date": "2023-04-14","number": 1}},\
        {"2023-04-15": {"date": "2023-04-15","number": 1}},\
        {"2023-04-16": {"date": "2023-04-16","number": 1}},\
        {"2023-04-17": {"date": "2023-04-17","number": 1}},\
        {"2023-04-18": {"date": "2023-04-18","number": 1}},\
        {"2023-04-19": {"date": "2023-04-19","number": 1}},\
        {"2023-04-20": {"date": "2023-04-20","number": 1}},\
        {"2023-04-21": {"date": "2023-04-21","number": 1}},\
        {"2023-04-22": {"date": "2023-04-22","number": 1}},\
        {"2023-04-23": {"date": "2023-04-23","number": 1}},\
        {"2023-04-24": {"date": "2023-04-24","number": 1}},\
        {"2023-04-25": {"date": "2023-04-25","number": 1}},\
        {"2023-04-26": {"date": "2023-04-26","number": 1}}],\
        "new_order": {},\
        "status": True
        }
        return jsonify(jason)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8888)