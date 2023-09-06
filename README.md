# Special-Project
## Install python3.10
``` bash
sudo apt-get update
sudo apt upgrade
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
wget https://www.python.org/ftp/python/3.10.11/Python-3.10.11.tgz
tar -xvf Python-3.10.11.tgz
cd Python-3.10.11
./configure --enable-optimizations
make -j 8
make altinstall
sudo rm /usr/bin/python3
sudo ln -s /usr/local/bin/python3.10 /usr/bin/python3
```

### 如果遇到問題（pkg_resources.DistributionNotFound: The 'pip==20.0.2' distribution was not found and is required by the application）
``` bash
python3 -m pip -V
# 各需要修改兩個地方
sudo vim /usr/bin/pip3
sudo vim /usr/bin/pip
```

## Use virtualenv to install requirements
``` bash
pip install virtualenv
cd ~
git clone https://github.com/Jack-1D/Special-Project.git
cd Special-Project
virtualenv venv
source venv/bin/activate
pip install -r flask案例/requirements.txt
```

## Install MySQL
``` bash
sudo apt update && sudo apt install mysql-server
sudo mysql -p -u root
CREATE USER 'pdclab'@'140.115.52.21' IDENTIFIED BY 'pdclab1234';
GRANT ALL PRIVILEGES ON orderlist . * TO 'pdclab'@'140.115.52.21';
FLUSH PRIVILEGES;
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf
```

<!-- kill占用port的所有process -->
kill $(lsof -t -i:8888)
<!-- or -->
sudo netstat -lpn |grep 8888
kill -9 [pid]

flask run -p 8888 -h 0.0.0.0
<!-- 背景執行 -->
sudo pip3 install gunicorn
sudo gunicorn --pythonpath /home/pdclab/.local/lib/python3.10/site-packages -b 0.0.0.0:8888 app:app --daemon