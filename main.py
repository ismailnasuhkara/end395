from model import END395Model
import pandas as pd

data = {}

model = END395Model(data)
model.solve('gurobi')