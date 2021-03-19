import osmnx as ox
import networkx as nx
import numpy as np
from datetime import timedelta
import timeit
import matplotlib.pyplot as plt
import pandas as pd
from random import randint
from tqdm import tqdm
import time
import requests
import key
import json


class Node:
    def __init__(self,lat,lon,charge):
        self.lat = lat
        self.lon = lon
        self.charge = charge

class NodeTab:
    def __init__(self):
        self.tab=[]
        self.bubbleNum=0
        self.depotNum=0

    def add_bubble(self,node):
        self.tab.insert(self.bubbleNum, node)
        self.bubbleNum = self.bubbleNum+1
    
    def add_depot(self,node):
        if node.charge == 0:
            self.tab.append(node)
            self.depotNum = self.depotNum+1
        else:
            print("Depot node charge should be 0 ")

class SymetricalMatrix:
    
    def __init__(self, size):
        intsize= (int) ((size+1) * size/2)
        self.symMatrix = np.zeros(intsize)
    
    def get_index(self,i,j):
        row, column = i,j
        if column > row:
            row, column = column, row
        index = row * (row + 1) // 2 + column
        return index

    def add_element(self, i, j, element):
        index = self.get_index(i,j)
        self.symMatrix[index]= element

    def get_element(self, i, j):
        index = self.get_index(i,j)
        return self.symMatrix[index]

def routing_time(startPos,endPos):
    getRequest='https://router.hereapi.com/v8/routes?transportMode=car&origin='+str(startPos.lat)+','+str(startPos.lon)+'&destination='+str(endPos.lat)+','+str(endPos.lon)+'&return=summary&apikey='+key.APIKEY
    response=requests.get(getRequest)
    responseJson=response.json()
    if responseJson["routes"]:
        routingTime=responseJson["routes"][0]['sections'][0]['summary']['duration']
        return routingTime #seconds
    else:
        print("No route found: "+startPos.lat+' '+startPos.lon+' to '+endPos.lat+' '+endPos.lon)
        return 0
    
def routing_distance(startPos,endPos):
    getRequest='https://router.hereapi.com/v8/routes?transportMode=car&origin='+str(startPos.lat)+','+str(startPos.lon)+'&destination='+str(endPos.lat)+','+str(endPos.lon)+'&return=summary&apikey='+key.APIKEY
    response=requests.get(getRequest)
    responseJson=response.json()
    if responseJson["routes"]:
        routingDistance=responseJson["routes"][0]['sections'][0]['summary']['length']
        return routingDistance
    else:
        print("No route found: "+startPos.lat+' '+startPos.lon+' to '+endPos.lat+' '+endPos.lon)
        return 0

def get_cost_matrix(bubblesTab):

    size = bubblesTab.bubbleNum + bubblesTab.depotNum
    cost_matrix = SymetricalMatrix(size)
    n=0
    for i in tqdm(range(size)):
        for j in tqdm(range(n), leave=False):
            cost = routing_time(bubblesTab.tab[i],bubblesTab.tab[j])
            cost_matrix.add_element(i,j,cost)
        n=n+1
    
    return cost_matrix



def save_as_csv_cost_matrix(costMatrix):
    np.savetxt('cost_matrix.csv', costMatrix.symMatrix, delimiter=',')

def get_cost_matrix_from_csv(csvName):
    costMatrix=SymetricalMatrix(0)
    costMatrix.symMatrix = np.genfromtxt(csvName, delimiter=',')
    return costMatrix

#WARNING RANDOM CHARGE
def build_bubblesTab_from_csv(csvName):
    bubblesLocation=[]
    bubblesLocation = np.genfromtxt(csvName, delimiter=',')
    bubblesTab= NodeTab()
    i=0
    for location in bubblesLocation:
        i=i+1
        charge=randint(40,90) #WARNING RANDOM CHARGE
        bubblesTab.add_bubble(Node(location[0],location[1],charge))

    #depot charge = 0
    bubblesTab.tab[-1].charge=0#Gedinne
    bubblesTab.tab[-2].charge=0#Namur
    bubblesTab.tab[-3].charge=0#Dinant
    bubblesTab.bubbleNum=bubblesTab.bubbleNum-3
    bubblesTab.depotNum=bubblesTab.depotNum+3

    return bubblesTab
    


    


#Old or few use

