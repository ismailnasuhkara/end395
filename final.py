from pyomo.environ import *
from pyomo.environ import value
import pandas as pd
import time

start_time = time.time()

orders = pd.read_excel("Part2-Scenario1.xlsx", sheet_name="Orders")
pallets = pd.read_excel("Part2-Scenario1.xlsx", sheet_name="Pallets")
vehicles = pd.read_excel("Part2-Scenario1.xlsx", sheet_name="Vehicles")
parameters = pd.read_excel("Part2-Scenario1.xlsx", sheet_name="Parameters")
loading_types = pd.read_excel("Part2-Scenario1.xlsx", sheet_name="LoadingTypes")


end_time = time.time()
print(f"Extracted data.\nCPU Time: {end_time - start_time} seconds\n")

model = ConcreteModel()

# Sets
model.planning_horizon = Set(initialize=range(1, parameters['Value'].iloc[0] + 1), doc="Set of days in the planning horizon")
model.pallets = Set(initialize=pallets['Pallet ID'], doc="Set of pallets")
model.orders = Set(initialize=orders['Order ID'], doc="Set of orders")
model.product_type = Set(initialize=orders['Product Type'].unique(), doc="Set of product types") 
model.vehicles = Set(initialize=vehicles["Vehicle ID"], doc="Set of owned vehicles")
model.rentable = Set(initialize=range(1, 40), doc="Set of rentable vehicles")
vehicle_type_list = [int(k) for k in list(vehicles["Vehicle Type"].unique())]
model.vehicle_type = Set(initialize=vehicle_type_list, doc="Set of vehicle types")
model.type_1_loading_types = Set(initialize=loading_types[loading_types["VehicleType"] == 1]["LoadingType"])
model.type_2_loading_types = Set(initialize=loading_types[loading_types["VehicleType"] == 2]["LoadingType"])
model.type_3_loading_types = Set(initialize=loading_types[loading_types["VehicleType"] == 3]["LoadingType"])

end_time = time.time()
print(f"Initialized sets.\nCPU Time: {end_time - start_time} seconds\n")

# Parameters
model.products_in_pallet = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Amount'].to_dict(), doc="Number of products that can be stored in each pallet", mutable=False)
# 1 = 100x120 cm, 2 = 80x120 cm
model.pallet_size = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Pallet Size'].to_dict(), doc="Size of each pallet", mutable=False)
model.pallet_release_day = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Release Day'].to_dict(), within=PositiveIntegers, doc="The release day of each pallet", mutable=False)
model.order_demand = Param(model.orders, model.product_type, initialize=orders.set_index(["Order ID","Product Type"])['Demand Amount'].to_dict(), default=0, doc="Number of products required for each order", mutable=False)
model.order_due_date = Param(model.orders, initialize=orders.set_index('Order ID')['Due Date'].to_dict(), doc="Due date of each order", mutable=False)
model.warehouse_storage = Param(initialize=parameters['Value'].iloc[2], doc="Warehouse storage capacity in terms of pallets", mutable=False)
model.earliness_penalty = Param(model.orders, initialize=orders.set_index('Order ID')['Earliness Penalty'].to_dict(), doc="Earliness penalty cost of each order", mutable=False)
model.owned_vehicle_cost = Param(model.vehicles, initialize=vehicles.set_index('Vehicle ID')['Fixed Cost (c_k)'].to_dict(), doc="Delivery cost of each owned vehicle", mutable=False)
model.rented_vehicle_cost = Param(model.vehicle_type, initialize=vehicles.set_index('Vehicle Type')['Variable Cost (c\'_k)'].to_dict(), doc="Delivery cost of each rented vehicle", mutable=False)    
# Truck = 22, Lorry = 12, Van = 6
# model.vehicle_capacity_100x120 = Param(model.vehicles, initialize=vehicles.set_index('Vehicle ID')['Capacity for pallet type 1'].to_dict(), doc="Capacity of each vehicle type for 100x120 cm pallets", mutable=False)
# Truck = 33, Lorry = 18, Van = 8
# model.vehicle_capacity_80x120 = Param(model.vehicles, initialize=vehicles.set_index('Vehicle ID')['Capacity for pallet type 2'].to_dict(), doc="Capacity of each vehicle type for 80x120 cm pallets", mutable=False)
# model.rented_capacity_100x120 = Param(model.vehicle_type, initialize=vehicles.set_index("Vehicle Type")["Capacity for pallet type 1"].to_dict(), mutable=False)
# model.rented_capacity_80x120 = Param(model.vehicle_type, initialize=vehicles.set_index("Vehicle Type")["Capacity for pallet type 2"].to_dict(), mutable=False)
model.order_product_type = Param(model.orders, initialize=orders.groupby('Order ID')['Product Type'].apply(list).to_dict(), within=Any, doc="The map of orders listed by product type", mutable=False)
model.pallet_product_type = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Product Type'].to_dict(), within=Any, doc="The map of pallets listed by product type", mutable=False)
model.vehicle_types = Param(model.vehicles, initialize=vehicles.set_index('Vehicle ID')['Vehicle Type'].to_dict(), within=Any, doc="The type of vehicle", mutable=False)
model.max_trips = Param(initialize=parameters['Value'].iloc[1], doc="The max number of trips allowed to each owned vehicle per day", mutable=False)
model.vehicle_1_pallet_1_cap = Param(model.type_1_loading_types, initialize=loading_types[loading_types["VehicleType"] == 1].set_index("LoadingType")["CapacityForPalletSize1"])
model.vehicle_1_pallet_2_cap = Param(model.type_1_loading_types, initialize=loading_types[loading_types["VehicleType"] == 1].set_index("LoadingType")["CapacityForPalletSize2"])
model.vehicle_2_pallet_1_cap = Param(model.type_2_loading_types, initialize=loading_types[loading_types["VehicleType"] == 2].set_index("LoadingType")["CapacityForPalletSize1"])
model.vehicle_2_pallet_2_cap = Param(model.type_2_loading_types, initialize=loading_types[loading_types["VehicleType"] == 2].set_index("LoadingType")["CapacityForPalletSize2"])
model.vehicle_3_pallet_1_cap = Param(model.type_3_loading_types, initialize=loading_types[loading_types["VehicleType"] == 3].set_index("LoadingType")["CapacityForPalletSize1"])
model.vehicle_3_pallet_2_cap = Param(model.type_3_loading_types, initialize=loading_types[loading_types["VehicleType"] == 3].set_index("LoadingType")["CapacityForPalletSize2"])

