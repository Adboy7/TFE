from routing import *
import pulp
import itertools
import sys


def MDVRP_optimise_fleet(bubblesTab,vehicle_count,costMatrix,Q,T,serviceTime,nbrVehicleInDepot):
    
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
        for k in range(vehicle_count):
            problem += pulp.lpSum(bubblesTab.tab[j].charge * x[i][j][k] if i != j else 0 for i in range(nbrNodes) for j in range (bubblesTab.bubbleNum)) <= Q
        
        for k in range(vehicle_count):
            problem += pulp.lpSum((costMatrix.get_element(i,j)+serviceTime) * x[i][j][k] if i != j else 0 for i in range(nbrNodes) for j in range (nbrNodes)) <= T
        
        #contraint 6 & 7

        for k in range(vehicle_count):
            problem += pulp.lpSum(x[i][j][k] if i != j else 0 
                for i in range(bubblesTab.bubbleNum) 
                for j in range(bubblesTab.bubbleNum,nbrNodes)) <= 1

        for k in range(vehicle_count):
            problem += pulp.lpSum(x[i][j][k] if i != j else 0 
            for j in range(bubblesTab.bubbleNum) 
            for i in range(bubblesTab.bubbleNum,nbrNodes)) <= 1

        for i in range(bubblesTab.bubbleNum,nbrNodes):
            problem+= pulp.lpSum(x[i][j][k]
            for k in range(vehicle_count)
            for j in range(bubblesTab.bubbleNum)) <= nbrVehicleInDepot[i-bubblesTab.bubbleNum]

        y = []
        for i in range(nbrNodes):
            y.append(pulp.LpVariable('y_' + str(i), cat='Integer'))

        for k in range(vehicle_count):
            for i in range(bubblesTab.bubbleNum):
                for j in range(bubblesTab.bubbleNum):
                    if(i != j):
                        problem += pulp.lpSum(y[i] - y[j] + nbrNodes * x[i][j][k] ) <= nbrNodes-1



        # print("subs")
        # subtours = []
        # for i in range(1,bubblesTab.bubbleNum):
        #     subtours += itertools.combinations(range(bubblesTab.bubbleNum), i)

        # print("subs2")
        # for s in subtours:  
        #     problem += pulp.lpSum(x[i][j][k] if i !=j else 0 for i, j in itertools.permutations(s,2) for k in range(vehicle_count)) <= len(s) - 1
        
        print("solving for "+ str(vehicle_count))
        solve = problem.solve(pulp.GUROBI_CMD())
        print(solve)
       
        if solve == 1:
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

            np.savetxt('edge.csv', edge, delimiter=',')
            G = nx.Graph()
            
            for node in range(nbrNodes):
                G.add_node(node, weight= node)

            G.add_edges_from(edge)
            labels = {n: G.nodes[n]['weight'] for n in G.nodes}
            colors = [G.nodes[n]['weight'] for n in G.nodes]
            nx.draw(G, with_labels=True, labels=labels, node_color=colors)
            plt.show() # display               
            break


