from routing import *
import pulp
import itertools
import sys


def MDVRP_optimise_fleet(nodesTab,vehicle_count,costMatrix,nbrVehicleInDepot):
    nbrDepots = nodesTab.nbrDepots
    nbrBubbles = nodesTab.nbrBubbles
    nbrNodes = nbrDepots + nbrBubbles

    for vehicle_count in range(1,vehicle_count+1):
        nbrNodes = nbrBubbles+nbrDepots
        
        problem = pulp.LpProblem("MDVRP",pulp.LpMinimize)
        x = [[[pulp.LpVariable("x%s_%s,%s"%(i,j,k), cat="Binary")
        if i != j else None for k in range(vehicle_count)]for j in range(nbrNodes)]
        for i in range(nbrNodes)]

        #objectif fonction to minimise
        problem += pulp.lpSum((costMatrix.get_element(nodesTab.tab[i].id,nodesTab.tab[j].id)+constant.SERVICE_TIME) * x[i][j][k] if i != j else 0
                                for k in range(vehicle_count) 
                                for j in range(nbrNodes) 
                                for i in range(nbrNodes)) 
        

        #constraint 1 & 2 
        for j in range(nbrBubbles):
            problem += pulp.lpSum(x[i][j][k] if i != j else 0 
                                for i in range(nbrNodes) 
                                for k in range(vehicle_count)) == 1

        for i in range(nbrBubbles):
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
            problem += pulp.lpSum(nodesTab.tab[j].charge * x[i][j][k] if i != j else 0 for i in range(nbrNodes) for j in range(nbrBubbles)) <= constant.Q
        
        for k in range(vehicle_count):
            problem += pulp.lpSum((costMatrix.get_element(nodesTab.tab[i].id,nodesTab.tab[j].id)+constant.SERVICE_TIME) * x[i][j][k] if i != j else 0 for i in range(nbrNodes) for j in range(nbrNodes)) <= constant.T
        
        #contraint 6 & 7

        for k in range(vehicle_count):
            problem += pulp.lpSum(x[i][j][k] if i != j else 0 
                for i in range(nbrBubbles) 
                for j in range(nbrBubbles, nbrNodes)) <= 1

        for k in range(vehicle_count):
            problem += pulp.lpSum(x[i][j][k] if i != j else 0 
            for j in range(nbrBubbles) 
            for i in range(nbrBubbles, nbrNodes)) <= 1

        for i in range(nbrBubbles, nbrNodes):
            problem+= pulp.lpSum(x[i][j][k]
            for k in range(vehicle_count)
            for j in range(nbrBubbles)) <= nbrVehicleInDepot[i-nbrBubbles]

        y = []
        for i in range(nbrNodes):
            y.append(pulp.LpVariable('y_' + str(i), cat='Integer'))

        for k in range(vehicle_count):
            for i in range(nbrBubbles):
                for j in range(nbrBubbles):
                    if(i != j):
                        problem += pulp.lpSum(y[i] - y[j] + nbrNodes * x[i][j][k] ) <= nbrNodes-1



        # print("subs")
        # subtours = []
        # for i in range(1,nbrBubbles):
        #     subtours += itertools.combinations(range(nbrBubbles), i)

        # print("subs2")
        # for s in subtours:  
        #     problem += pulp.lpSum(x[i][j][k] if i !=j else 0 for i, j in itertools.permutations(s,2) for k in range(vehicle_count)) <= len(s) - 1
        
        print("solving for "+ str(vehicle_count))
        solve = problem.solve(pulp.GUROBI_CMD(options=[("TimeLimit", 10)]))
       
        if solve == 1:
            print(vehicle_count)
            # print('Vehicle Requirements:', vehicle_count)
            # print('Moving Time:', pulp.value(problem.objective)/60)
            
            # edge=[]
            # time=0
            # charge=0
            # for k in range(vehicle_count):
            #     for i in range(nbrNodes):
            #         for j in range(nbrNodes):
            #             if i != j and pulp.value(x[i][j][k]) == 1:
            #                 edge.append((i,j))
            #                 time=time+costMatrix.get_element(nodesTab.tab[i].id,nodesTab.tab[j].id)+constant.SERVICE_TIME
            #                 charge=charge+nodesTab.tab[j].charge
            #     print("Truck ", k, " will take ", time/60," minutes and will take ",charge," kg")
            #     time=0
            #     charge=0

            # np.savetxt('edge.csv', edge, delimiter=',')
            # G = nx.Graph()
            
            # for node in range(nbrNodes):
            #     G.add_node(node, weight= node)

            # G.add_edges_from(edge)
            # labels = {n: G.nodes[n]['weight'] for n in G.nodes}
            # colors = [G.nodes[n]['weight'] for n in G.nodes]
            # nx.draw(G, with_labels=True, labels=labels, node_color=colors)
            # plt.show() # display               
            # break


