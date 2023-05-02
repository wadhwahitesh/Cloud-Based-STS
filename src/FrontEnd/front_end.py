import socketserver
import http.server
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import Pyro5.api as pyro
import Pyro5
from dotenv import load_dotenv
import time
import threading
load_dotenv()


HOST = "localhost"   #Running over all available ips
PORT = int(os.getenv("HOST_PORT"))#Loading from env variable
NUM_THREADS = 5 #Setting max threads
NUM_REPLICAS = int(os.getenv("NUM_REPLICAS"))
REPLICAS = [""]*4
LEADER = None
cache = {}

for i in range(1,NUM_REPLICAS+1):
        REPLICAS[i] = os.getenv("ORDERSERVICE_"+str(i))

#Creating the threaded server
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

lock = threading.Lock()




#Creating handler
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Handle GET request here
        #ns = pyro.locate_ns()
        
        parsed_url = urlparse(self.path).path.split('/')

        if parsed_url[1] == "stocks":    #Checking if correct GET request is mad
            CatalogService = pyro.Proxy(
                "PYRONAME:service.catalog")  # Getting Pyro Proxy
            with lock:
                if parsed_url[-1].lower() in cache:
                    print("Found in cache")
                    response = cache[parsed_url[-1].lower()]
                else:
                    print("Fetching...")
                    response = CatalogService.Lookup(parsed_url[-1])
                    cache[parsed_url[-1].lower()] = response
                    print(cache)
            self.send_response(200)
            self.send_header('Content-Type', 'json')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
        elif parsed_url[1] == "leaderID":
            self.send_response(200)
            self.send_header('Content-Type', 'json')
            self.end_headers()
            self.wfile.write(json.dumps({"ID":LEADER}).encode('utf-8'))
            



    def do_POST(self):
        if self.path == '/invalidate_cache':
            with lock:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                stock_name = post_data.decode('utf-8').split('=')[1]
                print("Inside invalidate {}".format(stock_name))

                if stock_name.lower() in cache:
                    del cache[stock_name.lower()]
                response_text = "Cache invalidated for {}".format(stock_name)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(response_text.encode('utf-8'))
                print(12345)
        else:
            orderData={}
            try:
                OrderService = pyro.Proxy("PYRONAME:service.order"+str(LEADER))
                parsed_url = urlparse(self.path).path.split('/')
                if parsed_url[1] == "orders":
                    content_length = int(self.headers['Content-Length'])
                    orderData = json.loads(self.rfile.read(content_length).decode())#Getting Post request data
                    response = OrderService.Trade(orderData["name"], orderData["type"], orderData["quantity"])
                    self.send_response(200)
                    self.send_header('Content-Type', 'json')
                    self.end_headers()
                    print(1234)
                    self.wfile.write(response.encode('utf-8'))
            except:
                leader_election()
                OrderService = pyro.Proxy("PYRONAME:service.order"+str(LEADER))
                response = OrderService.Trade(orderData["name"], orderData["type"], orderData["quantity"])
                self.send_response(200)
                self.send_header('Content-Type', 'json')
                self.end_headers()
                self.wfile.write(response.encode('utf-8'))



def leader_election():
    global LEADER

    print("Electing Leader, Please Wait......")
    for i in range(NUM_REPLICAS,0,-1):
        try:
            if pyro.Proxy("PYRONAME:{}".format(REPLICAS[i])).healthCheck():
                LEADER = i
                break
        except (Pyro5.errors.CommunicationError, Pyro5.errors.NamingError):
            continue
    
    if LEADER==None:
        time.sleep(2)
        print("Leader Not Found Yet, Trying Again")
        leader_election()
    
    
    for i in range(NUM_REPLICAS,0,-1):
        try:
            replica  = pyro.Proxy("PYRONAME:{}".format(REPLICAS[i]))
            # if i==LEADER:
            #     replica.leaderSelected(LEADER, [j for j in range(1,NUM_REPLICAS+1) if j != LEADER])
            # else:
            replica.leaderSelected(LEADER)
        except (Pyro5.errors.CommunicationError, Pyro5.errors.NamingError):
            continue

    print("Leader Elected:{}".format(LEADER))


    


if __name__ == "__main__":
    

    # Create thread pool
    executor = ThreadPoolExecutor(max_workers=NUM_THREADS)

    # Create threaded HTTP server
    httpd = ThreadedHTTPServer((HOST, PORT), Handler)

    # Set up handler to use thread pool
    httpd.request_queue_size = 10
    httpd.shutdown_on_request = False
    httpd.executor = executor   #Passing threaded executor to handler

    # Start server
    print("Server listening on http://{}:{}".format(HOST, PORT))
    leader_election()

    httpd.serve_forever()
    
