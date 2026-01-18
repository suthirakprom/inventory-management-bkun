-- ============================================================================
-- DATABASE VIEWS FOR REPORTING
-- ============================================================================
-- These views simplify common queries and improve performance for reports
-- ============================================================================

-- ============================================================================
-- VIEW: inventory_value_view
-- Purpose: Calculate total inventory value by category
-- ============================================================================
CREATE OR REPLACE VIEW inventory_value_view AS
SELECT 
    category,
    COUNT(*) AS item_count,
    SUM(quantity_in_stock) AS total_units,
    SUM(quantity_in_stock * cost_price) AS total_cost_value,
    SUM(quantity_in_stock * selling_price) AS total_selling_value,
    SUM(quantity_in_stock * profit_margin) AS potential_profit,
    ROUND(AVG(profit_margin), 2) AS avg_profit_per_item
FROM inventory
GROUP BY category
ORDER BY total_selling_value DESC;

-- ============================================================================
-- VIEW: low_stock_view
-- Purpose: Items that need restocking
-- ============================================================================
CREATE OR REPLACE VIEW low_stock_view AS
SELECT 
    i.item_code,
    i.item_name,
    i.category,
    i.quantity_in_stock,
    i.min_stock_level,
    (i.min_stock_level - i.quantity_in_stock) AS shortage,
    s.supplier_name,
    s.phone AS supplier_phone,
    i.cost_price,
    (i.min_stock_level - i.quantity_in_stock) * i.cost_price AS restock_cost_estimate
FROM inventory i
LEFT JOIN suppliers s ON i.supplier_id = s.supplier_id
WHERE i.quantity_in_stock <= i.min_stock_level
ORDER BY (i.min_stock_level - i.quantity_in_stock) DESC;

-- ============================================================================
-- VIEW: daily_sales_summary
-- Purpose: Daily sales aggregation
-- ============================================================================
CREATE OR REPLACE VIEW daily_sales_summary AS
SELECT 
    sale_date,
    COUNT(DISTINCT transaction_id) AS total_transactions,
    SUM(quantity_sold) AS total_items_sold,
    SUM(total_amount) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_transaction_value,
    COUNT(DISTINCT item_id) AS unique_items_sold
FROM sales_log
GROUP BY sale_date
ORDER BY sale_date DESC;

-- ============================================================================
-- VIEW: weekly_sales_summary
-- Purpose: Weekly sales aggregation
-- ============================================================================
CREATE OR REPLACE VIEW weekly_sales_summary AS
SELECT 
    DATE_TRUNC('week', sale_date) AS week_start,
    COUNT(DISTINCT transaction_id) AS total_transactions,
    SUM(quantity_sold) AS total_items_sold,
    SUM(total_amount) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_transaction_value,
    COUNT(DISTINCT item_id) AS unique_items_sold
FROM sales_log
GROUP BY DATE_TRUNC('week', sale_date)
ORDER BY week_start DESC;

-- ============================================================================
-- VIEW: monthly_sales_summary
-- Purpose: Monthly sales aggregation
-- ============================================================================
CREATE OR REPLACE VIEW monthly_sales_summary AS
SELECT 
    DATE_TRUNC('month', sale_date) AS month_start,
    TO_CHAR(sale_date, 'YYYY-MM') AS month_label,
    COUNT(DISTINCT transaction_id) AS total_transactions,
    SUM(quantity_sold) AS total_items_sold,
    SUM(total_amount) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_transaction_value,
    COUNT(DISTINCT item_id) AS unique_items_sold
FROM sales_log
GROUP BY DATE_TRUNC('month', sale_date), TO_CHAR(sale_date, 'YYYY-MM')
ORDER BY month_start DESC;

