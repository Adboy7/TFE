import osmnx as ox
import networkx as nx
import numpy as np
from datetime import timedelta
import timeit
import matplotlib.pyplot as plt
import pandas as pd
from random import randint,choice
from tqdm import tqdm
import flexpolyline as fp
import time
import requests
import key
import constant
import json


class Node:
    def __init__(self,lat,lon,id,charge):
        self.lat = lat
        self.lon = lon
        self.id = id
        self.charge = charge

class NodesTab:
    def __init__(self):
        self.tab=[]
        self.nbrBubbles=0
        self.nbrDepots=0

    def add_bubble(self,node):
        self.tab.insert(self.nbrBubbles, node)
        self.nbrBubbles = self.nbrBubbles+1
    
    def add_depot(self,node):
        if node.charge == 0:
            self.tab.append(node)
            self.nbrDepots = self.nbrDepots+1
        else:
            print("Depot node charge should be 0 ")

    def remove_node(self,id):
        for i in range(len(self.tab)):
            if self.tab[i].id == id:
                self.tab.remove(self.tab[i])
                if( i < self.nbrBubbles):
                    self.nbrBubbles = self.nbrBubbles-1
                else:
                    self.nbrDepots = self.nbrDepots-1
                break

    def remove_nodes(self,ids):
        for id in ids:
            self.remove_node(id)                


class SymetricalMatrix:
    
    def __init__(self, size, stype):
        intsize= (int) ((size+1) * size/2)
        if stype == "cost" :
            self.symMatrix = np.full(intsize, constant.TIME_INF)
        elif stype == "polyline":
            
            self.symMatrix = ["None"]*intsize
            
    
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
    getRequest='https://router.hereapi.com/v8/routes?transportMode=car&origin='+str(startPos.lat)+','+str(startPos.lon)+'&destination='+str(endPos.lat)+','+str(endPos.lon)+'&return=summary,polyline&apikey='+key.APIKEY
    response=requests.get(getRequest)
    responseJson=response.json()
    if not "routes" in responseJson:
        print(responseJson)
    if responseJson["routes"]:
        routingTime=responseJson["routes"][0]['sections'][0]['summary']['duration']
        polyline=responseJson["routes"][0]['sections'][0]['polyline']
        return routingTime,polyline #seconds
    else:
        print("No route found: "+startPos.lat+' '+startPos.lon+' to '+endPos.lat+' '+endPos.lon)
        return constant.TIME_INF,0
    
def routing_distance(startPos,endPos):
    getRequest='https://router.hereapi.com/v8/routes?transportMode=car&origin='+str(startPos.lat)+','+str(startPos.lon)+'&destination='+str(endPos.lat)+','+str(endPos.lon)+'&return=summary&apikey='+key.APIKEY
    response=requests.get(getRequest)
    responseJson=response.json()
    if responseJson["routes"]:
        routingDistance=responseJson["routes"][0]['sections'][0]['summary']['length']
        polyline=responseJson["routes"][0]['sections'][0]['polyline']
        return routingDistance,polyline
    else:
        print("No route found: "+startPos.lat+' '+startPos.lon+' to '+endPos.lat+' '+endPos.lon)
        return 0,0

def get_cost__and_polyline_matrix(nodesTab):

    size = nodesTab.nbrBubbles + nodesTab.nbrDepots
    costMatrix = SymetricalMatrix(size,"cost")
    polylineMatrix = SymetricalMatrix(size,"polyline")
    


    n=0
    for i in tqdm(range(size)):
        for j in tqdm(range(n), leave=False):
            #if inter depot route
            if i in range(size-nodesTab.nbrDepots,size) and j in range(size-nodesTab.nbrDepots,size):
                cost,polyline=constant.TIME_INF, "None"
            else:
                cost,polyline = routing_time(nodesTab.tab[i],nodesTab.tab[j])
            costMatrix.add_element(i,j,cost)
            polylineMatrix.add_element(i,j,polyline)
        n=n+1
    
    return costMatrix,polylineMatrix

def save_as_csv_polyline_matrix(polylineMatrix):
    np.savetxt('polyline_matrix_3D.csv', polylineMatrix.symMatrix, delimiter=',',fmt='%s')

def save_as_csv_cost_matrix(costMatrix):
    np.savetxt('cost_matrix_3D.csv', costMatrix.symMatrix, delimiter=',')

def get_cost_matrix_from_csv(csvName):
    costMatrix=SymetricalMatrix(0,"cost")
    costMatrix.symMatrix = np.genfromtxt(csvName, delimiter=',')
    return costMatrix

#WARNING RANDOM CHARGE
def build_nodesTab_from_csv(csvName):
    bubblesLocation=[]
    bubblesLocation = np.genfromtxt(csvName, delimiter=',')
    nodesTab= NodesTab()
    i=0
    for bubble in bubblesLocation:
        i=i+1
        charge=randint(400,900) #WARNING RANDOM CHARGE
        #charge=700
        #print(charge)
        nodesTab.add_bubble(Node(bubble[0],bubble[1], int(bubble[2]),charge))

    #depot charge = 0
    j=3
    for i in range(1,j+1):
        nodesTab.tab[-i].charge=0#Gedinne,Namur,Dinant
    nodesTab.nbrBubbles=nodesTab.nbrBubbles-j
    nodesTab.nbrDepots=j

    return nodesTab
    


    


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
    test = pd.read_csv("csv/location.csv")
    test=test.values
    location=[]
    nbr=[0] * 54
    for i in range(len(test)):
        res = tuple(map(float, test[i][0].split(',')))
        if not(res in location):
            location.append(res)
        else:
            nbr[location.index(res)]+=1

    for i in range(len(location)):
        print(i,location[i],nbr[i])
    #np.savetxt('bubbleLocation.csv', location, delimiter=',')


def main2():
    #save_location_as_csv()

    nodesTab = build_nodesTab_from_csv('csv/bubbleLocationid.csv')

    cost,poly = get_cost__and_polyline_matrix(nodesTab)
    save_as_csv_cost_matrix(cost)
    save_as_csv_polyline_matrix(poly)
    
    # nodesTab= NodesTab()
    # nodesTab.add_bubble(Node(50.640971, 5.574936,0,70))#université20aout 0
    # nodesTab.add_bubble(Node(50.689912, 5.569498,1,80))#maison 1
    # nodesTab.add_bubble(Node(50.491995, 5.862504,4,60))#Spa 4
    # a,b=get_cost__and_polyline_matrix(nodesTab)
    # save_as_csv_polyline_matrix(b)


    # nodesTab.add_bubble(Node(50.690295, 5.246443,2,85))#Warrem 2
    # nodesTab.add_bubble(Node(50.658423, 5.087172,3,65))#Hannut 3
    # nodesTab.add_bubble(Node(50.491995, 5.862504,4,60))#Spa 4
    # nodesTab.add_bubble(Node(50.587739, 5.861940,5,75))#Vervier 5
    # nodesTab.add_bubble(Node(50.426634, 6.190871,6,55))#Butgenbach 6
    # nodesTab.add_bubble(Node(50.412811, 5.935814,7,45))#Stavelot 7

    # nodesTab.add_depot(Node(50.419553, 6.117569,8,0))#waimes 8
    # nodesTab.add_depot(Node(50.587781, 5.618887,9,0))#chaudfontaine 9

    # nodesTab.remove_nodes([6,7,9])

    # for node in nodesTab.tab:
    #     print(node.id)
    # print(nodesTab.nbrBubbles,nodesTab.nbrDepots)

if __name__ == "__main__":
    main2()
    