def MDVRP_optimise(nodesTab,costMatrix,nbrVehicleInDepot,enhanced=False):
    
    nbrDepots = nodesTab.nbrDepots
    nbrBubbles = nodesTab.nbrBubbles
    nbrNodes = nbrBubbles+nbrDepots


    problem = pulp.LpProblem("MDVRP",pulp.LpMinimize)
    #Warning due to how pulp work d go from 0-nbrdepot max and not from their position in the bubbleTab
    x = [[[pulp.LpVariable("x%s_%s,%s"%(i,j,d), cat="Binary")
        if i != j else None for d in range(nbrDepots)]for j in range(nbrNodes)]
        for i in range(nbrNodes)]

    y = [[pulp.LpVariable("y%s,%s"%(i,d), cat="Binary")
        for d in range(nbrDepots)]
        for i in range(nbrNodes)]

    z = [[pulp.LpVariable("z%s_%s"%(i,j), lowBound=  0, cat="Integer")
    if i != j else None for j in range(nbrNodes)]
        for i in range(nbrNodes)]

    #Minimising function
    problem += pulp.lpSum((costMatrix.get_element(nodesTab.tab[i].id, nodesTab.tab[j].id)+constant.SERVICE_TIME) * x[i][j][d] if i != j else 0
                                for j in range(nbrNodes) 
                                for i in range(nbrNodes)
                                for d in range(nbrDepots) )
    #constraint 2
    for i in range(nbrBubbles):
        problem += pulp.lpSum(y[i][d]for d in range(nbrDepots)) == 1

    #constraint 4
    for i in range(nbrBubbles):
        for d in range(nbrDepots):
            problem+= y[i][d] <= y[d+nbrBubbles][d]

    #constraint 27
    for i in range(nbrBubbles):
        for d in range(nbrDepots):
            problem+= pulp.lpSum(x[i][j][d] if i != j else 0 for j in range(nbrNodes))+ \
                pulp.lpSum(x[j][i][d] if i != j else 0 for j in range(nbrNodes)) == 2*y[i][d]

    #constraint 28
    for j in range(nbrNodes):
        for d in range(nbrDepots):
            problem+= pulp.lpSum(x[i][j][d] if i != j else 0 for i in range(nbrNodes)) == pulp.lpSum(x[j][i][d] if i != j else 0 for i in range(nbrNodes))
        
    #constraint 29
    for d in range(nbrDepots):
        problem+= y[d+nbrBubbles][d] <= pulp.lpSum(x[i][j][d] if i != j else 0 for i in range(nbrNodes) for j in range(nbrNodes) )

    #constraint 30
    for d in range(nbrDepots):
        problem+= 2*y[d+nbrBubbles][d] <= pulp.lpSum(x[j][d+nbrBubbles][d] for j in range(nbrBubbles) ) + \
            pulp.lpSum(x[d+nbrBubbles][j][d] for j in range(nbrBubbles) )  

    #constraint 31
    for j in range(nbrBubbles):
        problem+= pulp.lpSum(z[i][j] if i != j else 0 for i in range(nbrNodes) ) - pulp.lpSum(z[j][i] if i != j else 0 for i in range(nbrNodes) )\
            == nodesTab.tab[j].charge

    #constraint 32
    problem+= pulp.lpSum(z[d+nbrBubbles][j] for d in range(nbrDepots) for j in range(nbrBubbles))\
        == pulp.lpSum(nodesTab.tab[j].charge for j in range(nbrBubbles))
    
    #constraint 33
    for i in range(nbrNodes):
        for j in range(nbrBubbles):
            if i != j:
                problem+= z[i][j] <= pulp.lpSum((constant.Q-nodesTab.tab[i].charge)*x[i][j][d] for d in range(nbrDepots) )

    if (enhanced == True):      
        #constraint 37
        for i in range(nbrBubbles):
            for j in range(nbrBubbles):
                if i != j :
                    problem+=z[i][j] >= pulp.lpSum(nodesTab.tab[j].charge*x[i][j][d] if i != j else 0 for d in range(nbrDepots))
        #constraint 38
        for j in range(nbrBubbles):
            problem+= pulp.lpSum(x[i][j][d] if i != j else 0 for i in range(nbrNodes) for d in range(nbrDepots))==1
         #constraint 39
        for i in range(nbrBubbles):
            problem+= pulp.lpSum(x[i][j][d] if i != j else 0 for j in range(nbrNodes) for d in range(nbrDepots))==1
        #constraint 40
        for i in range(nbrBubbles):
            for d in range(nbrDepots):
                problem+=x[i][d+nbrBubbles][d] <= y[i][d]
        #constraint 41
        for i in range(nbrBubbles):
            for d in range(nbrDepots):
                problem+=x[d+nbrBubbles][i][d] <= y[i][d]
        #constraint 42
        for i in range(nbrBubbles):
            for j in range(nbrBubbles):
                if i != j :
                    for d in range(nbrDepots):
                        problem+=x[i][j][d] + y[i][d] + pulp.lpSum(y[j][h] if h != d else 0 for h in range(nbrDepots)) <= 2
        #constraint 43
        for i in range(nbrBubbles):
            for j in range(nbrBubbles):
                if i != j :
                    for d in range(nbrDepots):
                        problem+=x[i][j][d]+x[j][i][d] <= 1
        #constraint 44
        problem+= (pulp.lpSum(nodesTab.tab[i].charge for i in range(nbrBubbles))) / (constant.Q) <= pulp.lpSum(x[d+nbrBubbles][i][d] 
                                                                                                            for i in range(nbrBubbles) 
                                                                                                            for d in range(nbrDepots))
        #constraint vehicle in depot
        for d in range(nbrDepots):
            problem+= pulp.lpSum(x[d+nbrBubbles][i][d] for i in range(nbrBubbles)) <= nbrVehicleInDepot[d]

        #time light constraint
        problem+=pulp.lpSum((costMatrix.get_element(nodesTab.tab[i].id,nodesTab.tab[j].id)+constant.SERVICE_TIME) * x[i][j][d] if i != j else 0
                                for j in range(nbrNodes) 
                                for i in range(nbrNodes)
                                for d in range(nbrDepots) ) <= constant.T * pulp.lpSum(x[d+nbrBubbles][i][d] 
                                                                            for i in range(nbrBubbles)
                                                                            for d in range(nbrDepots)) 
        
        for d in range(nbrDepots):
            for i in range(nbrBubbles):
                i

    #solve = problem.solve(pulp.GUROBI_CMD())
    #solve = problem.solve(pulp.GUROBI_CMD(options=[("MIPFocus", 1),("TimeLimit", constant.GUROBI_TIME_LIMIT)]))
    solver=pulp.GUROBI_CMD(options=[("MIPFocus", 1),("TimeLimit", constant.GUROBI_TIME_LIMIT),("ResultFile", "Gurobi_result_D"+str(nodesTab.nbrDepots)+"_B"+str(nodesTab.nbrBubbles)+".json")])
    solve = problem.solve(solver)
    print(solve)

    if solve == 1:
        print('Moving Time:', pulp.value(problem.objective)/60)
        print(solver)
        edge=[]
        chargeleft=[]
        time=0
        charge=0
        for d in range(nbrDepots):
            for i in range(nbrNodes):
                for j in range(nbrNodes):
                    if i != j and pulp.value(x[i][j][d]) == 1:
                        edge.append((i,j))
                        chargeleft.append(z[i][j])
                        time=time+costMatrix.get_element(nodesTab.tab[i].id,nodesTab.tab[j].id)+constant.SERVICE_TIME
                        charge=charge+nodesTab.tab[j].charge
                        print("depot ", d+nbrBubbles," i== ",i," j== ",j," z==", pulp.value(z[i][j]))
            time=0
            charge=0

        routes=[]
        charges=[]
        times=[]
        for e in edge:
            if e[0] in range(nbrBubbles, nbrNodes):
                route=[]
                time=0
                j=e[1]
                route.append(nodesTab.tab[e[0]].id)
                charges.append(pulp.value(z[e[0]][e[1]]))
                time+= costMatrix.get_element(e[0],e[1]) + constant.SERVICE_TIME
                while(j != e[0]):
                    route.append(nodesTab.tab[j].id)
                    for e2 in edge:
                        if e2[0] == j:
                            time+= costMatrix.get_element(j,e2[1]) + constant.SERVICE_TIME
                            j=e2[1]
                            break
                times.append(time)
                route.append(nodesTab.tab[e[0]].id)
                routes.append(route)
        
        for i in range(len(routes)):
            print(routes[i])
            print("Total charge: ",charges[i]," Time : ", times[i]/60, " minutes or ",times[i]/(60*60)," hours")
            print("----")


                


        G = nx.Graph()
        
        for node in range(nbrNodes):
            G.add_node(node, weight=nodesTab.tab[node].id )

        G.add_edges_from(edge)
        labels = {n: G.nodes[n]['weight'] for n in G.nodes}
        colors = [G.nodes[n]['weight'] for n in G.nodes]
        nx.draw(G, with_labels=True, labels=labels, node_color=colors)
        #plt.show() # display
        plt.savefig("Graph_D"+str(nodesTab.nbrDepots)+"_B"+str(nodesTab.nbrBubbles))
        G.clear
        return routes,charges,times              
        