-- ============================================================================
-- VIEW: best_sellers_view
-- Purpose: Top selling items by revenue and quantity
-- ============================================================================
CREATE OR REPLACE VIEW best_sellers_view AS
SELECT 
    i.item_code,
    i.item_name,
    i.category,
    COUNT(s.transaction_id) AS times_sold,
    SUM(s.quantity_sold) AS total_quantity_sold,
    SUM(s.total_amount) AS total_revenue,
    ROUND(AVG(s.unit_price), 2) AS avg_selling_price,
    i.cost_price,
    SUM(s.quantity_sold * (s.unit_price - i.cost_price)) AS total_profit,
    i.quantity_in_stock AS current_stock
FROM inventory i
INNER JOIN sales_log s ON i.item_id = s.item_id
GROUP BY i.item_id, i.item_code, i.item_name, i.category, i.cost_price, i.quantity_in_stock
ORDER BY total_revenue DESC;

-- ============================================================================
-- VIEW: slow_movers_view
-- Purpose: Items with low sales velocity
-- ============================================================================
CREATE OR REPLACE VIEW slow_movers_view AS
SELECT 
    i.item_code,
    i.item_name,
    i.category,
    i.quantity_in_stock,
    i.date_added,
    CURRENT_DATE - i.date_added AS days_in_inventory,
    COALESCE(SUM(s.quantity_sold), 0) AS total_sold,
    COALESCE(COUNT(s.transaction_id), 0) AS times_sold,
    i.quantity_in_stock * i.cost_price AS tied_up_capital,
    CASE 
        WHEN CURRENT_DATE - i.date_added > 0 THEN
            ROUND(COALESCE(SUM(s.quantity_sold), 0)::DECIMAL / (CURRENT_DATE - i.date_added), 2)
        ELSE 0
    END AS avg_daily_sales
FROM inventory i
LEFT JOIN sales_log s ON i.item_id = s.item_id
GROUP BY i.item_id, i.item_code, i.item_name, i.category, i.quantity_in_stock, i.date_added, i.cost_price
HAVING COALESCE(SUM(s.quantity_sold), 0) < 5 OR 
       (CURRENT_DATE - i.date_added > 30 AND COALESCE(COUNT(s.transaction_id), 0) = 0)
ORDER BY tied_up_capital DESC;

-- ============================================================================
-- VIEW: category_performance_view
-- Purpose: Sales performance by category
-- ============================================================================
CREATE OR REPLACE VIEW category_performance_view AS
SELECT 
    i.category,
    COUNT(DISTINCT i.item_id) AS total_items,
    COUNT(s.transaction_id) AS total_transactions,
    SUM(s.quantity_sold) AS total_units_sold,
    SUM(s.total_amount) AS total_revenue,
    SUM(s.quantity_sold * (s.unit_price - i.cost_price)) AS total_profit,
    ROUND(AVG(s.unit_price), 2) AS avg_selling_price,
    SUM(i.quantity_in_stock) AS current_stock_units,
    SUM(i.quantity_in_stock * i.cost_price) AS current_stock_value
FROM inventory i
LEFT JOIN sales_log s ON i.item_id = s.item_id
GROUP BY i.category
ORDER BY total_revenue DESC NULLS LAST;

-- ============================================================================
-- VIEW: payment_method_summary
-- Purpose: Sales breakdown by payment method
-- ============================================================================
CREATE OR REPLACE VIEW payment_method_summary AS
SELECT 
    payment_method,
    COUNT(transaction_id) AS transaction_count,
    SUM(quantity_sold) AS total_items,
    SUM(total_amount) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_transaction_value,
    ROUND(SUM(total_amount) * 100.0 / SUM(SUM(total_amount)) OVER (), 2) AS revenue_percentage
FROM sales_log
GROUP BY payment_method
ORDER BY total_revenue DESC;