def MDVRP_optimise(bubblesTab,costMatrix,Q,T,serviceTime,nbrVehicleInDepot,enhanced=False):
    nbrNodes = bubblesTab.bubbleNum+bubblesTab.depotNum

    problem = pulp.LpProblem("MDVRP",pulp.LpMinimize)
    #Warning due to how pulp work d go from 0-nbrdepot max and not from their position in the bubbleTab
    x = [[[pulp.LpVariable("x%s_%s,%s"%(i,j,d), cat="Binary")
        if i != j else None for d in range(bubblesTab.depotNum)]for j in range(nbrNodes)]
        for i in range(nbrNodes)]

    y = [[pulp.LpVariable("y%s,%s"%(i,d), cat="Binary")
        for d in range(bubblesTab.depotNum)]
        for i in range(nbrNodes)]

    z = [[pulp.LpVariable("z%s_%s"%(i,j), lowBound=  0, cat="Integer")
    if i != j else None for j in range(nbrNodes)]
        for i in range(nbrNodes)]

    #Minimising function
    problem += pulp.lpSum((costMatrix.get_element(i,j)+serviceTime) * x[i][j][d] if i != j else 0
                                for j in range(nbrNodes) 
                                for i in range (nbrNodes)
                                for d in range(bubblesTab.depotNum) )
    #constraint 2
    for i in range(bubblesTab.bubbleNum):
        problem += pulp.lpSum(y[i][d]for d in range(bubblesTab.depotNum)) == 1

    #constraint 4
    for i in range(bubblesTab.bubbleNum):
        for d in range(bubblesTab.depotNum):
            problem+= y[i][d] <= y[d+bubblesTab.bubbleNum][d]

    #constraint 27
    for i in range(bubblesTab.bubbleNum):
        for d in range(bubblesTab.depotNum):
            problem+= pulp.lpSum(x[i][j][d] if i != j else 0 for j in range(nbrNodes))+ \
                pulp.lpSum(x[j][i][d] if i != j else 0 for j in range(nbrNodes)) == 2*y[i][d]

    #constraint 28
    for j in range(nbrNodes):
        for d in range(bubblesTab.depotNum):
            problem+= pulp.lpSum(x[i][j][d] if i != j else 0 for i in range(nbrNodes)) == pulp.lpSum(x[j][i][d] if i != j else 0 for i in range(nbrNodes))
        
    #constraint 29
    for d in range(bubblesTab.depotNum):
        problem+= y[d+bubblesTab.bubbleNum][d] <= pulp.lpSum(x[i][j][d] if i != j else 0 for i in range(nbrNodes) for j in range(nbrNodes) )

    #constraint 30
    for d in range(bubblesTab.depotNum):
        problem+= 2*y[d+bubblesTab.bubbleNum][d] <= pulp.lpSum(x[j][d+bubblesTab.bubbleNum][d] for j in range(bubblesTab.bubbleNum) ) + \
            pulp.lpSum(x[d+bubblesTab.bubbleNum][j][d] for j in range(bubblesTab.bubbleNum) )  

    #constraint 31
    for j in range(bubblesTab.bubbleNum):
        problem+= pulp.lpSum(z[i][j] if i != j else 0 for i in range(nbrNodes) ) - pulp.lpSum(z[j][i] if i != j else 0 for i in range(nbrNodes) )\
            == bubblesTab.tab[j].charge

    #constraint 32
    problem+= pulp.lpSum(z[d+bubblesTab.bubbleNum][j] for d in range(bubblesTab.depotNum) for j in range(bubblesTab.bubbleNum))\
        == pulp.lpSum(bubblesTab.tab[j].charge for j in range(bubblesTab.bubbleNum))
    
    #constraint 33
    for i in range(nbrNodes):
        for j in range(bubblesTab.bubbleNum):
            if i != j:
                problem+= z[i][j] <= pulp.lpSum((Q-bubblesTab.tab[i].charge)*x[i][j][d] for d in range(bubblesTab.depotNum) )

    if (enhanced == True):      
        #constraint 37
        for i in range(bubblesTab.bubbleNum):
            for j in range(bubblesTab.bubbleNum):
                if i != j :
                    problem+=z[i][j] >= pulp.lpSum(bubblesTab.tab[j].charge*x[i][j][d] if i != j else 0 for d in range(bubblesTab.depotNum))
        #constraint 38
        for j in range(bubblesTab.bubbleNum):
            problem+= pulp.lpSum(x[i][j][d] if i != j else 0 for i in range(nbrNodes) for d in range(bubblesTab.depotNum))==1
         #constraint 39
        for i in range(bubblesTab.bubbleNum):
            problem+= pulp.lpSum(x[i][j][d] if i != j else 0 for j in range(nbrNodes) for d in range(bubblesTab.depotNum))==1
        #constraint 40
        for i in range(bubblesTab.bubbleNum):
            for d in range(bubblesTab.depotNum):
                problem+=x[i][d+bubblesTab.bubbleNum][d] <= y[i][d]
        #constraint 41
        for i in range(bubblesTab.bubbleNum):
            for d in range(bubblesTab.depotNum):
                problem+=x[d+bubblesTab.bubbleNum][i][d] <= y[i][d]
        #constraint 42
        for i in range(bubblesTab.bubbleNum):
            for j in range(bubblesTab.bubbleNum):
                if i != j :
                    for d in range(bubblesTab.depotNum):
                        problem+=x[i][j][d] + y[i][d] + pulp.lpSum(y[j][h] if h != d else 0 for h in range(bubblesTab.depotNum)) <= 2
        #constraint 43
        for i in range(bubblesTab.bubbleNum):
            for j in range(bubblesTab.bubbleNum):
                if i != j :
                    for d in range(bubblesTab.depotNum):
                        problem+=x[i][j][d]+x[j][i][d] <= 1
        #constraint 44
        problem+= (pulp.lpSum(bubblesTab.tab[i].charge for i in range(bubblesTab.bubbleNum))) / (Q) <= pulp.lpSum(x[d+bubblesTab.bubbleNum][i][d] 
                                                                                                            for i in range(bubblesTab.bubbleNum) 
                                                                                                            for d in range(bubblesTab.depotNum))
        #constraint vehicle in depot
        for d in range(bubblesTab.depotNum):
            problem+= pulp.lpSum(x[d+bubblesTab.bubbleNum][i][d] if d+bubblesTab.bubbleNum != i else 0 for i in range(nbrNodes)) <= nbrVehicleInDepot[d]



    #solve = problem.solve(pulp.GUROBI_CMD())
    solve = problem.solve(pulp.GUROBI_CMD(options=[("MIPFocus", 1),("TimeLimit", 600)]))
    print(solve)

    if solve == 1:
        print('Moving Time:', pulp.value(problem.objective)/60)
        
        edge=[]
        chargeleft=[]
        time=0
        charge=0
        for d in range(bubblesTab.depotNum):
            for i in range(nbrNodes):
                for j in range(nbrNodes):
                    if i != j and pulp.value(x[i][j][d]) == 1:
                        edge.append((i,j))
                        chargeleft.append(z[i][j])
                        time=time+costMatrix.get_element(i,j)+serviceTime
                        charge=charge+bubblesTab.tab[j].charge
                        print("depot ", d+bubblesTab.bubbleNum," i== ",i," j== ",j," z==", pulp.value(z[i][j]))


            time=0
            charge=0

        np.savetxt('edge.csv', edge, delimiter=',')
        G = nx.Graph()
        
        for node in range(nbrNodes):
            G.add_node(node, weight= node)

        G.add_edges_from(edge)
        labels = {n: G.nodes[n]['weight'] for n in G.nodes}
        colors = [G.nodes[n]['weight'] for n in G.nodes]
        nx.draw(G, with_labels=True, labels=labels, node_color=colors)
        plt.show() # display               
        


