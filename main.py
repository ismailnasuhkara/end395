from model import END395Model
import pandas as pd

orders_1 = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Orders")
pallets_1 = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Pallets")
vehicles_1 = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Vehicles")
parameters_1 = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Parameters")



model_1 = END395Model(orders_1, pallets_1, vehicles_1, parameters_1)
#model_1.solve('gurobi')



