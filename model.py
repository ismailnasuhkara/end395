from pyomo.environ import *
import pandas as pd

orders = pd.read_excel("ProjectPart1-Part1.xlsx", sheet_name="Orders")
pallets = pd.read_excel("ProjectPart1-Part1.xlsx", sheet_name="Pallets")
vehicles = pd.read_excel("ProjectPart1-Part1.xlsx", sheet_name="Vehicles")
parameters = pd.read_excel("ProjectPart1-Part1.xlsx", sheet_name="Parameters")

model = ConcreteModel()

# Sets
model.planning_horizon = Set(initialize=range(1, parameters['Value'].iloc[0] + 1), doc="Set of days in the planning horizon")
model.pallets = Set(initialize=pallets['Pallet ID'], doc="Set of pallets")
model.orders = Set(initialize=orders['Order ID'], doc="Set of orders")
model.product_type = Set(initialize=orders['Product Type'].unique(), doc="Set of product types") 
model.vehicles = Set(initialize=vehicles["Vehicle ID"], doc="Set of owned vehicles")
model.rentable = Set(initialize=range(1, 100), doc="Set of rentable vehicles")
model.vehicle_type = Set(initialize=vehicles["Vehicle Type"].unique(), doc="Set of vehicle types")

# Parameters
model.products_in_pallet = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Amount'].to_dict(), doc="Number of products that can be stored in each pallet")
# 1 = 100x120 cm, 2 = 80x120 cm
model.pallet_size = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Pallet Size'].to_dict(), doc="Size of each pallet")
model.pallet_release_day = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Release Day'].to_dict(), within=PositiveIntegers, doc="The release day of each pallet")
model.order_demand = Param(model.orders, model.product_type, initialize=orders.set_index(["Order ID","Product Type"])['Demand Amount'].to_dict(), doc="Number of products required for each order")
model.order_due_date = Param(model.orders, initialize=orders.set_index('Order ID')['Due Date'].to_dict(), doc="Due date of each order")
model.warehouse_storage = Param(initialize=parameters['Value'].iloc[2], doc="Warehouse storage capacity in terms of pallets")
model.earliness_penalty = Param(model.orders, initialize=orders.set_index('Order ID')['Earliness Penalty'].to_dict(), doc="Earliness penalty cost of each order")
model.owned_vehicle_cost = Param(model.vehicles, initialize=vehicles.set_index('Vehicle ID')['Fixed Cost (c_k)'].to_dict(), doc="Delivery cost of each owned vehicle")
model.rented_vehicle_cost = Param(model.vehicle_types, initialize=vehicles.set_index('Vehicle Type')['Variable Cost (c\'_k)'].to_dict(), doc="Delivery cost of each rented vehicle")    
# Truck = 22, Lorry = 12, Van = 6
model.vehicle_capacity_100x120 = Param(model.vehicles, initialize=vehicles.set_index('Vehicle ID')['Capacity for pallet type 1'].to_dict(), doc="Capacity of each vehicle type for 100x120 cm pallets")
# Truck = 33, Lorry = 18, Van = 8
model.vehicle_capacity_80x120 = Param(model.vehicles, initialize=vehicles.set_index('Vehicle ID')['Capacity for pallet type 2'].to_dict(), doc="Capacity of each vehicle type for 80x120 cm pallets")

model.rented_capacity_100x120 = Param(model.vehicle_type, initialize=vehicles.set_index("Vehicle Type")["Capacity for pallet type 1"].to_dict())

model.rented_capacity_80x120 = Param(model.vehicle_type, initialize=vehicles.set_index("Vehicle Type")["Capacity for pallet type 2"].to_dict())
model.order_product_type = Param(model.orders, initialize=orders.groupby('Order ID')['Product Type'].apply(list).to_dict(), within=Any, doc="The map of orders listed by product type")
model.pallet_product_type = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Product Type'].to_dict(), within=Any, doc="The map of pallets listed by product type")
model.vehicle_type = Param(model.vehicles, initialize=pallets.set_index('Vehicle ID')['Vehicle Type'].to_dict(), within=Any, doc="The type of vehicle")
model.max_trips = Param(initialize=parameters['Value'].iloc[1], doc="The max number of trips allowed to each owned vehicle per day")

