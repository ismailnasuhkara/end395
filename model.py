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
        
        self.model.pallet_shipment_day = Param(self.model.pallets, initialize=self.data['pallet_shipment_day'],
                                                   doc="The shipment day of each pallet")
        
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

    def createVariables(self):
        self.model.pallet_shipment = Var(self.model.pallets, self.model.planning_horizon, within=Binary)

        self.model.owned_vehicle_trips = Var(self.model.vehicle_types, self.model.planning_horizon, self.model.pallet_size, within=NonNegativeIntegers)

        self.model.rented_vehicle_trips = Var(self.model.vehicle_types, self.model.planning_horizon, self.model.pallet_size, within=NonNegativeIntegers)

        self.model.pallet_order_match = Var(self.model.pallets, self.model.orders, self.model.planning_horizon, within=Binary)

        self.model.warehouse_storage = Var(self.model.pallets, self.model.planning_horizon, within=Binary)        


    def createObjectiveFunction(self):
        self.model.total_cost = Objective(rule=self.total_cost(self.model), sense=minimize,
                                        doc="Minimize total cost")
    

    def createConstraints(self):
        self.model.constraints = ConstraintList()
        '''
            Buraya for loopları dizerek kısıtları yazacağız.
            Her kısıtı self.model.constraints.add(expr=) ile ekleyeceğiz.
            constraints'e index atmalı mıyız bilmiyorum.
        '''  
    

    def solve(self, solver_name):
        if solver_name == 'cplex':
            solver = SolverFactory('cplex')
        elif solver_name == 'gurobi':
            solver = SolverFactory('gurobi')
        else:
            raise ValueError("Solver not supported. Use 'cplex' or 'gurobi'.")

        results = solver.solve(self.model, tee=True) # tee here should print the results.
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
                model.earliness_penalty[o] * model.pallet_order_match[i, o] * 
                (model.order_due_date[o] - model.shipment_day[i])
                for o in model.orders
                for i in model.pallets
            )
            return vehicle_cost + total_penalty