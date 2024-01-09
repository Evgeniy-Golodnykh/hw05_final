# YaTube

### Description
The YaTube App is used for blogging, subscribing to authors and tracking their publications.

### Quick Start
1. Clone repo
```bash
git clone git@github.com:Evgeniy-Golodnykh/yatube.git
```
2. Creates the virtual environment
```bash
python3 -m venv venv
```
3. Activates the virtual environment
```bash
source venv/bin/activate
```
4. Upgrade PIP and install the requirements packages into the virtual environment
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```
5. To create the database use command
```bash
python3 manage.py migrate
```
6. To run the application use command
```bash
python3 manage.py runserver
```

### Technology
[Python](https://www.python.org), [Django](https://www.djangoproject.com)

### Author
[Evgeniy Golodnykh](https://github.com/Evgeniy-Golodnykh)
