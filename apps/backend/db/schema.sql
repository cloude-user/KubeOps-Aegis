-- ============================================================
-- Aegis Commerce: Enterprise PostgreSQL Database Schema & Seeding
-- Managed Azure Database for PostgreSQL Flexible Server
-- ============================================================

-- 1. Users Table (Supports Local Auth & Microsoft Entra ID)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entra_oid VARCHAR(255) UNIQUE, -- Microsoft Entra ID Object ID (OIDC)
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'customer', -- customer, sre_admin, cloud_architect
    avatar_blob_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Product Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),nsg
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Products Catalog Table
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 100,
    image_blob_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Customer Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, PAID, SHIPPED, DELIVERED, CANCELLED
    receipt_blob_url TEXT,
    shipping_address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT,
    quantity INT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);

-- 6. Audit Logs Table (For SRE Event Auditing)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SEED DATA (Enterprise Pre-populated Dataset)
-- ============================================================

-- Seed Users (Demo Admin & Demo Customer)
INSERT INTO users (id, entra_oid, email, password_hash, full_name, role, avatar_blob_url) VALUES
    ('11111111-1111-1111-1111-111111111111', 'entra-oid-admin-001', 'sre-admin@aegiscloud.onmicrosoft.com', '$2b$12$eImiTXuWVxfM37uY4JANjOL.sZnq7fB1/86V./1d0d', 'SRE Lead Architect', 'sre_admin', 'https://kubeopsaegisstprd.blob.core.windows.net/user-media/avatars/admin.png'),
    ('22222222-2222-2222-2222-222222222222', 'entra-oid-user-002', 'customer@aegiscloud.onmicrosoft.com', '$2b$12$eImiTXuWVxfM37uY4JANjOL.sZnq7fB1/86V./1d0d', 'Jane Cloud Engineer', 'customer', 'https://kubeopsaegisstprd.blob.core.windows.net/user-media/avatars/customer.png')
ON CONFLICT (email) DO NOTHING;

-- Seed Product Categories
INSERT INTO categories (id, name, description) VALUES
    ('c1111111-1111-1111-1111-111111111111', 'Cloud & DevOps', 'Azure, Kubernetes, Terraform & CI/CD Books & Tools'),
    ('c2222222-2222-2222-2222-222222222222', 'Hardware & IoT', 'Raspberry Pi, Cloud Gateways & Edge Nodes'),
    ('c3333333-3333-3333-3333-333333333333', 'Developer Gear', 'Mechanical Keyboards, Noise Cancelling Headphones')
ON CONFLICT (name) DO NOTHING;

-- Seed Products Catalog
INSERT INTO products (id, category_id, title, description, price, stock_quantity, image_blob_url) VALUES
    ('b1111111-1111-1111-1111-111111111111', 'c1111111-1111-1111-1111-111111111111', 'Azure AKS Masterclass Handbook', 'Complete guide to building resilient Kubernetes on Azure', 49.99, 150, 'https://kubeopsaegisstprd.blob.core.windows.net/user-media/products/aks-guide.png'),
    ('b2222222-2222-2222-2222-222222222222', 'c1111111-1111-1111-1111-111111111111', 'Terraform Enterprise IaC Guide', 'Production-grade Terraform modules & state management', 59.99, 200, 'https://kubeopsaegisstprd.blob.core.windows.net/user-media/products/terraform-guide.png'),
    ('b3333333-3333-3333-3333-333333333333', 'c1111111-1111-1111-1111-111111111111', 'Autonomous SRE AI Agent Toolkit', 'LangGraph & Prometheus self-healing agent framework', 89.99, 75, 'https://kubeopsaegisstprd.blob.core.windows.net/user-media/products/sre-agent.png'),
    ('b4444444-4444-4444-4444-444444444444', 'c3333333-3333-3333-3333-333333333333', 'Mechanical Kubernetes Keycaps', 'Custom CNC aluminum Keycaps with K8s logos', 29.99, 500, 'https://kubeopsaegisstprd.blob.core.windows.net/user-media/products/keycaps.png')
ON CONFLICT (id) DO NOTHING;

-- Seed Sample Orders
INSERT INTO orders (id, user_id, total_amount, status, receipt_blob_url, shipping_address) VALUES
    ('d1111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 109.98, 'PAID', 'https://kubeopsaegisstprd.blob.core.windows.net/order-receipts/receipt_o1111111.pdf', '100 Azure Way, Seattle, WA')
ON CONFLICT (id) DO NOTHING;

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    ('d1111111-1111-1111-1111-111111111111', 'b1111111-1111-1111-1111-111111111111', 1, 49.99),
    ('d1111111-1111-1111-1111-111111111111', 'b2222222-2222-2222-2222-222222222222', 1, 59.99)
ON CONFLICT (id) DO NOTHING;