-- ============================================================================
-- VIEW: supplier_performance_view
-- Purpose: Evaluate supplier relationships
-- ============================================================================
CREATE OR REPLACE VIEW supplier_performance_view AS
SELECT 
    s.supplier_code,
    s.supplier_name,
    s.contact_person,
    s.phone,
    COUNT(DISTINCT i.item_id) AS items_supplied,
    COUNT(ro.order_id) AS total_orders,
    SUM(CASE WHEN ro.status = 'Received' THEN 1 ELSE 0 END) AS completed_orders,
    SUM(CASE WHEN ro.status = 'Pending' THEN 1 ELSE 0 END) AS pending_orders,
    SUM(CASE WHEN ro.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
    SUM(CASE WHEN ro.status = 'Received' THEN ro.total_cost ELSE 0 END) AS total_spent,
    SUM(i.quantity_in_stock) AS current_stock_from_supplier,
    SUM(i.quantity_in_stock * i.cost_price) AS current_inventory_value
FROM suppliers s
LEFT JOIN inventory i ON s.supplier_id = i.supplier_id
LEFT JOIN restock_orders ro ON s.supplier_id = ro.supplier_id
GROUP BY s.supplier_id, s.supplier_code, s.supplier_name, s.contact_person, s.phone
ORDER BY total_spent DESC NULLS LAST;

-- ============================================================================
-- VIEW: user_activity_summary
-- Purpose: User performance metrics
-- ============================================================================
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT 
    u.user_code,
    u.username,
    u.role,
    COUNT(s.transaction_id) AS total_sales,
    SUM(s.quantity_sold) AS total_items_sold,
    SUM(s.total_amount) AS total_revenue_generated,
    ROUND(AVG(s.total_amount), 2) AS avg_transaction_value,
    COUNT(DISTINCT DATE(s.sale_date)) AS days_active,
    MAX(s.sale_date) AS last_sale_date
FROM users u
LEFT JOIN sales_log s ON u.user_id = s.sold_by
WHERE u.role = 'Staff' OR u.role = 'Admin'
GROUP BY u.user_id, u.user_code, u.username, u.role
ORDER BY total_revenue_generated DESC NULLS LAST;

-- ============================================================================
-- VIEW: restock_status_view
-- Purpose: Current restock order status
-- ============================================================================
CREATE OR REPLACE VIEW restock_status_view AS
SELECT 
    ro.order_code,
    ro.date_ordered,
    ro.expected_delivery,
    ro.status,
    s.supplier_name,
    i.item_code,
    i.item_name,
    ro.quantity_ordered,
    ro.cost_per_unit,
    ro.total_cost,
    CASE 
        WHEN ro.status = 'Pending' AND ro.expected_delivery < CURRENT_DATE THEN 'OVERDUE'
        WHEN ro.status = 'Pending' AND ro.expected_delivery = CURRENT_DATE THEN 'DUE TODAY'
        WHEN ro.status = 'Pending' THEN 'ON TIME'
        ELSE ro.status
    END AS delivery_status,
    CURRENT_DATE - ro.date_ordered AS days_since_ordered
FROM restock_orders ro
INNER JOIN suppliers s ON ro.supplier_id = s.supplier_id
INNER JOIN inventory i ON ro.item_id = i.item_id
ORDER BY ro.date_ordered DESC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON VIEW inventory_value_view IS 'Total inventory value and profit potential by category';
COMMENT ON VIEW low_stock_view IS 'Items below minimum stock level that need restocking';
COMMENT ON VIEW daily_sales_summary IS 'Daily sales aggregation for quick reporting';
COMMENT ON VIEW weekly_sales_summary IS 'Weekly sales aggregation for trend analysis';
COMMENT ON VIEW monthly_sales_summary IS 'Monthly sales aggregation for business reviews';
COMMENT ON VIEW best_sellers_view IS 'Top performing items by revenue and quantity';
COMMENT ON VIEW slow_movers_view IS 'Items with low sales velocity that may need attention';
COMMENT ON VIEW category_performance_view IS 'Sales and inventory metrics by product category';
COMMENT ON VIEW payment_method_summary IS 'Revenue breakdown by payment method';
COMMENT ON VIEW supplier_performance_view IS 'Supplier relationship metrics and performance';
COMMENT ON VIEW user_activity_summary IS 'User sales performance and activity metrics';
COMMENT ON VIEW restock_status_view IS 'Current status of all restock orders';
