import Pyro5.api
import json
import threading
import socket
import os
import requests


#Making pyro threaded server
Pyro5.config.SERVERTYPE = "thread"
Pyro5.config.THREADPOOL_SIZE_MIN = 5

print("Intializing server with stock data....")


#Checkinf if file exists or is it first time running
if os.path.exists("data/stocks.json") and os.path.getsize("data/stocks.json") != 0:
    with open('data/stocks.json', 'r') as openfile:
        DATA = json.load(openfile)
else:
    DATA = {"gamestart": {"price": 10, "volume": 0, "quantity": 100}, #If no make a new database
            "fishco": {"price": 30, "volume": 0, "quantity": 100},
            "boarco": {"price": 20, "volume": 0, "quantity": 100}, 
            "menhirco": {"price": 40, "volume": 0, "quantity": 100}}


lock = threading.Lock()  # create a lock object


@Pyro5.api.expose
class CatalogService(object):
    def Lookup(self, stock_name):
        with lock:
            stock_name = stock_name.lower()
            if not stock_name in DATA:
                error = {
                    "error": {
                    "code": 402,
                    "message": "Stock Not Found"
                    }
                }
                return json.dumps(error)
            
            stock_data= {
                "name": stock_name,
                "price": DATA[stock_name]["price"],
                "quantity": DATA[stock_name]["quantity"]
            }
            return json.dumps(stock_data)
    
    def trade(self, stock_name, trade_type, quantity):
        #1 for sell, -1 for buy 
        #1 success
        #0 invalid stock name 
        #-1 not enough stocks
        with lock:
            stock_name = stock_name.lower()
            if not stock_name in  DATA:
                return 0
            elif trade_type*quantity+DATA[stock_name]["quantity"]<0: #Sell = 1 will increae the quantity and buy being -1 will decrease
                return -1   #Checking if enough stocks exist
            DATA[stock_name]["quantity"]+=trade_type*quantity
            DATA[stock_name]["volume"]+=quantity
            with open("data/stocks.json", "w") as outfile:
                json.dump(DATA, outfile)
                
             # Send an invalidation request to the front-end server
            url = "http://localhost:8080/invalidate_cache"
            invalidate_data = {"stock_name": stock_name}
            response = requests.post(url, data=invalidate_data)
            return 1


container_ip = socket.gethostbyname(socket.gethostname())       #Getting host ip for finding nameserver
daemon = Pyro5.server.Daemon(host = container_ip)         # make a Pyro daemon
# find the name server
ns = Pyro5.api.locate_ns()  #Locating nameserver
uri = daemon.register(CatalogService)
ns.register("service.catalog", uri) #Registring
print("Ready")
daemon.requestLoop()