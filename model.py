from pyomo.environ import *
from pandas import *

class END395Model:
    def __init__(self, orders, pallets, vehicles, parameters):
        self.orders = orders
        self.pallets = pallets
        self.vehicles = vehicles
        self.parameters = parameters

        self.model = ConcreteModel()
        self.createSets()
        self.createParameters()
        self.createVariables()
        self.createObjectiveFunction()
        self.createConstraints()

    def createSets(self):
        self.model.planning_horizon = Set(initialize=range(1, self.parameters['Value'].iloc[0] + 1),
                          doc="Set of days in the planning horizon")
        
        # 1 = Truck, 2 = Lorry, 3 = Van
        self.model.vehicle_types = Set(initialize=self.vehicles['Vehicle Type'].unique(),
                           doc="Set of vehicle types")

        self.model.pallets = Set(initialize=self.pallets['Pallet ID'],
                     doc="Set of pallets")

        
        self.model.orders = Set(initialize=self.orders['Order ID'],
                    doc="Set of orders")
        
        self.model.product_type = Set(initialize=self.orders['Product Type'].unique(),
                          doc="Set of product types") 
        
        self.model.size_types = Set(initialize=self.pallets['Pallet Size'].unique(),
                                    doc="Set of pallet sizes")
        
        

    def createParameters(self):
        self.model.owned_vehicles = Param(self.model.vehicle_types, initialize=self.vehicles["Vehicle Type"].value_counts().to_frame("Count").to_dict()["Count"],
                          doc="Number of owned vehicles of each type")

        self.model.products_in_pallet = Param(self.model.pallets, initialize=self.pallets.set_index('Pallet ID')['Amount'].to_dict(),
                            doc="Number of products that can be stored in each pallet")

        # 1 = 100x120 cm, 2 = 80x120 cm
        self.model.pallet_size = Param(self.model.pallets, initialize=self.pallets.set_index('Pallet ID')['Pallet Size'].to_dict(),
                        doc="Size of each pallet")
        
        self.model.pallet_release_day = Param(self.model.pallets, initialize=self.pallets.set_index('Pallet ID')['Release Day'].to_dict(), within=PositiveIntegers,
                               doc="The release day of each pallet")
        
        self.model.order_demand = Param(self.model.orders, self.model.product_type, initialize=self.orders.set_index(["Order ID","Product Type"])['Demand Amount'].to_dict(),
                         doc="Number of products required for each order")
        
        self.model.order_due_date = Param(self.model.orders, initialize=self.orders.set_index('Order ID')['Due Date'].to_dict(),
                          doc="Due date of each order")
        
        self.model.warehouse_storage = Param(initialize=self.parameters['Value'].iloc[2],
                                   doc="Warehouse storage capacity in terms of pallets")
        
        self.model.earliness_penalty = Param(self.model.orders, initialize=self.orders.set_index('Order ID')['Earliness Penalty'].to_dict(),
                             doc="Earliness penalty cost of each order")
        
        self.model.owned_vehicle_cost = Param(self.model.vehicle_types, initialize=self.vehicles.set_index('Vehicle Type')['Fixed Cost (c_k)'].to_dict(),
                              doc="Delivery cost of each owned vehicle")
        
        self.model.rented_vehicle_cost = Param(self.model.vehicle_types, initialize=self.vehicles.set_index('Vehicle Type')['Variable Cost (c\'_k)'].to_dict(),
                               doc="Delivery cost of each rented vehicle")
        
        # Truck = 22, Lorry = 12, Van = 6
        self.model.vehicle_capacity_100x120 = Param(self.model.vehicle_types, initialize=self.vehicles.set_index('Vehicle Type')['Capacity for pallet type 1'].to_dict(),
                                doc="Capacity of each vehicle type for 100x120 cm pallets")
        
        # Truck = 33, Lorry = 18, Van = 8
        self.model.vehicle_capacity_80x120 = Param(self.model.vehicle_types, initialize=self.vehicles.set_index('Vehicle Type')['Capacity for pallet type 2'].to_dict(),
                               doc="Capacity of each vehicle type for 80x120 cm pallets")    

        self.model.order_product_type = Param(self.model.orders, initialize=self.orders.groupby('Order ID')['Product Type'].apply(list).to_dict(), within=Any,
                              doc="The map of orders listed by product type")

        self.model.pallet_product_type = Param(self.model.pallets, initialize=self.pallets.set_index('Pallet ID')['Product Type'].to_dict(), within=Any,
                               doc="The map of pallets listed by product type")
        
        self.model.max_trips = Param(initialize=self.parameters['Value'].iloc[1])

        self.model.owned_vehicles.display()
        print("\n")
        self.model.products_in_pallet.display()
        print("\n")
        self.model.pallet_size.display()
        print("\n")
        self.model.pallet_release_day.display()
        print("\n")
        self.model.order_demand.display()
        print("\n")
        self.model.order_due_date.display()
        print("\n")
        self.model.warehouse_storage.display()
        print("\n")
        self.model.earliness_penalty.display()
        print("\n")
        self.model.owned_vehicle_cost.display()
        print("\n")
        self.model.rented_vehicle_cost.display()
        print("\n")
        self.model.vehicle_capacity_100x120.display()
        print("\n")
        self.model.vehicle_capacity_80x120.display()
        print("\n")
        self.model.order_product_type.display()
        print("\n")
        self.model.pallet_product_type.display()
        print("\n")
        self.model.max_trips.display()
        print("\n")
        

    def createVariables(self):
        self.model.is_shipped = Var(self.model.pallets, self.model.planning_horizon, within=Binary)

        self.model.owned_vehicle_trips = Var(self.model.vehicle_types, self.model.planning_horizon, self.model.size_types, within=NonNegativeIntegers)

        self.model.rented_vehicle_trips = Var(self.model.vehicle_types, self.model.planning_horizon, self.model.size_types, within=NonNegativeIntegers)

        self.model.order_pallet_match = Var(self.model.pallets, self.model.orders, within=Binary)

    def createObjectiveFunction(self):
        def total_cost(model):
            vehicle_cost = sum(
                model.owned_vehicle_cost[k] * model.owned_vehicle_trips[int(k), t, int(s)] +
                model.rented_vehicle_cost[k] * model.rented_vehicle_trips[k, t, s]
                for k in model.vehicle_types
                for t in model.planning_horizon
                for s in model.size_types
            )
            total_penalty = sum(
                model.earliness_penalty[o] * model.order_pallet_match[i, o] * 
                (model.order_due_date[o] - model.pallet_release_day[i])
                for o in model.orders
                for i in model.pallets
            )
            return vehicle_cost + total_penalty
        
        self.model.total_cost = Objective(rule=total_cost, sense=minimize,
                                        doc="Minimize total cost")
    
    def createConstraints(self):

        def constraint_1(model, i):
            return sum(model.is_shipped[i, t] for t in model.planning_horizon) == 1
            
        self.model.constraint_1 = Constraint(self.model.pallets, rule=constraint_1)

        def constraint_2(model, i):
            release_day = model.pallet_release_day[i]
            return sum(model.is_shipped[i, t] for t in range(1, release_day+1)) == 0
        
        self.model.constraint_2 = Constraint(self.model.pallets, rule=constraint_2)

        def constraint_3(model, t):
            total_shipped = sum(1 - model.is_shipped[i, t] for i in model.pallets)
            return total_shipped <= model.warehouse_storage
                
        self.model.constraint_3 = Constraint(self.model.planning_horizon, rule=constraint_3)

        def constraint_4(model, t):
            daily_capacity = 0
            for k in model.vehicle_types:
                for s in model.size_types:
                    daily_capacity += END395Model.capacity_calculator(model, k, s) * (model.owned_vehicle_trips[int(k), t, s] + model.rented_vehicle_trips[int(k), t, s])
            total = sum(model.is_shipped[i, t] for i in model.pallets)
            return total <= daily_capacity
        
        self.model.constraint_4 = Constraint(self.model.planning_horizon, rule=constraint_4)
        
        def constraint_5(model, k, t):
            max_trips = model.max_trips * model.owned_vehicles[k]
            return model.owned_vehicle_trips[k, t, 1] + model.owned_vehicle_trips[k, t, 2] <= max_trips
        
        self.model.constraint_5 = Constraint(self.model.vehicle_types, self.model.planning_horizon, rule=constraint_5)

        def constraint_6(model, o):
            return sum(model.order_pallet_match[i, o] for i in model.pallets if model.pallet_product_type[i] in model.order_product_type[o]) >= 1
        
        self.model.constraint_6 = Constraint(self.model.orders, rule=constraint_6)

#        def constraint_7(model, o):
 #           return sum(model.order_pallet_match[i, o] for i in model.pallets) <= model.order_demand[o]
        
#        self.model.constraint_7 = Constraint(self.model.orders, rule=constraint_7)

    def solve(self, solver_name):
        if solver_name == 'cplex':
            solver = SolverFactory('cplex')
        elif solver_name == 'gurobi':
            solver = SolverFactory('gurobi')
        else:
            raise ValueError("Solver not supported. Use 'cplex' or 'gurobi'.")

        results = solver.solve(self.model, tee=True) # tee here should print the results.
        
        if (results.solver.status != SolverStatus.ok) or (results.solver.termination_condition != TerminationCondition.optimal):
            raise RuntimeError("Solver failed to find an optimal solution.")
        
        return results
    
    def capacity_calculator(model, k, s):
        if s == 1:
            return model.vehicle_capacity_100x120[k]
        else:
            return model.vehicle_capacity_80x120[k]