model.M = Param(initialize=100, mutable=False)

end_time = time.time()
print(f"Extracted parameters.\nCPU Time: {end_time - start_time} seconds\n")

# Variables
model.is_shipped = Var(model.pallets, model.planning_horizon, domain=Binary)
model.pallet_used_on_order = Var(model.pallets, model.orders, model.product_type, domain=Binary)
model.owned_vehicle_has_pallet = Var(model.pallets, model.vehicles, model.planning_horizon, domain=Binary)
model.number_of_trips = Var(model.vehicles, model.planning_horizon, domain=NonNegativeIntegers)
model.is_rented = Var(model.rentable, domain=Binary)
model.rented_type = Var(model.rentable, domain=NonNegativeIntegers, bounds=(min(model.vehicle_type), max(model.vehicle_type)), initialize=1)
model.rented_vehicle_has_pallet = Var(model.pallets, model.rentable, model.planning_horizon, domain=Binary)
model.rented_vehicle_trip = Var(model.rentable, model.planning_horizon, domain=NonNegativeIntegers)
model.owned_vehicle_1_loading_type = Var(model.vehicles, domain=NonNegativeIntegers, bounds=(min(model.type_1_loading_types), max(model.type_1_loading_types)), initialize=0)
model.owned_vehicle_2_loading_type = Var(model.vehicles, domain=NonNegativeIntegers, bounds=(min(model.type_2_loading_types), max(model.type_2_loading_types)), initialize=0)
model.owned_vehicle_3_loading_type = Var(model.vehicles, domain=NonNegativeIntegers, bounds=(min(model.type_3_loading_types), max(model.type_3_loading_types)), initialize=0)
model.rented_vehicle_1_loading_type = Var(model.vehicles, domain=NonNegativeIntegers, bounds=(min(model.type_1_loading_types), max(model.type_1_loading_types)), initialize=0)
model.rented_vehicle_2_loading_type = Var(model.vehicles, domain=NonNegativeIntegers, bounds=(min(model.type_2_loading_types), max(model.type_2_loading_types)), initialize=0)
model.rented_vehicle_3_loading_type = Var(model.vehicles, domain=NonNegativeIntegers, bounds=(min(model.type_3_loading_types), max(model.type_3_loading_types)), initialize=0)


