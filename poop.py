import pandas as pd
loading_types = pd.read_excel("Part2-Scenario1.xlsx", sheet_name="LoadingTypes")
print(loading_types[loading_types["VehicleType"] == 1]["LoadingType"])