import pandas as pd
from pyomo.environ import *

orders = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Orders")
pallets = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Pallets")
vehicles = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Vehicles")
parameters = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Parameters")

pallet_amount = pallets.groupby('Product Type')['Amount'].apply(list).to_dict()
order_amount = orders.groupby('Product Type')['Demand Amount'].apply(list).to_dict()

print(pallet_amount, "\n")
print(order_amount, "\n")