model.aux_1 = Var(model.pallets, model.planning_horizon, model.vehicles, domain=Binary)
model.aux_2 = Var(model.pallets, model.planning_horizon, model.vehicles, domain=Binary)
model.aux_3 = Var(model.pallets, model.planning_horizon, model.rentable, domain=Binary)
model.aux_4 = Var(model.pallets, model.planning_horizon, model.rentable, domain=Binary)
model.aux_5 = Var(model.pallets, model.pallets, model.vehicles, domain=Binary)
model.aux_6 = Var(model.pallets, model.orders, model.product_type, model.planning_horizon, model.rentable, domain=Binary)
model.aux_7 = Var(model.pallets, model.orders, model.product_type, model.planning_horizon, model.rentable, domain=Binary)
model.aux_8 = Var(model.pallets, model.orders, model.product_type, model.planning_horizon, model.vehicles, domain=Binary)
model.aux_9 = Var(model.pallets, model.orders, model.product_type, model.planning_horizon, model.vehicles, domain=Binary)
model.aux_10 = Var(model.pallets, model.pallets, model.rentable, model.planning_horizon, domain=Binary)

end_time = time.time()
print(f"Initialized variables.\nCPU Time: {end_time - start_time} seconds\n")

# Objective Function,
def total_cost(model):
    owned_vehicle_cost = sum(value(model.owned_vehicle_cost[v]) * model.number_of_trips[v,t] for v in model.vehicles for t in model.planning_horizon)
    rented_vehicle_cost = 0
    for rv in model.rentable:
        rented_type = value(model.rented_type[rv])
        rented_vehicle_cost += sum(value(model.rented_vehicle_cost[rented_type]) * model.rented_vehicle_trip[rv, t] for t in model.planning_horizon)
    total_penalty = sum(value(model.earliness_penalty[o]) * model.pallet_used_on_order[i,o,j] * (value(model.order_due_date[o]) - value(model.pallet_release_day[i])) for j in model.product_type for o in model.orders for i in model.pallets if model.order_due_date[o] >= value(model.pallet_release_day[i]))

    return owned_vehicle_cost + rented_vehicle_cost + total_penalty
model.total_cost = Objective(rule=total_cost, sense=minimize) 

end_time = time.time()
print(f"Initialized objective function.\nCPU Time: {end_time - start_time} seconds\n")

# Constraints

def constraint_1(model, i):
    return sum(model.is_shipped[i,t] for t in model.planning_horizon) <= 1
model.constraint_1 = Constraint(model.pallets, rule=constraint_1)


