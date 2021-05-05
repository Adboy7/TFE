from priority import *
from optimisation import *

def main():
    tab=get_data_n_day_from_now('csv/data.csv',365)
    nodesTab = build_nodesTab_from_csv('csv/nodes.csv')
    toRemove=update_charge(nodesTab,tab,50)
    nodesTab.remove_nodes(toRemove)
    for node in nodesTab.tab:
        print(node.id,node.charge)
    print("bubble get complete")
    costMatrix=get_cost_matrix_from_csv('csv/cost_matrix_final.csv')
    poly=get_polyline_matrix_from_csv("csv/polyline_matrix_final.csv")
    
    print("costmatrix get complete") 
    depotFleet=[20,20,20]
    print(nodesTab.nbrBubbles, nodesTab.nbrDepots)
    routesPoints,a,b=MDVRP_optimise(nodesTab=nodesTab,costMatrix=costMatrix,nbrVehicleInDepot=depotFleet,enhanced=True)
    routes=build_routes_with_polylines(routesPoints,poly)
    build_and_save_GeoJson(routes,routesPoints,nodesTab,'test1')

if __name__ == "__main__":
    main()