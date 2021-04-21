from optimisation import *
import os

def save_result(routes,charges,times,D,B,bubbles=None):
 
    f =open("Result_D"+str(D)+"_B"+str(B), "a+")
    f.write("Number of truck is "+str(len(routes))+"\n")
    if(bubbles):
        f.write("Bubbles selected : "+str(bubbles)+"\n")
    for i in range(len(routes)):
        f.write(str(routes[i])+"\n")
        f.write("Total charge: "+str(charges[i])+" Time : " +str(times[i]/60)+ " minutes or "+ str(times[i]/(60*60))+" hours\n")


def bubbles_number_test(nodesTab,costMatrix):
    print("Begin test with different number of bubbles")
    bubbles=list(range(nodesTab.nbrBubbles))
    bubblesToRemove = []
    bubbleToRemove = -1
    routes = []
    charges = []
    times = []
    depotFleet=[20,20,20]
    for i in range(6):
        bubblesToRemove=[]
        if i != 0:      
            for j in range(10):
                bubbleToRemove=choice(bubbles)
                bubblesToRemove.append(bubbleToRemove)
                bubbles.remove(bubbleToRemove)

        nodesTab.remove_nodes(bubblesToRemove)
        print("Compute with "+str(nodesTab.nbrBubbles)+" bubbles")
        routes, charges, times = MDVRP_optimise(nodesTab=nodesTab,costMatrix=costMatrix,nbrVehicleInDepot=depotFleet,enhanced=True)
        save_result(routes,charges,times,nodesTab.nbrDepots,nodesTab.nbrBubbles,bubbles)




def main3():
    
    nodesTab = build_nodesTab_from_csv('csv/bubbleLocationid.csv')
    
    print("bubble get complete")
    costMatrix=get_cost_matrix_from_csv('csv/cost_matrix_3D.csv')
   
    
    print("costmatrix get complete")

    bubbles_number_test(nodesTab,costMatrix)

if __name__ == "__main__":
    main3()