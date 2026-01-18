-- ============================================================================
-- FUNCTIONS AND TRIGGERS FOR STOCK MANAGEMENT SYSTEM
-- ============================================================================

-- ============================================================================
-- FUNCTION: Auto-update updated_at timestamp
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_suppliers_updated_at') THEN
        CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_inventory_updated_at') THEN
        CREATE TRIGGER update_inventory_updated_at BEFORE UPDATE ON inventory
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_users_updated_at') THEN
        CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_sales_updated_at') THEN
        CREATE TRIGGER update_sales_updated_at BEFORE UPDATE ON sales_log
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_restock_updated_at') THEN
        CREATE TRIGGER update_restock_updated_at BEFORE UPDATE ON restock_orders
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- ============================================================================
-- FUNCTION: Generate sequential supplier codes (SUP001, SUP002, etc.)
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_supplier_code()
RETURNS TRIGGER AS $$
DECLARE
    next_num INTEGER;
    new_code VARCHAR(20);
BEGIN
    -- Get the highest existing number
    SELECT COALESCE(MAX(CAST(SUBSTRING(supplier_code FROM 4) AS INTEGER)), 0) + 1
    INTO next_num
    FROM suppliers;
    
    -- Generate new code with zero-padding
    new_code := 'SUP' || LPAD(next_num::TEXT, 3, '0');
    NEW.supplier_code := new_code;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'auto_supplier_code') THEN
        CREATE TRIGGER auto_supplier_code BEFORE INSERT ON suppliers
            FOR EACH ROW
            WHEN (NEW.supplier_code IS NULL OR NEW.supplier_code = '')
            EXECUTE FUNCTION generate_supplier_code();
    END IF;
END $$;

-- ============================================================================
-- FUNCTION: Generate sequential item codes (ITM001, ITM002, etc.)
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_item_code()
RETURNS TRIGGER AS $$
DECLARE
    next_num INTEGER;
    new_code VARCHAR(20);
BEGIN
    -- Get the highest existing number
    SELECT COALESCE(MAX(CAST(SUBSTRING(item_code FROM 4) AS INTEGER)), 0) + 1
    INTO next_num
    FROM inventory;
    
    -- Generate new code with zero-padding
    new_code := 'ITM' || LPAD(next_num::TEXT, 3, '0');
    NEW.item_code := new_code;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'auto_item_code') THEN
        CREATE TRIGGER auto_item_code BEFORE INSERT ON inventory
            FOR EACH ROW
            WHEN (NEW.item_code IS NULL OR NEW.item_code = '')
            EXECUTE FUNCTION generate_item_code();
    END IF;
END $$;

-- ============================================================================
-- FUNCTION: Generate sequential user codes (USR001, USR002, etc.)
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_user_code()
RETURNS TRIGGER AS $$
DECLARE
    next_num INTEGER;
    new_code VARCHAR(20);
BEGIN
    -- Get the highest existing number
    SELECT COALESCE(MAX(CAST(SUBSTRING(user_code FROM 4) AS INTEGER)), 0) + 1
    INTO next_num
    FROM users;
    
    -- Generate new code with zero-padding
    new_code := 'USR' || LPAD(next_num::TEXT, 3, '0');
    NEW.user_code := new_code;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'auto_user_code') THEN
        CREATE TRIGGER auto_user_code BEFORE INSERT ON users
            FOR EACH ROW
            WHEN (NEW.user_code IS NULL OR NEW.user_code = '')
            EXECUTE FUNCTION generate_user_code();
    END IF;
END $$;

-- ============================================================================
-- FUNCTION: Generate transaction codes (TXN20260118-001)
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_transaction_code()
RETURNS TRIGGER AS $$
DECLARE
    today_str VARCHAR(8);
    next_num INTEGER;
    new_code VARCHAR(30);
BEGIN
    -- Format: TXNYYYYMMDD-NNN
    today_str := TO_CHAR(CURRENT_DATE, 'YYYYMMDD');
    
    -- Get the highest transaction number for today
    SELECT COALESCE(MAX(CAST(SUBSTRING(transaction_code FROM 16) AS INTEGER)), 0) + 1
    INTO next_num
    FROM sales_log
    WHERE transaction_code LIKE 'TXN' || today_str || '%';
    
    -- Generate new code
    new_code := 'TXN' || today_str || '-' || LPAD(next_num::TEXT, 3, '0');
    NEW.transaction_code := new_code;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'auto_transaction_code') THEN
        CREATE TRIGGER auto_transaction_code BEFORE INSERT ON sales_log
            FOR EACH ROW
            WHEN (NEW.transaction_code IS NULL OR NEW.transaction_code = '')
            EXECUTE FUNCTION generate_transaction_code();
    END IF;
END $$;

-- ============================================================================
-- FUNCTION: Generate purchase order codes (PO20260118-001)
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_order_code()
RETURNS TRIGGER AS $$
DECLARE
    today_str VARCHAR(8);
    next_num INTEGER;
    new_code VARCHAR(30);
