# saved as greeting-server.py
import Pyro5.api
import json
import csv
import os
import pickle
import threading
import socket
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

# Making pyro threaded server
Pyro5.config.SERVERTYPE = "thread"
Pyro5.config.THREADPOOL_SIZE_MIN = 5
NUM_REPLICAS = int(os.getenv("NUM_REPLICAS"))

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
    # FOLLOWERS = None
    if os.path.exists(PICKLE_FILE):#Checking if last transaction ID is pickled
        with open(PICKLE_FILE, "rb") as f:
            Transaction_id = pickle.load(f)
    else:
        Transaction_id = 0
    
    try:

        url = "http://localhost:8080/leaderID"
        response = requests.get(url)
        if response.status_code == 200:
            LEADER_ID = json.loads(response.content.decode())['ID']
            print(LEADER_ID)
            if LEADER_ID != None:
                transactions=Pyro5.api.Proxy(f"PYRONAME:service.order{LEADER_ID}").fetch_transactions(Transaction_id-1)
                print(transactions)
                with open(LOG_FILE, "a") as file:
                    writer = csv.writer(file)
                    if os.path.getsize(LOG_FILE) == 0:
                        writer.writerow(["Transaction ID", "Stock Name", "Order Type", "Quantity"])#Adding headers if it's a new file
                    for transaction in transactions:
                            writer.writerow(transaction)
                    Transaction_id += len(transactions)
                    with open(PICKLE_FILE, "wb") as f:
                        pickle.dump(Transaction_id, f)
        else:
            print('Request failed with status code:', response.status_code)
    except Exception as e:
        print(e)
        print("Front end not active, No leader appointed!")
    
    def fetch_transactions(self, id):
        entries = []
        if id<OrderService.Transaction_id:
            with open(OrderService.LOG_FILE, "r") as file:
                reader = csv.reader(file)
                found_id = False
                for row in reader:
                    print(found_id)
                    if found_id:
                        entries.append(row)
                    elif row[0] == id or id == -1:
                        found_id = True
        
        return entries

    
    def leaderSelected(self, ID):
        OrderService.LEADER_ID = ID
        # if ID == OrderService.ID:
        #     OrderService.FOLLOWERS = followers


    def Trade(self, stock_name, trade_type, quantity):

        CatalogService = Pyro5.api.Proxy("PYRONAME:service.catalog")#Connecting to catalog service

        response = CatalogService.trade(stock_name, 1 if trade_type.lower()=="sell" else -1, quantity)
        # 1 is Pass, 0 is no stock name, -1 is Not enough stock
        if response==1:
            with lock:
                MSG1["data"]["transaction_number"] = OrderService.Transaction_id    #Assiging transaction ID
                order_details = None
                with open(OrderService.LOG_FILE, "a") as file:
                    writer = csv.writer(file)
                    if os.path.getsize(OrderService.LOG_FILE) == 0:
                        writer.writerow(["Transaction ID", "Stock Name", "Order Type", "Quantity"])#Adding headers if it's a new file
                    order_details = [OrderService.Transaction_id,
                                     stock_name, trade_type, quantity]
                    writer.writerow(order_details)
                OrderService.Transaction_id+=1
                with open(OrderService.PICKLE_FILE, "wb") as f:
                    pickle.dump(OrderService.Transaction_id, f) #Storing Transaction ID
                # print(OrderService.FOLLOWERS)
                for follower_id in range(1,NUM_REPLICAS+1):
                    try:
                        if follower_id != OrderService.ID:
                            follower = Pyro5.api.Proxy(f"PYRONAME:service.order{follower_id}")
                            follower.updateLog(
                                order_details)
                    except Exception as e:
                        print(e)
                        continue
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