# Variables
model.is_shipped = Var(model.pallets, model.planning_horizon, domain=Binary)
model.pallet_used_on_order = Var(model.pallets, model.orders, model.product_type, domain=Binary)
model.owned_vehicle_has_pallet = Var(model.pallets, model.vehicles, domain=Binary)
model.number_of_trips = Var(model.vehicles, model.planning_horizon, domain=NonNegativeIntegers)
model.is_rented = Var(model.rentable, domain=Binary)
model.rented_type = Var(model.rentable, domain=model.vehicle_types)
model.rented_vehicle_has_pallet = Var(model.pallets, model.rentable, model.planning_horizon, domain=Binary)
model.rented_vehicle_trips = Var(model.rentable, model.planning_horizon, domain=NonNegativeIntegers)

# Objective Function,
def total_cost():
    owned_vehicle_cost = sum(model.owned_vehicle_cost[v] * model.number_of_trips[v,t] for v in model.vehicles for t in model.planning_horizon)
    rented_vehicle_cost = 0
    for rv in model.rentable:
        rented_type = model.rented_vehicle_type[rv]
        rented_vehicle_cost += sum(model.rented_vehicle_cost[rented_type] * model.rented_vehicle_trips[rv, t] for t in model.planning_horizon)
    total_penalty = sum(model.earliness_penalty[o] * model.pallet_used_on_order[i, o] * (model.order_due_date[o] - model.pallet_release_day[i]) for o in model.orders for i in model.pallets if model.order_due_date[o] >= model.pallet_release_day[i])

    return owned_vehicle_cost + rented_vehicle_cost + total_penalty

model.total_cost = Objective(rule=total_cost, sense=minimize) 

# Constraints
def constraint_1(i):
    return sum(model.is_shipped[i,t] for t in model.planning_horizon) == 1
model.constraint_1 = Constraint(model.pallets, rule=constraint_1)

def constraint_2(i):
    release_day = model.pallet_release_day[i]
    if release_day == 1:
        return Constraint.Feasible
    else:
        return sum(model.is_shipped for t in range(1, release_day)) == 0
model.constraint_2 = Constraint(model.pallets, rule=constraint_2)

def constraint_3():
    return sum(1 - sum(model.is_shipped[i,] for t in model.planning_horizon if t >= model.pallet_release_day[i]) for i in model.pallets) <= model.warehouse_storage
model.constraint_3 = Constraint(rule=constraint_3)

def constraint_4_1(v,t):
    return sum(model.is_shippped[i,t] * model.owned_vehicle_has_pallet[i,v] for i in model.pallets if model.pallet_size[i] == 1) <= owned_capacity_calculator(v,1)
model.constraint_4_1 = Constraint(model.vehicles, model.planning_horizon, rule=constraint_4_1)

def constraint_4_2(v,t):
    return sum(model.is_shippped[i,t] * model.owned_vehicle_has_pallet[i,v] for i in model.pallets if model.pallet_size[i] == 2) <= owned_capacity_calculator(v,2)
model.constraint_4_2 = Constraint(model.vehicles, model.planning_horizon, rule=constraint_4_2)

def constraint_4_3(rv,t):
     return sum(model.is_shipped[i,t] * model.rented_vehicle_has_pallet[i,rv, t] for i in model.pallets if model.pallet_size[i] == 1) <= rented_capacity_calculator(rv,1)
model.constraint_4_3 = Constraint(model.rentable, model.planning_horizon, rule=constraint_4_3)

def constraint_4_4(rv,t):
     return sum(model.is_shipped[i,t] * model.rented_vehicle_has_pallet[i,rv,t] for i in model.pallets if model.pallet_size[i] == 2) <= rented_capacity_calculator(rv,1)
