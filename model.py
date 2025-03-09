from pyomo.environ import *

class END395Model:
    def __init__(self, data):
        # data: A database containing all the required data
        self.data = data
        self.model = ConcreteModel()
        self.createSets()
        self.createParameters()
        self.createVariables()
        self.createObjectiveFunction()
        self.createConstraints()


    def createSets(self):
        self.model.planning_horizon = Set(initialize=self.data['planning_horizon'],
                                          doc="Set of days in the planning horizon")
        
        self.model.product_type = Set(initialize=self.data['product_type'],
                                      doc="Set of product types")
        
        # 1 = Truck, 2 = Lorry, 3 = Van
        self.model.vehicle_types = Set(initialize=self.data['vehicle_types'],
                                       doc="Set of vehicle types")

        self.model.pallets = Set(initialize=self.data['pallets'],
                                 doc="Set of pallets")
        
        self.model.orders = Set(initialize=self.data['orders'],
                                doc="Set of orders")
        

    def createParameters(self):
        self.model.owned_vehicles = Param(self.model.vehicle_types, initialize=self.data['owned_vehicles'],
                                          doc="Number of owned vehicles of each type")

        self.model.products_in_pallet = Param(self.model.pallets, initialize=self.data['products_in_pallet'],
                                            doc="Number of products that can be stored in each pallet")

        # 1 = 100x120 cm, 2 = 80x120 cm
        self.model.pallet_size = Param(self.model.pallets, initialize=self.data['pallet_size'],
                                        doc="Size of each pallet")
        
        self.model.pallet_release_day = Param(self.model.pallets, initialize=self.data['pallet_release_day'],
                                                   doc="The release day of each pallet")
        
        self.model.order_demand = Param(self.model.orders, initialize=self.data['order_demand'],
                                         doc="Number of products required for each order")
        
        self.model.order_due_date = Param(self.model.orders, initialize=self.data['order_due_date'],
                                          doc="Due date of each order")
        
        self.model.warehouse_storage = Param(initialize=self.data['warehouse_storage'],
                                                       doc="Warehouse storage capacity in terms of pallets")
        
        self.model.earliness_penalty = Param(self.model.orders, initialize=self.data['earliness_penalty'],
                                             doc="Earliness penalty cost of each order")
        
        self.model.owned_vehicle_cost = Param(self.model.vehicle_types, initialize=self.data['owned_vehicle_cost'],
                                              doc="Delivery cost of each owned vehicle")
        
        self.model.rented_vehicle_cost = Param(self.model.vehicle_types, initialize=self.data['rented_vehicle_cost'],
                                               doc="Delivery cost of each rented vehicle")
        
        # Truck = 22, Lorry = 12, Van = 6
        self.model.vehicle_capacity_100x120 = Param(self.model.vehicle_types, initialize=self.data['vehicle_capacity_100x120'],
                                                    doc="Capacity of each vehicle type for 100x120 cm pallets")
        
        # Truck = 33, Lorry = 18, Van = 8
        self.model.vehicle_capacity_80x120 = Param(self.model.vehicle_types, initialize=self.data['vehicle_capacity_80x120'],
                                                   doc="Capacity of each vehicle type for 80x120 cm pallets")
        
        self.model.owned_vehicles = Param(self.model.vehicle_types, initialize=self.data['owned_vehicles'],
                                        doc="Number of owned vehicles for each vehicle type.")
        
        self.model.order_pallet_is_assigned = Param(self.model.pallets, self.model.planning_horizon, initialize=self.data['orders'],
                                                    doc="Tracks the pallets assigned to each order.")     

        self.model.order_product_type = Param(self.model.orders, self.model.product_type,
                                                  doc="The map of orders listed by product type.")

        self.model.pallet_product_type = Param(self.model.pallets, self.model.product_type,
                                               doc="The map of pallets listed by product type.")
        

    def createVariables(self):
        self.model.is_shipped = Var(self.model.pallets, self.model.planning_horizon, within=Binary)

        self.model.owned_vehicle_trips = Var(self.model.vehicle_types, self.model.planning_horizon, self.model.pallet_size, within=NonNegativeIntegers)

        self.model.rented_vehicle_trips = Var(self.model.vehicle_types, self.model.planning_horizon, self.model.pallet_size, within=NonNegativeIntegers)
  

    def createObjectiveFunction(self):
        self.model.total_cost = Objective(rule=self.total_cost(self.model), sense=minimize,
                                        doc="Minimize total cost")
    

    def createConstraints(self):
        def constraint_1(model, i):
            return sum(model.is_shipped[i, t] for t in model.planning_horizon) == 1
            
        self.model.constraint_1 = Constraint(self.model.pallets, rule=constraint_1)

        def constraint_2(model, i, t):
            for t in range(1, model.pallet_release_day[i] - 1):
                if model.is_shipped[i, t] != 0:
                    return False
            return True
        
        self.model.constraint_2 = Constraint(self.model.pallets, rule=constraint_2)

        def constraint_3(model, t):
            total_shipped = sum(model.is_shipped[i, t] == 0 for i in model.pallets)
            return total_shipped <= model.warehouse_storage
                
        self.model.constraint_3 = Constraint(self.model.planning_horizon, rule=constraint_3)

        def constraint_4(model, i, t):
            daily_capacity = 0
            for k in model.vehicle_types:
                for s in model.pallet_size:
                    daily_capacity += model.capacity_calculator(model, k, s) * (model.owned_vehicle_trips[k, t, s] + model.rented_vehicle_trips[k, t, s])
            sum = sum(model.is_shipped[i, t] for i in model.pallets)

            if sum > daily_capacity:
                return False
            else:
                return True
        
        self.model.constraint_4 = Constraint(self.model.pallets, self.model.planning_horizon, rule=constraint_4)
        
        def constraint_5(model, k, t):
            max_trips = 3 * model.owned_vehicles[k]
            return model.owned_vehicle_trips[k, t, 1] + model.owned_vehicle_trips[k, t, 2] <= max_trips
        
        self.model.constraint_5 = Constraint(self.model.vehicle_types, self.model.planning_horizon, rule=constraint_5)

        def constraint_6(model, p):
            pallets_to_use = sum(
                model.products_in_pallet[i] * sum(model.is_shipped[i, t] for t in model.planning_horizon) * model.pallet_product_type[i, p]
                for i in model.pallets
            )
            order_to_fulfill = sum(
                model.order_demand[o] * model.order_product_type[o, p]
                for o in model.orders
            )
            return pallets_to_use >= order_to_fulfill

        self.model.constraint_6 = Constraint(self.model.orders, self.model.product_type, rule=constraint_6)


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


    def total_cost(model):
            vehicle_cost = sum(
                model.owned_vehicle_cost[k] * model.owned_vehicle_trips[k, t, s] +
                model.rented_vehicle_cost[k] * model.rented_vehicle_trips[k, t, s]
                for k in model.vehicle_types
                for t in model.planning_horizon
                for s in model.pallet_size
            )
            total_penalty = sum(
                model.earliness_penalty[o] * model.order_pallet_is_assigned[i, o] * 
                (model.order_due_date[o] - model.pallet_release_day[i])
                for o in model.orders
                for i in model.pallets
            )
            return vehicle_cost + total_penalty
    
    def capacity_calculator(model, k, s):
        if s == 1:
            return model.vehicle_capacity_100x120[k]
        else:
            return model.vehicle_capacity_80x120[k]