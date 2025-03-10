import pandas as pd

orders = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Orders")
dicta=orders.groupby('Order ID')['Product Type'].apply(list).to_dict()
print(dicta)