def main():
    # nodesTab= NodesTab()
    # nodesTab.add_bubble(Node(50.640971, 5.574936,0,70))#université20aout 0
    # nodesTab.add_bubble(Node(50.689912, 5.569498,1,80))#maison 1
    # nodesTab.add_bubble(Node(50.690295, 5.246443,2,85))#Warrem 2
    # nodesTab.add_bubble(Node(50.658423, 5.087172,3,65))#Hannut 3
    # nodesTab.add_bubble(Node(50.491995, 5.862504,4,60))#Spa 4
    # nodesTab.add_bubble(Node(50.587739, 5.861940,5,75))#Vervier 5
    # nodesTab.add_bubble(Node(50.426634, 6.190871,6,55))#Butgenbach 6
    # nodesTab.add_bubble(Node(50.412811, 5.935814,7,45))#Stavelot 7

    # nodesTab.add_depot(Node(50.419553, 6.117569,8,0))#waimes 8
    # nodesTab.add_depot(Node(50.587781, 5.618887,9,0))#chaudfontaine 9
    
    
    # costMatrix=get_cost_matrix_from_csv('csv/cost_matrix_old.csv')
    # MDVRP_optimise(nodesTab=nodesTab,costMatrix=costMatrix,nbrVehicleInDepot=[10,10])
    
    nodesTab = build_nodesTab_from_csv('csv/bubbleLocationid.csv')
    
    print("bubble get complete")
    costMatrix=get_cost_matrix_from_csv('csv/cost_matrix_3.csv')
   
    
    print("costmatrix get complete") 
    depotFleet=[20,20,20]
    #MDVRP_optimise_fleet(nodesTab=nodesTab,vehicle_count=1000,costMatrix=costMatrix,Q=7000,T=6*60*60depotFleet=[10,10,20])
    #MDVRP_optimise_fleet(nodesTab=nodesTab,vehicle_count=1000,costMatrix=costMatrix,nbrVehicleInDepot=depotFleet)
    a=[1,2,3,4,5,6,7,10,15,16,17,19,21,22,24,26,28,31,32,33,35,39,40,45,46,50,54]
    l=list(range(42))
    nodesTab.remove_nodes(a)
    print(nodesTab.nbrBubbles, nodesTab.nbrDepots)
    MDVRP_optimise(nodesTab=nodesTab,costMatrix=costMatrix,nbrVehicleInDepot=depotFleet,enhanced=True)

    
if __name__ == "__main__":
    main()
