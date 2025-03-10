import pandas as pd

pallets = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Pallets")
dicta=pallets.set_index('Pallet ID')['Release Day'].to_dict()
print(dicta)