def main():
    

    # bubblesTab= NodeTab()
    # bubblesTab.add_bubble(Node(50.640971, 5.574936,70))#université20aout 0
    # bubblesTab.add_bubble(Node(50.689912, 5.569498,80))#maison 1
    # bubblesTab.add_bubble(Node(50.690295, 5.246443,85))#Warrem 2
    # bubblesTab.add_bubble(Node(50.658423, 5.087172,65))#Hannut 3
    # bubblesTab.add_bubble(Node(50.491995, 5.862504,60))#Spa 4
    # bubblesTab.add_bubble(Node(50.587739, 5.861940,75))#Vervier 5
    # bubblesTab.add_bubble(Node(50.426634, 6.190871,55))#Butgenbach 6
    # bubblesTab.add_bubble(Node(50.412811, 5.935814,45))#Stavelot 7

    # bubblesTab.add_depot(Node(50.419553, 6.117569,0))#waimes 8
    # bubblesTab.add_depot(Node(50.587781, 5.618887,0))#chaudfontaine 9
    
    # print("N=",bubblesTab.bubbleNum," M=", bubblesTab.depotNum)
    # costMatrix=get_cost_matrix_from_csv('csv/cost_matrix_old.csv')
    # MDVRP_optimise(bubblesTab=bubblesTab,vehicle_count=10,costMatrix=costMatrix,Q=150,T=6*60*60,serviceTime=600,depotFleet=[10,10])
    





    bubblesTab = build_bubblesTab_from_csv('csv/bubbleLocation.csv')
    
    print("bubble get complete")
    costMatrix=get_cost_matrix_from_csv('csv/cost_matrix_3.csv')
   
    
    print("costmatrix get complete") 
    depotFleet=[2,2,2]
    #MDVRP_optimise_fleet(bubblesTab=bubblesTab,vehicle_count=1000,costMatrix=costMatrix,Q=7000,T=6*60*60,serviceTime=600,depotFleet=[10,10,20])
    MDVRP_optimise(bubblesTab=bubblesTab,costMatrix=costMatrix,Q=7000,T=170*60,serviceTime=600,nbrVehicleInDepot=depotFleet,enhanced=True)

    
if __name__ == "__main__":
    main()