end_time = time.time()
print(f"Initialized constraint_1.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_2(model, i):
    release_day = value(model.pallet_release_day[i])
    if release_day == 1:
        return Constraint.Feasible
    else:
        return sum(model.is_shipped[i,t] for t in range(1, release_day)) == 0
model.constraint_2 = Constraint(model.pallets, rule=constraint_2)

end_time = time.time()
print(f"Initialized constraint_2.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_3(model):
    return sum(1 - sum(model.is_shipped[i,t] for t in model.planning_horizon if t >= value(model.pallet_release_day[i])) for i in model.pallets) <= value(model.warehouse_storage)
model.constraint_3 = Constraint(rule=constraint_3)

end_time = time.time()
print(f"Initialized constraint_3.\nCPU Time: {end_time - start_time} seconds\n")
    
"""
inputs = v, t
sum(model.owned_vehicle_has_pallet[i, v] * model.is_shipped[i, t] for i in model.pallets if model.pallet_size[value(i)] == 1) <= owned_capacity_calculator(v, 1)
"""

"""
inputs = v, t
sum(model.owned_vehicle_has_pallet[i, v] * model.is_shipped[i, t] for i in model.pallets if model.pallet_size[value(i)] == 2) <= owned_capacity_calculator(v, 2)
"""

def constraint_4_1_REMASTERED(model, v):
    if value(model.vehicle_types[v]) == 1:
        return model.owned_vehicle_1_loading_type[v] >= 1
    else:
        return model.owned_vehicle_1_loading_type[v] == 0
model.constraint_4_1_REMASTERED = Constraint(model.vehicles, rule=constraint_4_1_REMASTERED)

end_time = time.time()
print(f"Initialized constraint_4_1.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_4_2_REMASTERED(model, v):
    if value(model.vehicle_types[v]) == 2:
        return model.owned_vehicle_2_loading_type[v] >= 1
    else:
        return model.owned_vehicle_2_loading_type[v] == 0
model.constraint_4_2_REMASTERED = Constraint(model.vehicles, rule=constraint_4_2_REMASTERED)

end_time = time.time()
print(f"Initialized constraint_4_2.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_4_3_REMASTERED(model, v):
    if value(model.vehicle_types[v]) == 3:
        return model.owned_vehicle_3_loading_type[v] >= 1
    else:
        return model.owned_vehicle_3_loading_type[v] == 0
model.constraint_4_3_REMASTERED = Constraint(model.vehicles, rule=constraint_4_3_REMASTERED)

end_time = time.time()
print(f"Initialized constraint_4_3.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_4_4_REMASTERED(model, v):
    if value(model.vehicle_types[v]) == 1:
        return model.rented_vehicle_1_loading_type[v] >= 1
    else:
        return model.rented_vehicle_1_loading_type[v] == 0
model.constraint_4_4_REMASTERED = Constraint(model.vehicles, rule=constraint_4_4_REMASTERED)

end_time = time.time()
print(f"Initialized constraint_4_4.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_4_5_REMASTERED(model, v):
    if value(model.vehicle_types[v]) == 2:
        return model.rented_vehicle_2_loading_type[v] >= 1
    else:
        return model.rented_vehicle_2_loading_type[v] == 0
model.constraint_4_5_REMASTERED = Constraint(model.vehicles, rule=constraint_4_5_REMASTERED)

end_time = time.time()
print(f"Initialized constraint_4_5.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_4_6_REMASTERED(model, v):
    if value(model.vehicle_types[v]) == 3:
        return model.rented_vehicle_3_loading_type[v] >= 1
    else:
        return model.rented_vehicle_3_loading_type[v] == 0
model.constraint_4_6_REMASTERED = Constraint(model.vehicles, rule=constraint_4_6_REMASTERED)

end_time = time.time()
print(f"Initialized constraint_4_6.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_5_1_REMASTERED(model, v, t):
    if value(model.vehicle_type[v]) == 1:
        l = model.owned_vehicle_1_loading_type[v]
        return (sum(model.owned_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 1)) <= model.vehicle_1_pallet_1_cap[l])
    if value(model.vehicle_type[v]) == 2:
        l = model.owned_vehicle_2_loading_type[v]
        return (sum(model.owned_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 1)) <= model.vehicle_2_pallet_1_cap[l])
    if value(model.vehicle_type[v]) == 3:
        l = model.owned_vehicle_3_loading_type[v]
        return (sum(model.owned_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 1)) <= model.vehicle_3_pallet_1_cap[l])
model.constraint_5_1_REMASTERED = Constraint(model.vehicles, model.planning_horizon, rule=constraint_5_1_REMASTERED)

end_time = time.time()
print(f"Initialized constraint_5_1.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_5_2_REMASTERED(model, v, t):
    if value(model.vehicle_type[v]) == 1:
        l = model.owned_vehicle_1_loading_type[v]
        return (sum(model.owned_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 2)) <= model.vehicle_1_pallet_2_cap[l])
    if value(model.vehicle_type[v]) == 2:
        l = model.owned_vehicle_2_loading_type[v]
        return (sum(model.owned_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 2)) <= model.vehicle_2_pallet_2_cap[l])
    if value(model.vehicle_type[v]) == 3:
        l = model.owned_vehicle_3_loading_type[v]
        return (sum(model.owned_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 2)) <= model.vehicle_3_pallet_2_cap[l])
model.constraint_5_2_REMASTERED = Constraint(model.vehicles, model.planning_horizon, rule=constraint_5_2_REMASTERED)

end_time = time.time()
print(f"Initialized constraint_5_2.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_5_3_REMASTERED(model, v, t):
    if value(model.vehicle_type[v]) == 1:
        l = model.owned_vehicle_1_loading_type[v]
        return (sum(model.rented_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 1)) <= model.vehicle_1_pallet_1_cap[l])
    if value(model.vehicle_type[v]) == 2:
        l = model.owned_vehicle_2_loading_type[v]
        return (sum(model.rented_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 1)) <= model.vehicle_2_pallet_1_cap[l])
    if value(model.vehicle_type[v]) == 3:
        l = model.owned_vehicle_3_loading_type[v]
        return (sum(model.rented_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 1)) <= model.vehicle_3_pallet_1_cap[l])
model.constraint_5_3_REMASTERED = Constraint(model.vehicles, model.planning_horizon, rule=constraint_5_3_REMASTERED)

end_time = time.time()
print(f"Initialized constraint_5_3.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_5_4_REMASTERED(model, v, t):
    if value(model.vehicle_type[v]) == 1:
        l = model.owned_vehicle_1_loading_type[v]
        return (sum(model.rented_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 2)) <= model.vehicle_1_pallet_2_cap[l])
    if value(model.vehicle_type[v]) == 2:
        l = model.owned_vehicle_2_loading_type[v]
        return (sum(model.rented_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 2)) <= model.vehicle_2_pallet_2_cap[l])
    if value(model.vehicle_type[v]) == 3:
        l = model.owned_vehicle_3_loading_type[v]
        return (sum(model.rented_vehicle_has_pallet[i,v,t] for i in model.pallets if value(model.pallet_size[i] == 2)) <= model.vehicle_3_pallet_2_cap[l])
