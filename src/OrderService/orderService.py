# saved as greeting-server.py
import Pyro5.api
import json
import csv
import os
import pickle
import threading
import socket
import sys

# Making pyro threaded server
Pyro5.config.SERVERTYPE = "thread"
Pyro5.config.THREADPOOL_SIZE_MIN = 5

lock = threading.Lock()


#Setting some default responses

MSG1 = {"data":{
    "transaction_number":0
}}
MSG0 = {"error":{
    "code":402,
    "message":"Stock Not Found"
}}
MSGn1 = {"error":{
    "code":404,
    "message":"Not Enough Stocks"
}
}

@Pyro5.api.expose
class OrderService(object):
    ID = int(sys.argv[1])
    LEADER_ID = None
    #ID = None
    PICKLE_FILE = f"data/last_id_{ID}.pickle"
    LOG_FILE = f"data/tradeLog_{ID}.csv"
    FOLLOWERS = None
    if os.path.exists(PICKLE_FILE):#Checking if last transaction ID is pickled
        with open(PICKLE_FILE, "rb") as f:
            Transaction_id = pickle.load(f)
    else:
        Transaction_id = 0
    
    def leaderSelected(self, ID, followers = None):
        OrderService.LEADER_ID = ID
        print(type(ID) ,type(OrderService.ID), followers)
        if ID == OrderService.ID:
            OrderService.FOLLOWERS = followers
            print(OrderService.FOLLOWERS)


    def Trade(self, stock_name, trade_type, quantity):

        CatalogService = Pyro5.api.Proxy("PYRONAME:service.catalog")#Connecting to catalog service

        response = CatalogService.trade(stock_name, 1 if trade_type.lower()=="sell" else -1, quantity)
        # 1 is Pass, 0 is no stock name, -1 is Not enough stock
        if response==1:
            with lock:
                MSG1["data"]["transaction_number"] = OrderService.Transaction_id    #Assiging transaction ID
                with open(OrderService.LOG_FILE, "a") as file:
                    writer = csv.writer(file)
                    if os.path.getsize(OrderService.LOG_FILE) == 0:
                        writer.writerow(["Transaction ID", "Stock Name", "Order Type", "Quantity"])#Adding headers if it's a new file
                    writer.writerow([OrderService.Transaction_id, stock_name, trade_type, quantity])
                OrderService.Transaction_id+=1
                with open(OrderService.PICKLE_FILE, "wb") as f:
                    pickle.dump(OrderService.Transaction_id, f) #Storing Transaction ID
                
                for follower_id in OrderService.FOLLOWERS:
                    follower = Pyro5.api.Proxy(f"PYRONAME:service.order{follower_id}")
                    follower.updateLog(
                        [OrderService.Transaction_id, stock_name, trade_type, quantity])
                return json.dumps(MSG1)
        elif response==0:
            return json.dumps(MSG0)
        else:
            return json.dumps(MSGn1)
    def healthCheck(self):
        return True

    def notifyLeader(self, leader_ID):
        OrderService.LEADER_ID = leader_ID
    
    def updateLog(self, order_details):
        with open(OrderService.LOG_FILE, "a") as file:
            writer = csv.writer(file)
            if os.path.getsize(OrderService.LOG_FILE) == 0:
                writer.writerow(["Transaction ID", "Stock Name", "Order Type", "Quantity"]) # Adding headers if it's a new file
            writer.writerow(order_details)
        OrderService.Transaction_id += 1
        with open(OrderService.PICKLE_FILE, "wb") as f:
            pickle.dump(OrderService.Transaction_id, f)


        
container_ip = socket.gethostbyname(socket.gethostname())
daemon = Pyro5.server.Daemon(host = container_ip)         # make a Pyro daemon
ns = Pyro5.api.locate_ns()             # find the name server
# register the greeting maker as a Pyro object
uri = daemon.register(OrderService)
# register the object with a name in the name server
ns.register(f"service.order{sys.argv[1]}", uri)

print("Ready.")
# start the event loop of the server to wait for calls

daemon.requestLoop()
