
# few_shots_retail.py  
FEW_SHOTS = [
    {"q": "How many Nike White size L are in stock?",
     "sql": "SELECT SUM(`stock_quantity`) FROM `t_shirts` WHERE `brand`='Nike' AND `color`='White' AND `size`='L'"},
    {"q": "Stock by color for Nike",
     "sql": "SELECT `color`, SUM(`stock_quantity`) FROM `t_shirts` WHERE `brand`='Nike' GROUP BY `color` ORDER BY `color`"},
    {"q": "Price and stock for Levi Black XL",
     "sql": "SELECT `price`, `stock_quantity` FROM `t_shirts` WHERE `brand`='Levi' AND `color`='Black' AND `size`='XL'"},
    {"q": "Total inventory value for Levi",
     "sql": "SELECT SUM(`price`*`stock_quantity`) FROM `t_shirts` WHERE `brand`='Levi'"},
    {"q": "Among discounted items, which SKU gives highest revenue if sold out?",
     "sql": "SELECT t.`brand`, t.`color`, t.`size`, t.`price`, t.`stock_quantity`, d.`pct_discount`, "
            "(t.`price`*t.`stock_quantity`*((100-COALESCE(d.`pct_discount`,0))/100)) AS net_revenue "
            "FROM `t_shirts` t INNER JOIN `discounts` d ON t.`t_shirt_id`=d.`t_shirt_id` "
            "ORDER BY net_revenue DESC, t.`t_shirt_id` ASC LIMIT 1"}
]
