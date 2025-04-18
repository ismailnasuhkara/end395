from model import END395Model
import pandas as pd
import io
import time

start_time = time.time()

orders_1 = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Orders")
pallets_1 = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Pallets")
vehicles_1 = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Vehicles")
parameters_1 = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Parameters")

model_1 = END395Model(orders_1, pallets_1, vehicles_1, parameters_1)

"""
output = io.StringIO()
model_1.pprint(output)
text = output.getvalue()
output.close()

f = open("check.txt", "w")
f.write(text)
"""
model_1.solve('gurobi')

end_time = time.time()
print(f"\nCPU Time: {str(end_time - start_time)} seconds\n")