def update_routing_old():
    # In the graph, get the nodes closest to the points

    #area = ("Namur, Wallonia, Belgium")
    #G = ox.graph_from_place(area, network_type='drive')

    #G = ox.graph_from_bbox(north=50.817, south=50.1135, east=6.4243, west= 4.9603,  network_type='drive')#box around Liege province
    G = ox.graph_from_bbox(north=50.6497, south=59.7852, east=5.3966, west= 4.29,  network_type='drive')#box around Namur province
    # OSM data are sometime incomplete so we use the speed module of osmnx to add missing edge speeds and travel times
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    # Save graph to disk if you want to reuse it
    ox.save_graphml(G, "Namur.graphml")

def routing_distance_old(startPos,endPos):

    # Load the graph
    G = ox.load_graphml("Liege.graphml")
    origin_node = ox.get_nearest_node(G, (startPos.lat,startPos.lon))
    destination_node = ox.get_nearest_node(G, (endPos.lat,endPos.lon))

    # uncomment to see the path
    # shortest_route_by_distance = ox.shortest_path(G, origin_node, destination_node, weight='length')
    # fig, ax = ox.plot_graph_route(G, shortest_route_by_distance, route_color='y', route_linewidth=6, node_size=0)

    # Get the distance in meters
    distance_in_meters = nx.shortest_path_length(G, origin_node, destination_node, weight='length')

    # Distance in kilometers
    distance_in_kilometers = distance_in_meters / 1000
    print(distance_in_kilometers)
    return distance_in_kilometers

def routing_time_old(startPos,endPos):

    # Load the graph
    G = ox.load_graphml("Liege.graphml")

    origin_node = ox.get_nearest_node(G, (startPos.lat,startPos.lon))
    destination_node = ox.get_nearest_node(G, (endPos.lat,endPos.lon))

    #uncomment to see the path
    #shortest_route_by_time = ox.shortest_path(G, origin_node, destination_node, weight='travel_time')
    #fig, ax = ox.plot_graph_route(G, shortest_route_by_time, route_color='y', route_linewidth=6, node_size=0)

    # Get the routing time
    routing_time = nx.shortest_path_length(G, origin_node, destination_node, weight='travel_time')

    return routing_time 

def save_location_as_csv():
    test = pd.read_csv("location.csv")
    test=test.values
    location=[]
    for i in range(len(test)):
        res = tuple(map(float, test[i][0].split(',')))
        if not(res in location):
            location.append(res)
        np.savetxt('bubbleLocation.csv', location, delimiter=',')


# def main():

#     liegeBubble= NodeTab()
#     #liegeBubble.add_bubble(Node(50.640971, 5.574936,70))#université20aout
#     #liegeBubble.add_bubble(Node(50.689912, 5.569498,80))#maison
#     # liegeBubble.add_bubble(Node(50.690295, 5.246443,85))#Warrem
#     # liegeBubble.add_bubble(Node(50.658423, 5.087172,65))#Hannut
#     # liegeBubble.add_bubble(Node(50.491995, 5.862504,60))#Spa
#     # liegeBubble.add_bubble(Node(50.587739, 5.861940,75))#Vervier
#     #liegeBubble.add_bubble(Node(50.426634, 6.190871,55))#Butgenbach
#     #liegeBubble.add_bubble(Node(50.412811, 5.935814,45))#Stavelot

#     # liegeBubble.add_depot(Node(50.419553, 6.117569,0))#waimes
#     # liegeBubble.add_depot(Node(50.587781, 5.618887,0))#chaudfontaine
    

#     #liegeBubble.add_bubble(Node(52.5308,13.3847,0))
#     #liegeBubble.add_bubble(Node(41.8845,-87.6386,0))
#     # print("N=",liegeBubble.bubbleNum," M=", liegeBubble.depotNum)
#     # costMatrix=get_cost_matrix_from_csv('cost_matrix.csv')
#     # print(costMatrix.symMatrix)

#     bubblesTab = build_bubblesTab_from_csv('bubbleLocation.csv')
#     costMatrix=get_cost_matrix(bubblesTab)
#     save_as_csv_cost_matrix(costMatrix)
#     #routing_time(liegeBubble.tab[0], liegeBubble.tab[1])
#     #routing_distance(liegeBubble.tab[0], liegeBubble.tab[1])
# if __name__ == "__main__":
#     main()
    