-- ============================================================================
-- SUPABASE POSTGRESQL SCHEMA FOR STOCK MANAGEMENT SYSTEM
-- ============================================================================
-- This script creates all tables, indexes, and constraints for the inventory
-- management system migrated from Google Sheets.
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE: suppliers
-- ============================================================================
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_code VARCHAR(20) UNIQUE NOT NULL, -- SUP001, SUP002, etc.
    supplier_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    payment_terms TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(supplier_code);
CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(supplier_name);

-- ============================================================================
-- TABLE: inventory
-- ============================================================================
CREATE TABLE IF NOT EXISTS inventory (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_code VARCHAR(20) UNIQUE NOT NULL, -- ITM001, ITM002, etc.
    category VARCHAR(50) NOT NULL CHECK (category IN ('Bags', 'Shoes', 'Wallets', 'Belts', 'Accessories', 'Other')),
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    sku VARCHAR(100),
    quantity_in_stock INTEGER NOT NULL DEFAULT 0 CHECK (quantity_in_stock >= 0),
    min_stock_level INTEGER NOT NULL DEFAULT 5,
    cost_price DECIMAL(10, 2) NOT NULL CHECK (cost_price >= 0),
    selling_price DECIMAL(10, 2) NOT NULL CHECK (selling_price >= 0),
    profit_margin DECIMAL(10, 2) GENERATED ALWAYS AS (selling_price - cost_price) STORED,
    supplier_id UUID REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    date_added DATE NOT NULL DEFAULT CURRENT_DATE,
    last_restocked DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_inventory_code ON inventory(item_code);
CREATE INDEX IF NOT EXISTS idx_inventory_category ON inventory(category);
CREATE INDEX IF NOT EXISTS idx_inventory_name ON inventory(item_name);
CREATE INDEX IF NOT EXISTS idx_inventory_supplier ON inventory(supplier_id);
CREATE INDEX IF NOT EXISTS idx_inventory_low_stock ON inventory(quantity_in_stock) WHERE quantity_in_stock <= min_stock_level;

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_inventory_search ON inventory USING GIN (to_tsvector('english', item_name || ' ' || COALESCE(description, '')));

-- ============================================================================
-- TABLE: users
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_code VARCHAR(20) UNIQUE NOT NULL, -- USR001, USR002, etc.
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('Admin', 'Staff')),
    account_status VARCHAR(20) NOT NULL DEFAULT 'Active' CHECK (account_status IN ('Active', 'Suspended', 'Locked')),
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_code ON users(user_code);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================================
-- TABLE: sales_log
-- ============================================================================
CREATE TABLE IF NOT EXISTS sales_log (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_code VARCHAR(30) UNIQUE NOT NULL, -- TXN20260118-001
    sale_date DATE NOT NULL DEFAULT CURRENT_DATE,
    sale_time TIME NOT NULL DEFAULT CURRENT_TIME,
    item_id UUID NOT NULL REFERENCES inventory(item_id) ON DELETE RESTRICT,
    quantity_sold INTEGER NOT NULL CHECK (quantity_sold > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    total_amount DECIMAL(10, 2) GENERATED ALWAYS AS (quantity_sold * unit_price) STORED,
    payment_method VARCHAR(50) NOT NULL CHECK (payment_method IN ('Cash', 'Card', 'Bank Transfer', 'Other')),
    sold_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for reporting
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_log(sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_sales_item ON sales_log(item_id);
CREATE INDEX IF NOT EXISTS idx_sales_sold_by ON sales_log(sold_by);
CREATE INDEX IF NOT EXISTS idx_sales_code ON sales_log(transaction_code);

-- ============================================================================
-- TABLE: restock_orders
-- ============================================================================
CREATE TABLE IF NOT EXISTS restock_orders (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_code VARCHAR(30) UNIQUE NOT NULL, -- PO20260118-001
    date_ordered DATE NOT NULL DEFAULT CURRENT_DATE,
    supplier_id UUID NOT NULL REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    item_id UUID NOT NULL REFERENCES inventory(item_id) ON DELETE RESTRICT,
    quantity_ordered INTEGER NOT NULL CHECK (quantity_ordered > 0),
    cost_per_unit DECIMAL(10, 2) NOT NULL CHECK (cost_per_unit >= 0),
    total_cost DECIMAL(10, 2) GENERATED ALWAYS AS (quantity_ordered * cost_per_unit) STORED,
    expected_delivery DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Received', 'Cancelled')),
    date_received DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraint: date_received should only be set when status is 'Received'
    CONSTRAINT check_received_date CHECK (
        (status = 'Received' AND date_received IS NOT NULL) OR
        (status != 'Received' AND date_received IS NULL)
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_restock_date ON restock_orders(date_ordered DESC);
CREATE INDEX IF NOT EXISTS idx_restock_supplier ON restock_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_restock_item ON restock_orders(item_id);
CREATE INDEX IF NOT EXISTS idx_restock_status ON restock_orders(status);
CREATE INDEX IF NOT EXISTS idx_restock_code ON restock_orders(order_code);

-- ============================================================================
-- TABLE: activity_log
-- ============================================================================
CREATE TABLE IF NOT EXISTS activity_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_log(action);
CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at DESC);

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE inventory IS 'Stores all inventory items with stock levels and pricing';
COMMENT ON TABLE sales_log IS 'Records all sales transactions';
COMMENT ON TABLE suppliers IS 'Supplier contact information and terms';
COMMENT ON TABLE restock_orders IS 'Purchase orders for restocking inventory';
COMMENT ON TABLE users IS 'User accounts with role-based access';
COMMENT ON TABLE activity_log IS 'Audit trail of all user actions';
