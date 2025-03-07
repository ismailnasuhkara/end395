from model import END395Model

data = {}

model = END395Model(data)
model.solve('gurobi')