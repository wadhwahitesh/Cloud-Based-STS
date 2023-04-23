# How to run

Should have python-dotenv and pyro5 pip installed.

or run "pip3 install python-dotenv pyro5"

## For running with docker

All the services can be run using the "docker-compose up --build" command. This will start all the services along with the port forwarding set up.

The client should be then run on a new terminal by going to the client directory and run by using "python3 client.py".

Additionally, build.sh can be run using the command "bash build.sh". This will build all the images. This is not required as docker-compose command will also build all the images.

## For running on terminal

All of the below steps should be on a new terminal

1. First run the pyro nameserver using "pyro5-ns"
2. Then start the catalog service after cd to CatalogService by "python3 catalogService.py"
3. In OrderSerive directory, run "python3 orderService.py"
4. In FrontEnd directory, run "python3 front_end.py"
5. Now for the client, inside the client directory, run "python3 client.py".



