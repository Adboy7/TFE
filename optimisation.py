
import pulp
import itertools
import sys
from routing import *
from testing import *

def MDVRP_optimise_fleet(nodesTab,vehicle_count,costMatrix,nbrVehicleInDepot):
    nbrDepots = nodesTab.nbrDepots
    nbrBubbles = nodesTab.nbrBubbles
    nbrNodes = nbrDepots + nbrBubbles

    for vehicle_count in range(1,vehicle_count+1):
        
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
        solver=pulp.GUROBI_CMD(options=[("MIPFocus", 1),("TimeLimit", constant.GUROBI_TIME_LIMIT),("ResultFile", "Gurobi_result_D"+str(nodesTab.nbrDepots)+"_B"+str(nodesTab.nbrBubbles)+".json")])
        solve = problem.solve(solver)
       
        if solve == 1:
            print(vehicle_count)
            print('Moving Time:', pulp.value(problem.objective)/60)
            edge=[]
            for d in range(vehicle_count):
                for i in range(nbrNodes):
                    for j in range(nbrNodes):
                        if i != j and pulp.value(x[i][j][d]) == 1:
                            edge.append((i,j))
            for e in edge:
                print(e)
            routes=[]
            charges=[]
            times=[]
            for e in edge:
                if e[0] in range(nbrBubbles, nbrNodes):
                    route=[]
                    time=0
                    ca=0 
                    j=e[1]
                    route.append(nodesTab.tab[e[0]].id)
                    ca=nodesTab.tab[e[1]].charge
                    time+= costMatrix.get_element(nodesTab.tab[e[0]].id,nodesTab.tab[e[1]].id)+ constant.SERVICE_TIME
                    while(j != e[0]):
                        route.append(nodesTab.tab[j].id)
                        for e2 in edge:
                            if e2[0] == j:
                                time+= costMatrix.get_element(nodesTab.tab[j].id,nodesTab.tab[e2[1]].id) + constant.SERVICE_TIME
                                ca+=nodesTab.tab[e2[1]].charge
                                j=e2[1]
                                break
                    times.append(time)
                    charges.append(ca)
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
            pos=nx.nx_agraph.graphviz_layout(G, prog="neato")
            nx.draw(G,pos= pos, with_labels=True, labels=labels, node_color=colors)
            #plt.show() # display
            plt.savefig("Graph_D"+str(nodesTab.nbrDepots)+"_B"+str(nodesTab.nbrBubbles))
            G.clear()
            plt.clf()

            
            
            return routes,charges,times 
            
           


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



    for i in range(nbrBubbles):
        for d in range(nbrDepots):
            problem+=pulp.lpSum(x[i][d+nbrBubbles][h] if h != d else 0 for h in range(nbrDepots)) == 0
        
    for i in range(nbrBubbles):
        for d in range(nbrDepots):
            problem+=pulp.lpSum(x[d+nbrBubbles][i][h] if h != d else 0 for h in range(nbrDepots)) == 0




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
        
        

    #solve = problem.solve(pulp.GUROBI_CMD())
    #solve = problem.solve(pulp.GUROBI_CMD(options=[("MIPFocus", 1),("TimeLimit", constant.GUROBI_TIME_LIMIT)]))

    #solve=problem.solve(pulp.COIN_CMD(timeLimit=60))

    #solve=problem.solve(pulp.GLPK_CMD(options=["--tmlim", "60",]))

    solver=pulp.GUROBI_CMD(options=[("MIPFocus", 1),("TimeLimit", constant.GUROBI_TIME_LIMIT),("ResultFile", "Gurobi_result_D"+str(nodesTab.nbrDepots)+"_B"+str(nodesTab.nbrBubbles)+".json")])
    solve = problem.solve(solver)

    if solve == 1:
        print('Moving Time:', pulp.value(problem.objective)/60)
        edge=[]
        for d in range(nbrDepots):
            for i in range(nbrNodes):
                for j in range(nbrNodes):
                    if i != j and pulp.value(x[i][j][d]) == 1:
                        edge.append((i,j))
                        
        
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
                time+= costMatrix.get_element(nodesTab.tab[e[0]].id,nodesTab.tab[e[1]].id)+ constant.SERVICE_TIME
                
                while(j != e[0]):
                    route.append(nodesTab.tab[j].id)
                    for e2 in edge:
                        if e2[0] == j:
                            time+= costMatrix.get_element(nodesTab.tab[j].id,nodesTab.tab[e2[1]].id) + constant.SERVICE_TIME

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
        pos=nx.nx_agraph.graphviz_layout(G, prog="neato")
        nx.draw(G,pos= pos, with_labels=True, labels=labels, node_color=colors)
        #plt.show() # display
        plt.savefig("Graph_D"+str(nodesTab.nbrDepots)+"_B"+str(nodesTab.nbrBubbles))
        G.clear()
        plt.clf()
        return routes,charges,times

    return [],[],[]              
        


def main4():
   
   
    
    nodesTab = build_nodesTab_from_csv('csv/nodes.csv')
    
    print("bubble get complete")
    costMatrix=get_cost_matrix_from_csv('csv/cost_matrix_final.csv')
    poly=get_polyline_matrix_from_csv("csv/polyline_matrix_final.csv")
    
    print("costmatrix get complete") 
    depotFleet=[3,3,3]
    #depotFleet=[6,6,6,3,3,3,3,3,3,3]
    
    
    print(nodesTab.nbrBubbles, nodesTab.nbrDepots)
    routesPoints,a,b=MDVRP_optimise(nodesTab=nodesTab,costMatrix=costMatrix,nbrVehicleInDepot=depotFleet,enhanced=True)
    #routesPoints,a,b=MDVRP_optimise_fleet(nodesTab=nodesTab,vehicle_count=20,costMatrix=costMatrix,nbrVehicleInDepot=[3,3,3])

    routes=build_routes_with_polylines(routesPoints,poly)
    build_and_save_GeoJson(routes,routesPoints,nodesTab,'D3_B104L_')
    save_result(routesPoints,a,b,nodesTab.nbrDepots,nodesTab.nbrBubbles,[0])
    
if __name__ == "__main__":
    main4()
