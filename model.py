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
model.product_type = Set(initialize=orders['Product Type'].unique(), doc="Set of product types")
model.vehicles = Set(initialize=vehicles["Vehicle ID"], doc="Set of owned vehicles")

# Parameters
model.products_in_pallet = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Amount'].to_dict(), doc="Number of products that can be stored in each pallet")
# 1 = 100x120 cm, 2 = 80x120 cm
model.pallet_size = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Pallet Size'].to_dict(), doc="Size of each pallet")
model.pallet_release_day = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Release Day'].to_dict(), within=PositiveIntegers, doc="The release day of each pallet")
model.order_demand = Param(model.orders, model.product_type, initialize=orders.set_index(["Order ID","Product Type"])['Demand Amount'].to_dict(), doc="Number of products required for each order")
model.order_due_date = Param(model.orders, initialize=orders.set_index('Order ID')['Due Date'].to_dict(), doc="Due date of each order")
model.warehouse_storage = Param(initialize=parameters['Value'].iloc[2], doc="Warehouse storage capacity in terms of pallets")
model.earliness_penalty = Param(model.orders, initialize=orders.set_index('Order ID')['Earliness Penalty'].to_dict(), doc="Earliness penalty cost of each order")
model.owned_vehicle_cost = Param(model.vehicle_types, initialize=vehicles.set_index('Vehicle Type')['Fixed Cost (c_k)'].to_dict(), doc="Delivery cost of each owned vehicle")
model.rented_vehicle_cost = Param(model.vehicle_types, initialize=vehicles.set_index('Vehicle Type')['Variable Cost (c\'_k)'].to_dict(), doc="Delivery cost of each rented vehicle")    
# Truck = 22, Lorry = 12, Van = 6
model.vehicle_capacity_100x120 = Param(model.vehicles, initialize=vehicles.set_index('Vehicle ID')['Capacity for pallet type 1'].to_dict(), doc="Capacity of each vehicle type for 100x120 cm pallets")
# Truck = 33, Lorry = 18, Van = 8
model.vehicle_capacity_80x120 = Param(model.vehicles, initialize=vehicles.set_index('Vehicle ID')['Capacity for pallet type 2'].to_dict(), doc="Capacity of each vehicle type for 80x120 cm pallets")    
model.order_product_type = Param(model.orders, initialize=orders.groupby('Order ID')['Product Type'].apply(list).to_dict(), within=Any, doc="The map of orders listed by product type")
model.pallet_product_type = Param(model.pallets, initialize=pallets.set_index('Pallet ID')['Product Type'].to_dict(), within=Any, doc="The map of pallets listed by product type")
model.vehicle_type = Param(model.vehicles, initialize=pallets.set_index('Vehicle ID')['Vehicle Type'].to_dict(), within=Any, doc="The type of vehicle")
model.max_trips = Param(initialize=parameters['Value'].iloc[1], doc="The max number of trips allowed to each owned vehicle")

# Constraints




