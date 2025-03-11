import pandas as pd
from pyomo.environ import *

orders = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Orders")
pallets = [1, 2, 3, 4, 5, 6, 7]
vehicles = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Vehicles")
parameters = [1, 2, 3]

model = ConcreteModel()

model.planning_horizon = Set(initialize=range(1, parameters),
                          doc="Set of days in the planning horizon")

model.pallets = Set(initialize=pallets['Pallet ID'],
                     doc="Set of pallets")

model.is_shipped = Var(model.pallets, model.planning_horizon, within=Binary)

def constraint_1(model, i):
            return sum(model.is_shipped[i, t] for t in model.planning_horizon) == 1
            
model.constraint_1 = Constraint(model.pallets, rule=constraint_1)

model.constraint_1.display()
