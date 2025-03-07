# MoteurRecherche
DAAR | master 2 STL sorbonne université 
# 1. Installation
## 1.1. Windows
```bash   
cd backend
python -m venv env
./env/Scripts/activate
pip install -r req.txt
```
## 1.2. Macos/Linux
``` bash   
cd backend
python3 -m venv env
source ./env/bin/activate
pip3 install -r req.txt
```
Postgres should be installed in your device.

``` bash   
brew install postgresql

```

# 2. Data base
in the backend folder
```bash   
python manage.py makemigrations
python manage.py migrate
```
# 2.1. Commands to execute
These django commands needs to be executed in this specific order so that the project actually works correctly, note that these commands may take some time, depending on your CPU / internet speed so grab a coffee and call your friends ( you probably don't have any)
- Make sure to be in thed ```./backend``` folder
```sh   
mkdir keywords
python manage.py initBooks
python manage.py addKeywords
python manage.py computeKeywords
python manage.py createGraphJaccard
```
# 3. BackEnd API endpoints
```sh   
data/books/
data/books/neighbors/<int:pk>
server/books/
```
# 4. Server startup
in the ```./backend``` folder, execute :
```bash
python manage.py runserver
```
default host is ```localhost:8000``` 
# 5. Frontend startup

``` bash
cd frontend
npm i 
npm run dev
```
default host is ```localhost:3000``` 