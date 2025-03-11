import pandas as pd

orders = pd.read_excel("ProjectPart1-Scenario1.xlsx", sheet_name="Orders")
dicta=orders.groupby('Order ID')['Product Type'].apply(list).to_dict()
order_dict = orders.groupby('Order ID').apply(
    lambda x: dict(zip(x['Product Type'], x['Demand Amount']))
).to_dict()
print(order_dict[1]["P1"])