model.constraint_5_4_REMASTERED = Constraint(model.vehicles, model.planning_horizon, rule=constraint_5_4_REMASTERED)

end_time = time.time()
print(f"Initialized constraint_5_4.\nCPU Time: {end_time - start_time} seconds\n")

#CONSTRAINT 4 HAS BEEN REBORN.

#CONSTRAINT 5 HAS PERISHED.

def constraint_6(model, v, t):
    return model.number_of_trips[v, t] <= model.max_trips
model.constraint_6 = Constraint(model.vehicles, model.planning_horizon, rule=constraint_6)

end_time = time.time()
print(f"Initialized constraint_6.\nCPU Time: {end_time - start_time} seconds\n")


def constraint_7(model, o, j):
    return sum(value(model.products_in_pallet[i]) * model.pallet_used_on_order[i,o,j] for i in model.pallets) >= model.order_demand[o,j]
model.constraint_7 = Constraint(model.orders, model.product_type, rule=constraint_7)

end_time = time.time()
print(f"Initialized constraint_7.\nCPU Time: {end_time - start_time} seconds\n")


def constraint_8(model, i, j):
    if model.pallet_product_type[i] != j:
        return sum(model.pallet_used_on_order[i,o,j] for o in model.orders) <= 0
    else:
        return Constraint.Feasible
model.constraint_8 = Constraint(model.pallets, model.product_type, rule=constraint_8)

end_time = time.time()
print(f"Initialized constraint_8.\nCPU Time: {end_time - start_time} seconds\n")


def constraint_9(model, i, rv, t):
     return model.rented_vehicle_has_pallet[i, rv, t] <= model.is_rented[rv]
model.constraint_9 = Constraint(model.pallets, model.rentable, model.planning_horizon, rule=constraint_9)

end_time = time.time()
print(f"Initialized constraint_9.\nCPU Time: {end_time - start_time} seconds\n")


def constraint_10(model, i, o, j):
    return model.pallet_used_on_order[i,o,j] * value(model.pallet_release_day[i]) <= model.order_due_date[o]
model.constraint_10 = Constraint(model.pallets, model.orders, model.product_type, rule=constraint_10)

end_time = time.time()
print(f"Initialized constraint_10.\nCPU Time: {end_time - start_time} seconds\n")

def owned_capacity_calculator(model, v):
    l = model.owned_vehicle_1_loading_type[v]
    match value(model.vehicle_types[v]):
        case 1:
            return value(model.vehicle_1_pallet_1_cap[l] + model.vehicle_1_pallet_2_cap[l])
        case 2:
            return value(model.vehicle_2_pallet_1_cap[l] + model.vehicle_3_pallet_2_cap[l])
        case 3:
            return value(model.vehicle_3_pallet_1_cap[l] + model.vehicle_3_pallet_2_cap[l])
        
def rented_capacity_calculator(model, v):
        l = model.rented_vehicle_1_loading_type[v]
        match value(model.vehicle_types[v]):
            case 1:
                return value(model.vehicle_1_pallet_1_cap[l] + model.vehicle_1_pallet_2_cap[l])
            case 2:
                return value(model.vehicle_2_pallet_1_cap[l] + model.vehicle_2_pallet_2_cap[l])
            case 3:
                return value(model.vehicle_3_pallet_1_cap[l] + model.vehicle_3_pallet_2_cap[l])


def constraint_11_1(model, j, rv, t):
    total_pallets = sum(model.aux_6[i,o,j,t,rv] for o in model.orders for i in model.pallets)
    return model.rented_vehicle_trip[rv,t] >= total_pallets / rented_capacity_calculator(model, rv)
model.constraint_11_1 = Constraint(model.product_type, model.rentable, model.planning_horizon, rule=constraint_11_1)

