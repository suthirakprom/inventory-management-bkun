-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================
-- This script sets up Row Level Security policies for role-based access control.
-- 
-- ROLES:
-- - Admin: Full access to all tables
-- - Staff: Read/write access to inventory, sales, suppliers, restock orders
--          NO access to users table or other users' activity logs
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE restock_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- HELPER FUNCTION: Get current user's role
-- ============================================================================
-- This function retrieves the role of the currently authenticated user
-- from the users table based on the user_id stored in JWT claims
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS TEXT AS $$
BEGIN
    RETURN (
        SELECT role 
        FROM users 
        WHERE user_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- INVENTORY TABLE POLICIES
-- ============================================================================

-- Admin: Full access
CREATE POLICY "Admin full access to inventory"
ON inventory
FOR ALL
TO authenticated
USING (get_user_role() = 'Admin')
WITH CHECK (get_user_role() = 'Admin');

-- Staff: Read and update access (can view and modify inventory)
CREATE POLICY "Staff read access to inventory"
ON inventory
FOR SELECT
TO authenticated
USING (get_user_role() = 'Staff');

CREATE POLICY "Staff update access to inventory"
ON inventory
FOR UPDATE
TO authenticated
USING (get_user_role() = 'Staff')
WITH CHECK (get_user_role() = 'Staff');

CREATE POLICY "Staff insert access to inventory"
ON inventory
FOR INSERT
TO authenticated
WITH CHECK (get_user_role() = 'Staff');

-- ============================================================================
-- SALES_LOG TABLE POLICIES
-- ============================================================================

-- Admin: Full access
CREATE POLICY "Admin full access to sales_log"
ON sales_log
FOR ALL
TO authenticated
USING (get_user_role() = 'Admin')
WITH CHECK (get_user_role() = 'Admin');

-- Staff: Can insert and view sales
CREATE POLICY "Staff read access to sales_log"
ON sales_log
FOR SELECT
TO authenticated
USING (get_user_role() = 'Staff');

CREATE POLICY "Staff insert access to sales_log"
ON sales_log
FOR INSERT
TO authenticated
WITH CHECK (get_user_role() = 'Staff');

-- ============================================================================
-- SUPPLIERS TABLE POLICIES
-- ============================================================================

-- Admin: Full access
CREATE POLICY "Admin full access to suppliers"
ON suppliers
FOR ALL
TO authenticated
USING (get_user_role() = 'Admin')
WITH CHECK (get_user_role() = 'Admin');

-- Staff: Read-only access
CREATE POLICY "Staff read access to suppliers"
ON suppliers
FOR SELECT
TO authenticated
USING (get_user_role() = 'Staff');

-- ============================================================================
-- RESTOCK_ORDERS TABLE POLICIES
-- ============================================================================

-- Admin: Full access
CREATE POLICY "Admin full access to restock_orders"
ON restock_orders
FOR ALL
TO authenticated
USING (get_user_role() = 'Admin')
WITH CHECK (get_user_role() = 'Admin');

-- Staff: Can view and create restock orders
CREATE POLICY "Staff read access to restock_orders"
ON restock_orders
FOR SELECT
TO authenticated
USING (get_user_role() = 'Staff');

CREATE POLICY "Staff insert access to restock_orders"
ON restock_orders
FOR INSERT
TO authenticated
WITH CHECK (get_user_role() = 'Staff');

CREATE POLICY "Staff update access to restock_orders"
ON restock_orders
FOR UPDATE
TO authenticated
USING (get_user_role() = 'Staff')
WITH CHECK (get_user_role() = 'Staff');

-- ============================================================================
-- USERS TABLE POLICIES
-- ============================================================================

-- Admin: Full access to all users
CREATE POLICY "Admin full access to users"
ON users
FOR ALL
TO authenticated
USING (get_user_role() = 'Admin')
WITH CHECK (get_user_role() = 'Admin');

-- Staff: Can only view and update their own profile
CREATE POLICY "Staff can view own profile"
ON users
FOR SELECT
TO authenticated
USING (user_id = auth.uid() AND get_user_role() = 'Staff');

CREATE POLICY "Staff can update own profile"
ON users
FOR UPDATE
TO authenticated
USING (user_id = auth.uid() AND get_user_role() = 'Staff')
WITH CHECK (user_id = auth.uid() AND get_user_role() = 'Staff');

-- ============================================================================
-- ACTIVITY_LOG TABLE POLICIES
-- ============================================================================

-- Admin: Can view all activity logs
CREATE POLICY "Admin full access to activity_log"
ON activity_log
FOR ALL
TO authenticated
USING (get_user_role() = 'Admin')
WITH CHECK (get_user_role() = 'Admin');

-- Staff: Can only view their own activity logs
CREATE POLICY "Staff can view own activity"
ON activity_log
FOR SELECT
TO authenticated
USING (user_id = auth.uid() AND get_user_role() = 'Staff');

-- All authenticated users can insert activity logs
CREATE POLICY "Users can insert activity logs"
ON activity_log
FOR INSERT
TO authenticated
WITH CHECK (user_id = auth.uid());

-- ============================================================================
-- ALTERNATIVE: If NOT using Supabase Auth
-- ============================================================================
-- If you're using custom authentication (not Supabase Auth), you'll need to
-- modify the policies to use a different method of identifying the current user.
-- 
-- Option 1: Use application-level security (bypass RLS)
-- - Set a service role key in your application
-- - Handle permissions in application code
-- - Disable RLS or use simpler policies
--
-- Option 2: Use custom JWT claims
-- - Store user_id and role in JWT token
-- - Access via current_setting('request.jwt.claims')
--
-- Example for custom JWT:
/*
CREATE OR REPLACE FUNCTION get_user_role_from_jwt()
RETURNS TEXT AS $$
BEGIN
    RETURN current_setting('request.jwt.claims', true)::json->>'role';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_user_id_from_jwt()
RETURNS UUID AS $$
BEGIN
    RETURN (current_setting('request.jwt.claims', true)::json->>'user_id')::UUID;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
*/
