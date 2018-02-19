#!/bin/bash

turnon()
{
curl -X POST \
  http://10.0.10.181:5000/switch \
  -H 'cache-control: no-cache' \
  -H 'content-type: application/json' \
  -H 'postman-token: 09a937ae-9082-fb5d-5b3d-8b50eab4fb43' \
  -d '{
    "state" :"on"
}'
} 

turnoff(){
curl -X POST \
  http://10.0.10.181:5000/switch \
  -H 'cache-control: no-cache' \
  -H 'content-type: application/json' \
  -H 'postman-token: 09a937ae-9082-fb5d-5b3d-8b50eab4fb43' \
  -d '{
    "state" :"off"
}'
}

while true
do 
	echo "Press [CTRL+C] to stop... "
	sleep 5
	turnoff
	sleep 5
	turnon
done

