from routing import *
import pulp
import itertools



def MDVRP_optimise(bubblesTab,vehicle_count,costMatrix,Q,T,serviceTime):
    
    for vehicle_count in range(1,vehicle_count+1):

        nbrNodes = bubblesTab.bubbleNum+bubblesTab.depotNum
        
        problem = pulp.LpProblem("MDVRP",pulp.LpMinimize)
        x = [[[pulp.LpVariable("x%s_%s,%s"%(i,j,k), cat="Binary")
        if i != j else None for k in range(vehicle_count)]for j in range(nbrNodes)]
        for i in range(nbrNodes)]

        #objectif fonction to minimise
        problem += pulp.lpSum((costMatrix.get_element(i,j)+serviceTime) * x[i][j][k] if i != j else 0
                                for k in range(vehicle_count) 
                                for j in range(nbrNodes) 
                                for i in range (nbrNodes)) 

        #constraint 1 & 2 
        for j in range( bubblesTab.bubbleNum):
            problem += pulp.lpSum(x[i][j][k] if i != j else 0 
                                for i in range(nbrNodes) 
                                for k in range(vehicle_count)) == 1

        for i in range( bubblesTab.bubbleNum):
            problem += pulp.lpSum(x[i][j][k] if i != j else 0 
                for j in range(nbrNodes) 
                for k in range(vehicle_count)) == 1 

        #constraint 3
        for k in range(vehicle_count):
            for j in range(nbrNodes):
                problem += pulp.lpSum(x[i][j][k] if i != j else 0 
                    for i in range(nbrNodes)) -  pulp.lpSum(x[j][i][k] for i in range(nbrNodes)) == 0
        #constraint 4 & 5
        charge=[70,80,85,65,60,75,55,45,0,0]
        for k in range(vehicle_count):
            problem += pulp.lpSum(bubblesTab.tab[j].charge * x[i][j][k] if i != j else 0 for i in range(nbrNodes) for j in range (bubblesTab.bubbleNum)) <= Q
        
        for k in range(vehicle_count):
            problem += pulp.lpSum((costMatrix.get_element(i,j)+serviceTime) * x[i][j][k] if i != j else 0 for i in range(nbrNodes) for j in range (nbrNodes)) <= T
        #contraint 6 & 7

        for k in range(vehicle_count):
            problem += pulp.lpSum(x[i][j][k] if i != j else 0 
                for i in range(nbrNodes) 
                for j in range(bubblesTab.bubbleNum,nbrNodes)) <= 1

        for k in range(vehicle_count):
            problem += pulp.lpSum(x[i][j][k] if i != j else 0 
            for j in range(nbrNodes) 
            for i in range(bubblesTab.bubbleNum,nbrNodes)) <= 1
        
        subtours = []
        for i in range(1,bubblesTab.bubbleNum):
            subtours += itertools.combinations(range(bubblesTab.bubbleNum), i)

        for s in subtours:  
            problem += pulp.lpSum(x[i][j][k] if i !=j else 0 for i, j in itertools.permutations(s,2) for k in range(vehicle_count)) <= len(s) - 1

        if problem.solve() == 1:
            print('Vehicle Requirements:', vehicle_count)
            print('Moving Time:', pulp.value(problem.objective)/60)
            
            edge=[]
            time=0
            charge=0
            for k in range(vehicle_count):
                for i in range(nbrNodes):
                    for j in range(nbrNodes):
                        if i != j and pulp.value(x[i][j][k]) == 1:
                            edge.append((i,j))
                            time=time+costMatrix.get_element(i,j)+serviceTime
                            charge=charge+bubblesTab.tab[j].charge
                print("Truck ", k, " will take ", time/60," minutes and will take ",charge," kg")
                time=0
                charge=0


            G = nx.Graph()
            
            for node in range(nbrNodes):
                G.add_node(node, weight= node)

            G.add_edges_from(edge)
            labels = {n: G.nodes[n]['weight'] for n in G.nodes}
            colors = [G.nodes[n]['weight'] for n in G.nodes]
            nx.draw(G, with_labels=True, labels=labels, node_color=colors)
            plt.show() # display               
            break



def main():
    

    # liegeBubble= NodeTab()
    # liegeBubble.add_bubble(Node(50.640971, 5.574936,70))#université20aout 0
    # liegeBubble.add_bubble(Node(50.689912, 5.569498,80))#maison 1
    # liegeBubble.add_bubble(Node(50.690295, 5.246443,85))#Warrem 2
    # liegeBubble.add_bubble(Node(50.658423, 5.087172,65))#Hannut 3
    # liegeBubble.add_bubble(Node(50.491995, 5.862504,60))#Spa 4
    # liegeBubble.add_bubble(Node(50.587739, 5.861940,75))#Vervier 5
    # liegeBubble.add_bubble(Node(50.426634, 6.190871,55))#Butgenbach 6
    # liegeBubble.add_bubble(Node(50.412811, 5.935814,45))#Stavelot 7

    # liegeBubble.add_depot(Node(50.419553, 6.117569,0))#waimes 8
    # liegeBubble.add_depot(Node(50.587781, 5.618887,0))#chaudfontaine 9
    
    #print("N=",liegeBubble.bubbleNum," M=", liegeBubble.depotNum)
    bubblesTab = build_bubblesTab_from_csv('bubbleLocation.csv')
    print("bubble get complete")
    costMatrix=get_cost_matrix_from_csv('cost_matrix.csv')
    print("costmatrix get complete")
    print(bubblesTab.tab[56].lat)
    MDVRP_optimise(bubblesTab=bubblesTab,vehicle_count=10,costMatrix=costMatrix,Q=180,T=6*60*60,serviceTime=600)
    
if __name__ == "__main__":
    main()
