-- Seed Data for Text-to-SQL Clarification Engine

-- Customers
INSERT INTO customers (id, name, email, country, created_at) VALUES (1, 'Rahul Sharma', 'rahul@example.com', 'India', '2026-08-14 16:32:51.131591') ON CONFLICT (id) DO NOTHING;
INSERT INTO customers (id, name, email, country, created_at) VALUES (2, 'Raman Sharma', 'raman@example.com', 'India', '2026-08-14 16:34:40.764729') ON CONFLICT (id) DO NOTHING;
INSERT INTO customers (id, name, email, country, created_at) VALUES (3, 'Priya Singh', 'priya@example.com', 'India', '2026-08-14 16:38:55.057705') ON CONFLICT (id) DO NOTHING;
INSERT INTO customers (id, name, email, country, created_at) VALUES (4, 'John Smith', 'john@example.com', 'USA', '2026-08-14 16:38:55.057705') ON CONFLICT (id) DO NOTHING;
INSERT INTO customers (id, name, email, country, created_at) VALUES (5, 'Amit Sharma', 'amit@gmail.com', 'India', '2026-08-14 16:46:40.239539') ON CONFLICT (id) DO NOTHING;
SELECT setval('customers_id_seq', (SELECT MAX(id) FROM customers));

-- Products
INSERT INTO products (id, name, category, price, created_at) VALUES (1, 'Laptop Pro 15', 'Electronics', 85000.00, '2026-08-14 16:54:41.516220') ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, category, price, created_at) VALUES (2, 'Wireless Mouse', 'Accessories', 1500.00, '2026-08-14 16:54:41.516220') ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, category, price, created_at) VALUES (3, 'Mechanical Keyboard', 'Accessories', 4500.00, '2026-08-14 16:54:41.516220') ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, category, price, created_at) VALUES (4, '4K Monitor', 'Electronics', 32000.00, '2026-08-14 16:54:41.516220') ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, category, price, created_at) VALUES (5, 'Office Chair', 'Furniture', 18000.00, '2026-08-14 16:54:41.516220') ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, category, price, created_at) VALUES (6, 'USB-C Hub', 'Accessories', 3500.00, '2026-08-14 16:54:41.516220') ON CONFLICT (id) DO NOTHING;
SELECT setval('products_id_seq', (SELECT MAX(id) FROM products));

-- Orders
INSERT INTO orders (id, customer_id, order_date, status, total_amount) VALUES (1, 1, '2026-08-01 10:30:00', 'completed', 93500.00) ON CONFLICT (id) DO NOTHING;
INSERT INTO orders (id, customer_id, order_date, status, total_amount) VALUES (2, 1, '2026-08-05 14:15:00', 'completed', 4500.00) ON CONFLICT (id) DO NOTHING;
INSERT INTO orders (id, customer_id, order_date, status, total_amount) VALUES (3, 2, '2026-08-07 11:00:00', 'pending', 18000.00) ON CONFLICT (id) DO NOTHING;
INSERT INTO orders (id, customer_id, order_date, status, total_amount) VALUES (4, 3, '2026-08-10 16:45:00', 'completed', 32000.00) ON CONFLICT (id) DO NOTHING;
SELECT setval('orders_id_seq', (SELECT MAX(id) FROM orders));

-- Order Items
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (1, 1, 1, 1, 85000.00) ON CONFLICT (id) DO NOTHING;
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (2, 1, 2, 1, 1500.00) ON CONFLICT (id) DO NOTHING;
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (3, 2, 3, 1, 4500.00) ON CONFLICT (id) DO NOTHING;
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (4, 3, 5, 1, 18000.00) ON CONFLICT (id) DO NOTHING;
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (5, 4, 4, 1, 32000.00) ON CONFLICT (id) DO NOTHING;
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (6, 1, 6, 2, 3500.00) ON CONFLICT (id) DO NOTHING;
SELECT setval('order_items_id_seq', (SELECT MAX(id) FROM order_items));

-- Payments
INSERT INTO payments (id, order_id, payment_date, amount, status) VALUES (1, 1, '2026-08-01 10:35:00', 93500.00, 'completed') ON CONFLICT (id) DO NOTHING;
INSERT INTO payments (id, order_id, payment_date, amount, status) VALUES (2, 2, '2026-08-05 14:20:00', 4500.00, 'completed') ON CONFLICT (id) DO NOTHING;
INSERT INTO payments (id, order_id, payment_date, amount, status) VALUES (3, 3, '2026-08-07 11:05:00', 18000.00, 'pending') ON CONFLICT (id) DO NOTHING;
INSERT INTO payments (id, order_id, payment_date, amount, status) VALUES (4, 4, '2026-08-10 16:50:00', 32000.00, 'completed') ON CONFLICT (id) DO NOTHING;
SELECT setval('payments_id_seq', (SELECT MAX(id) FROM payments));
