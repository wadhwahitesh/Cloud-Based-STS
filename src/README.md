Submitted by : Anchal Gupta and Hitesh Wadhwa

# How to run

Should have python-dotenv and pyro5 pip installed.

or run "pip3 install python-dotenv pyro5"

## For running with AWS

1. run aws ec2 run-instances --image-id ami-0d73480446600f555 --instance-type m5a.large --key-name vockey > instance.json
2. Get instance ID and DNS name
3. run aws ec2 describe-instances --instance-id <your-instance-id>
4. run ssh -i labsuser.pem ubuntu@<your_dns/ip>
5. git clone repo
6. start nameserver
7. Open port 8080 using aws ec2 describe-instances --instance-ids <instance-id> --query 'Reservations[].Instances[].SecurityGroups[].GroupId' --output text
8. aws ec2 authorize-security-group-ingress --group-id <security-group-id> --protocol tcp --port <port-number> --cidr 0.0.0.0/0
9. start all services
10. run front end at 0.0.0.0
11. connect client at public IP address



## For running on terminal

All of the below steps should be on a new terminal

1. First run the pyro nameserver using "pyro5-ns"
2. Then start the catalog service after cd to CatalogService by "python3 catalogService.py"
3. Start the order service replica 1 in OrderSerive directory, run "python3 orderService.py 1"
4. Start the order service replica 1 in OrderSerive directory, run "python3 orderService.py 2"
5. Start the order service replica 1 in OrderSerive directory, run "python3 orderService.py 3"
4. In FrontEnd directory, run "python3 front_end.py"
5. Now for the client, inside the client directory, run "python3 client.py".

## Group Contribution 

Anchal completed part 1 and 2 
Hitesh completed part 3 and 4
We both worked on the documents and evaluation. 


