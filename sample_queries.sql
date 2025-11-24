-- Sample Query 1: Simple SELECT with WHERE
SELECT 
    customer_id,
    first_name,
    last_name,
    email
FROM customers c
WHERE c.status = 'active';

-- Sample Query 2: JOIN with multiple conditions
SELECT 
    o.order_id,
    c.customer_name,
    p.product_name,
    o.quantity,
    o.total_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id
WHERE o.order_date >= '2024-01-01'
    AND o.status = 'completed';

-- Sample Query 3: Multiple JOINs with aliases
SELECT 
    e.employee_id,
    e.employee_name,
    d.department_name,
    m.manager_name,
    l.city,
    l.country
FROM employees e
JOIN departments d ON e.department_id = d.department_id
JOIN employees m ON e.manager_id = m.employee_id
JOIN locations l ON d.location_id = l.location_id
WHERE e.hire_date > '2020-01-01';

-- Sample Query 4: UNION query
SELECT 
    customer_id,
    customer_name,
    'Premium' as customer_type
FROM premium_customers pc
WHERE pc.subscription_status = 'active'
UNION
SELECT 
    customer_id,
    customer_name,
    'Regular' as customer_type
FROM regular_customers rc
WHERE rc.registration_date >= '2023-01-01';

-- Sample Query 5: Complex query with subquery and aggregation
SELECT 
    s.store_id,
    s.store_name,
    r.region_name,
    SUM(t.sales_amount) as total_sales,
    COUNT(t.transaction_id) as transaction_count,
    AVG(t.sales_amount) as avg_sale
FROM stores s
JOIN regions r ON s.region_id = r.region_id
JOIN transactions t ON s.store_id = t.store_id
WHERE t.transaction_date BETWEEN '2024-01-01' AND '2024-12-31'
    AND t.status = 'completed'
GROUP BY s.store_id, s.store_name, r.region_name
HAVING SUM(t.sales_amount) > 10000;

-- Sample Query 6: LEFT JOIN with multiple conditions
SELECT 
    u.user_id,
    u.username,
    p.profile_name,
    a.last_login_date
FROM users u
LEFT JOIN user_profiles p ON u.user_id = p.user_id
LEFT JOIN user_activity a ON u.user_id = a.user_id AND a.activity_type = 'login'
WHERE u.created_date >= '2023-01-01';
