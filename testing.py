from optimisation import *
import os

def save_result(routes,charges,times,D,B,bubblesOrDepots=None):
 
    f =open("Result_D"+str(D)+"_B"+str(B), "a+")
    f.write("Number of truck is "+str(len(routes))+"\n")
    if(bubblesOrDepots):
        f.write("Bubbles/Depots selected : "+str(bubblesOrDepots)+"\n")
    for i in range(len(routes)):
        f.write(str(routes[i])+"\n")
        f.write("Total charge: "+str(charges[i])+" Time : " +str(times[i]/60)+ " minutes or "+ str(times[i]/(60*60))+" hours\n")


def bubbles_number_test(nodesTab,costMatrix,poly):
    print("Begin test with different number of bubbles")
    bubbles=list(range(nodesTab.nbrBubbles))
    bubblesToRemove = []
    bubbleToRemove = -1
    routes = []
    charges = []
    times = []
    depotFleet=[3,3,3]
    for i in range(6):
        bubblesToRemove=[]
        if i != 0:      
            for j in range(10):
                bubbleToRemove=choice(bubbles)
                bubblesToRemove.append(bubbleToRemove)
                bubbles.remove(bubbleToRemove)

        nodesTab.remove_nodes(bubblesToRemove)
        print("Compute with "+str(nodesTab.nbrBubbles)+" bubbles")
        routesPoints, charges, times = MDVRP_optimise(nodesTab=nodesTab,costMatrix=costMatrix,nbrVehicleInDepot=depotFleet,enhanced=True)
        save_result(routesPoints,charges,times,nodesTab.nbrDepots,nodesTab.nbrBubbles,bubbles)
        
        routes=build_routes_with_polylines(routesPoints,poly)
        build_and_save_GeoJson(routes,routesPoints,nodesTab,'geo_D'+str(nodesTab.nbrDepots)+"_B"+str(nodesTab.nbrBubbles)+"_")

def depots_number_test(nodesTab,costMatrix,poly):
    print("Begin Test with different number of depots")
    depots=list(range(nodesTab.nbrBubbles,nodesTab.nbrBubbles+nodesTab.nbrDepots))
    depotsToRemove = []
    depotToRemove = -1
    routes = []
    charges = []
    times = []
    depotFleet=[20,20,20]
    for i in range(3):
        depotsToRemove=[]
        if i != 0:
            depotToRemove=choice(depots)
            depotsToRemove.append(depotToRemove)
            depots.remove(depotToRemove)
        nodesTab.remove_nodes(depotsToRemove)

        print("Compute with "+str(nodesTab.nbrDepots)+" Depots")
        routesPoints, charges, times = MDVRP_optimise(nodesTab=nodesTab,costMatrix=costMatrix,nbrVehicleInDepot=depotFleet,enhanced=True)
        save_result(routesPoints,charges,times,nodesTab.nbrDepots,nodesTab.nbrBubbles,depots)

        routes=build_routes_with_polylines(routesPoints,poly)
        build_and_save_GeoJson(routes,routesPoints,nodesTab,'geo_D'+str(nodesTab.nbrDepots)+"_B"+str(nodesTab.nbrBubbles))



def main3():
    
    nodesTab = build_nodesTab_from_csv('csv/nodes.csv')
    
    print("bubble get complete")
    costMatrix=get_cost_matrix_from_csv('csv/cost_matrix_final.csv')
    poly=get_polyline_matrix_from_csv("csv/polyline_matrix_final.csv")
    
    print("costmatrix get complete")

    bubbles_number_test(nodesTab,costMatrix,poly)
    #depots_number_test(nodesTab,costMatrix,poly)

if __name__ == "__main__":
    main3()