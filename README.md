# Special-Project
sudo mysql -p -u root
CREATE USER 'pdclab'@'140.115.52.21' IDENTIFIED BY 'pdclab1234';
GRANT ALL PRIVILEGES ON orderlist . * TO 'pdclab'@'140.115.52.21';
FLUSH PRIVILEGES;
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf
<!-- kill占用port的所有process -->
kill $(lsof -t -i:8888)
flask run -p 8888 -h 0.0.0.0