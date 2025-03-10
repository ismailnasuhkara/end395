def constraint_6(model):
            pallets_to_use = sum(
                sum(model.products_in_pallet[i] * model.is_shipped[i, t] for t in model.planning_horizon) * model.pallet_product_type[i]
                for i in model.pallets
            )
            order_to_fulfill = sum(
                model.order_demand[o] * model.order_product_type[o]
                for o in model.orders
            )
            return pallets_to_use >= order_to_fulfill

        self.model.constraint_6 = Constraint(rule=constraint_6)
