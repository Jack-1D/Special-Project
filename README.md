# Special-Project
sudo mysql -p -u root
CREATE USER 'pdclab'@'140.115.52.21' IDENTIFIED BY 'pdclab1234';
GRANT ALL PRIVILEGES ON orderlist . * TO 'pdclab'@'140.115.52.21';
FLUSH PRIVILEGES;
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf
<!-- kill占用port的所有process -->
kill $(lsof -t -i:8888)
<!-- or -->
sudo netstat -lpn |grep 8888
kill -9 [pid]

flask run -p 8888 -h 0.0.0.0
<!-- 背景執行 -->
sudo pip3 install gunicorn
sudo gunicorn --pythonpath /home/pdclab/.local/lib/python3.10/site-packages -b 0.0.0.0:8888 app:app --daemon