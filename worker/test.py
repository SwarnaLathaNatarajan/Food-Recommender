from IPython import embed
import jsonpickle
import platform
import io
import os
import sys
import pika
import redis
import requests

user, radius, lat, lon = "krishna", "1", "40.014984", "-105.270546"
# log(
#     "logs",
#     hostname + ".worker.info",
#     "Recieved message " + user + ", " + lat + ", "+lon,
# )
url = "https://us-restaurant-menus.p.rapidapi.com/menuitems/search/geo"

querystring = {"lon":"-73.992378","lat":"40.68919","distance":"1","page":"1"}
# log(
#     "logs",
#     hostname + ".worker.info",
#     "Querying Backend Rapid API",
# )
headers = {
    'x-rapidapi-key': "4da4beaf58msh777f33561f3f9bap13722ejsna5635d03cc22",
    'x-rapidapi-host': "us-restaurant-menus.p.rapidapi.com"
}

response = requests.request("GET", url, headers=headers, params=querystring)
# log(
#     "logs",
#     hostname + ".worker.info",
#     response.text,
# )
embed()
# redisUserToFoodItems.srem(user)
# response=response.json()
# foodItems=response["result"]["data"]
# for foodItem in foodItems.keys():
#     foodName=foodItems[foodItem]["menu_item_name"]
#     description=foodItems[foodItem]["menu_item_description"]
#     newItem=Item(foodName, description)
#     pickledItem = pickle.dumps(newItem)
#     redisUserToFoodItems.sadd(user, pickledItem)