BEGIN
    -- Format: POYYYYMMDD-NNN
    today_str := TO_CHAR(CURRENT_DATE, 'YYYYMMDD');
    
    -- Get the highest order number for today
    SELECT COALESCE(MAX(CAST(SUBSTRING(order_code FROM 14) AS INTEGER)), 0) + 1
    INTO next_num
    FROM restock_orders
    WHERE order_code LIKE 'PO' || today_str || '%';
    
    -- Generate new code
    new_code := 'PO' || today_str || '-' || LPAD(next_num::TEXT, 3, '0');
    NEW.order_code := new_code;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'auto_order_code') THEN
        CREATE TRIGGER auto_order_code BEFORE INSERT ON restock_orders
            FOR EACH ROW
            WHEN (NEW.order_code IS NULL OR NEW.order_code = '')
            EXECUTE FUNCTION generate_order_code();
    END IF;
END $$;

-- ============================================================================
-- FUNCTION: Validate stock before sale
-- ============================================================================
CREATE OR REPLACE FUNCTION validate_stock_before_sale()
RETURNS TRIGGER AS $$
DECLARE
    current_stock INTEGER;
BEGIN
    -- Get current stock level
    SELECT quantity_in_stock INTO current_stock
    FROM inventory
    WHERE item_id = NEW.item_id;
    
    -- Check if enough stock
    IF current_stock < NEW.quantity_sold THEN
        RAISE EXCEPTION 'Insufficient stock. Available: %, Requested: %', current_stock, NEW.quantity_sold;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'check_stock_before_sale') THEN
        CREATE TRIGGER check_stock_before_sale BEFORE INSERT ON sales_log
            FOR EACH ROW EXECUTE FUNCTION validate_stock_before_sale();
    END IF;
END $$;

-- ============================================================================
-- FUNCTION: Update inventory after sale
-- ============================================================================
CREATE OR REPLACE FUNCTION update_inventory_after_sale()
RETURNS TRIGGER AS $$
BEGIN
    -- Reduce stock quantity
    UPDATE inventory
    SET quantity_in_stock = quantity_in_stock - NEW.quantity_sold
    WHERE item_id = NEW.item_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'reduce_stock_after_sale') THEN
        CREATE TRIGGER reduce_stock_after_sale AFTER INSERT ON sales_log
            FOR EACH ROW EXECUTE FUNCTION update_inventory_after_sale();
    END IF;
END $$;

-- ============================================================================
-- FUNCTION: Update inventory after restock order received
-- ============================================================================
CREATE OR REPLACE FUNCTION update_inventory_after_restock()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if status changed to 'Received'
    IF NEW.status = 'Received' AND (OLD.status IS NULL OR OLD.status != 'Received') THEN
        UPDATE inventory
        SET 
            quantity_in_stock = quantity_in_stock + NEW.quantity_ordered,
            last_restocked = NEW.date_received
        WHERE item_id = NEW.item_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'add_stock_after_restock') THEN
        CREATE TRIGGER add_stock_after_restock AFTER UPDATE ON restock_orders
            FOR EACH ROW EXECUTE FUNCTION update_inventory_after_restock();
    END IF;
END $$;

-- ============================================================================
-- FUNCTION: Get low stock items
-- ============================================================================
CREATE OR REPLACE FUNCTION get_low_stock_items()
RETURNS TABLE (
    item_code VARCHAR,
    item_name VARCHAR,
    category VARCHAR,
    quantity_in_stock INTEGER,
    min_stock_level INTEGER,
    shortage INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.item_code,
        i.item_name,
        i.category,
        i.quantity_in_stock,
        i.min_stock_level,
        (i.min_stock_level - i.quantity_in_stock) AS shortage
    FROM inventory i
    WHERE i.quantity_in_stock <= i.min_stock_level
    ORDER BY (i.min_stock_level - i.quantity_in_stock) DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: Calculate total inventory value
-- ============================================================================
CREATE OR REPLACE FUNCTION calculate_inventory_value()
RETURNS TABLE (
    total_cost_value DECIMAL,
    total_selling_value DECIMAL,
    potential_profit DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        SUM(quantity_in_stock * cost_price) AS total_cost_value,
        SUM(quantity_in_stock * selling_price) AS total_selling_value,
        SUM(quantity_in_stock * profit_margin) AS potential_profit
    FROM inventory;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: Get sales summary for date range
-- ============================================================================
CREATE OR REPLACE FUNCTION get_sales_summary(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    total_transactions BIGINT,
    total_items_sold BIGINT,
    total_revenue DECIMAL,
    avg_transaction_value DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT transaction_id) AS total_transactions,
        SUM(quantity_sold) AS total_items_sold,
        SUM(total_amount) AS total_revenue,
        AVG(total_amount) AS avg_transaction_value
    FROM sales_log
    WHERE sale_date BETWEEN start_date AND end_date;
END;
$$ LANGUAGE plpgsql;