end_time = time.time()
print(f"Initialized constraint_11_1.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_11_1_1(model, i, o, j, t, rv):
    return model.aux_6[i,o,j,t,rv] <= model.pallet_used_on_order[i,o,j]
model.constraint_11_1_1 = Constraint(model.pallets, model.orders, model.product_type, model.planning_horizon, model.rentable, rule=constraint_11_1_1)

end_time = time.time()
print(f"Initialized constraint_11_1_1.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_11_1_2(model, i, o, j, t, rv):
    return model.aux_6[i,o,j,t,rv] <= model.rented_vehicle_has_pallet[i,rv,t]
model.constraint_11_1_2 = Constraint(model.pallets, model.orders, model.product_type, model.planning_horizon, model.rentable, rule=constraint_11_1_2)

end_time = time.time()
print(f"Initialized constraint_11_1_2.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_11_1_3(model, i, o, j, t, rv):
    return model.aux_6[i,o,j,t,rv] >= model.pallet_used_on_order[i,o,j] + model.rented_vehicle_has_pallet[i,rv,t] - 1
model.constraint_11_1_3 = Constraint(model.pallets, model.orders, model.product_type, model.planning_horizon, model.rentable, rule=constraint_11_1_3)

end_time = time.time()
print(f"Initialized constraint_11_1_3.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_11_3(model, j, v, t):
    total_pallets = sum(model.aux_8[i,o,j,t,v] for o in model.orders for i in model.pallets if model.pallet_size[i] == 1)
    return model.number_of_trips[v,t] >= total_pallets / owned_capacity_calculator(model, v)
model.constraint_11_3 = Constraint(model.product_type, model.vehicles, model.planning_horizon, rule=constraint_11_3)

end_time = time.time()
print(f"Initialized constraint_11_3.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_11_3_1(model, i, o, j, t, v):
    return model.aux_8[i,o,j,t,v] <= model.pallet_used_on_order[i,o,j]
model.constraint_11_3_1 = Constraint(model.pallets, model.orders, model.product_type, model.planning_horizon, model.vehicles, rule=constraint_11_3_1)

end_time = time.time()
print(f"Initialized constraint_11_3_1.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_11_3_2(model, i, o, j, t, v):
    return model.aux_8[i,o,j,t,v] <= model.owned_vehicle_has_pallet[i,v,t]
model.constraint_11_3_2 = Constraint(model.pallets, model.orders, model.product_type, model.planning_horizon, model.vehicles, rule=constraint_11_3_2)

end_time = time.time()
print(f"Initialized constraint_11_3_2.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_11_3_3(model, i, o, j, t, v):
    return model.aux_8[i,o,j,t,v] >= model.pallet_used_on_order[i,o,j] + model.owned_vehicle_has_pallet[i,v,t] - 1
model.constraint_11_3_3 = Constraint(model.pallets, model.orders, model.product_type, model.planning_horizon, model.vehicles, rule=constraint_11_3_3)

end_time = time.time()
print(f"Initialized constraint_11_3_3.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_11_5(model, i, t):
    return sum(model.owned_vehicle_has_pallet[i,v,t] for v in model.vehicles) + sum(model.rented_vehicle_has_pallet[i, rv, t] for rv in model.rentable for t in model.planning_horizon) == sum(model.is_shipped[i, t] for t in model.planning_horizon)
model.constraint_11_5 = Constraint(model.pallets, model.planning_horizon, rule=constraint_11_5)

end_time = time.time()
print(f"Initialized constraint_11_5.\nCPU Time: {end_time - start_time} seconds\n")

def constraint_12(model, i, o, j):
    # When pallet_used_on_order[i,o,j] is 1, the shipping day (weighted sum) must be <= order_due_date[o]
    # When pallet_used_on_order[i,o,j] is 0, the constraint is relaxed using a big-M term.
    return sum(value(t) * model.is_shipped[i, t] for t in model.planning_horizon) <= value(model.order_due_date[o]) + value(model.M) * (1 - model.pallet_used_on_order[i,o,j])

model.constraint_12 = Constraint(model.pallets, model.orders, model.product_type, rule=constraint_12)

end_time = time.time()
print(f"Done so far.\nCPU Time: {end_time - start_time} seconds")

solver = SolverFactory('gurobi')
solver.options['TimeLimit'] = 19000
solver.solve(model, tee=True)

end_time = time.time()
print(f"\nCPU Time: {end_time - start_time} seconds\n")

with open("solution.txt", "w") as f:
    for v in model.component_objects(Var, active=True):
        for index in v:
            f.write(f"{v.name}[{index}] = {v[index].value}\n")