model.constraint_4_4 = Constraint(model.rentable, model.planning_horizon, rule=constraint_4_4)

def constraint_5_1(i, j, v):
    return model.owned_vehicle_has_pallet[i, v] * model.owned_vehicle_has_pallet[j, v] * (model.pallet_size[i] - model.pallet_size[j]) == 0
model.constraint_5_1 = Constraint(model.pallets, model.pallets, model.vehicles, rule=constraint_5_1)

def constraint_5_2(i, j, rv, t):
    return model.rented_vehicle_has_pallet[i, rv] * model.rented_vehicle_has_pallet[j, rv, t] * (model.pallet_size[i] - model.pallet_size[j]) == 0
model.constraint_5_2 = Constraint(model.pallets, model.pallets, model.rentable, model.planning_horizon, rule=constraint_5_2)

def constraint_6(v,t):
    return model.number_of_trips[v, t] <= model.max_trips
model.constraint_6 = Constraint(model.vehicles, model.planning_horizon, rule=constraint_6)

def constraint_7(o,j):
    return sum(model.products_in_pallet[i] * model.pallet_used_on_order[i,o,j] for i in model.pallets) >= model.order_demand[o,j]
model.constraint_7 = Constraint(model.orders, model.product_type, rule=constraint_7)

def constraint_8(i, j):
    return sum(model.pallet_used_on_order[i,o,j] for o in model.orders if (model.pallet_product_type[i] > j or model.pallet_product_type < j)) <= 0
model.constraint_8 = Constraint(model.pallets, model.product_type, rule=constraint_8)

def constraint_9(i, rv):
     return model.rented_vehicle_has_pallet[i, rv] <= model.is_rented[rv]
model.constraint_9 = Constraint(model.pallets, model.rentable, rule=constraint_9)

def constraint_10(i,o):
    return model.pallet_used_on_order[i,o] * model.pallet_release_day[i] <= model.order_due_date[o]
model.constraint_10 = Constraint(model.pallets, model.orders, rule=constraint_10)

def constraint_11_1(rv, t):
    total_pallets = sum(model.pallet_used_on_order[i, o] * model.rented_vehicle_has_pallet[i, rv ,t] for o in model.orders for i in model.pallets if model.pallet_size[i] == 1)
    return model.rented_vehicle_trips >= total_pallets / rented_capacity_calculator(rv, 1)


def constraint_11_2(rv, t):
    total_pallets = sum(model.pallet_used_on_order[i, o] * model.rented_vehicle_has_pallet[i, rv ,t] for o in model.orders for i in model.pallets if model.pallet_size[i] == 2)
    return model.rented_vehicle_trips >= total_pallets / rented_capacity_calculator(rv, 2)

def constraint_11_3(v, t):
    total_pallets = sum(model.pallet_used_on_order[i, o] * model.owned_vehicle_has_pallet[i, v ,t] for o in model.orders for i in model.pallets if model.pallet_size[i] == 1)
    return model.number_of_trips >= total_pallets / owned_capacity_calculator(v, 1)

def constraint_11_4(v, t):
    total_pallets = sum(model.pallet_used_on_order[i, o] * model.owned_vehicle_has_pallet[i, v ,t] for o in model.orders for i in model.pallets if model.pallet_size[i] == 2)
    return model.number_of_trips >= total_pallets / owned_capacity_calculator(v, 2)

def owned_capacity_calculator(v, s):
        if s == 1:
            return model.vehicle_capacity_100x120[v]
        elif s == 2:
            return model.vehicle_capacity_80x120[v]
        
def rented_capacity_calculator(rv, s):
    if s == 1:
         return model.rented_vehicle_capacity_100x120[model.rented_type[rv]]
    elif s == 2:
         return model.rented_vehicle_capacity_80x120[model.rented_type[rv]]
