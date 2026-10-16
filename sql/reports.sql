-- Mamaearth Capstone: Part 1, Task 3
-- Run against the raw seed data before Part 2 cleaning.
-- Revenue treats NULL discounts as 0%, as specified in the brief.

-- Report (a): Order totals
-- Actual query output:
--  total_orders  total_revenue  avg_order_value
--           180        99860.2           554.78
SELECT
    COUNT(*) AS total_orders,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_revenue,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ) / COUNT(*),
        2
    ) AS avg_order_value
FROM orders o
JOIN products p
    ON o.product_id = p.product_id;

-- Report (b): COUNT(*) vs COUNT(rating)
-- Actual query output:
--  total_orders  rated_orders  unrated_orders
--           180           165              15
SELECT
    COUNT(*) AS total_orders,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;

-- Report (c1): LEFT JOIN customers with zero orders
-- Actual query output:
-- customer_id   name
--        C045 Vihaan
SELECT
    c.customer_id,
    c.name
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) = 0;

-- Report (c2): NOT IN confirmation
-- Actual query output:
-- customer_id   name
--        C045 Vihaan
SELECT
    customer_id,
    name
FROM customers
WHERE customer_id NOT IN (
    SELECT DISTINCT customer_id
    FROM orders
);

-- Report (d): City return rates above 20%
-- Actual query output:
--      city  total_orders  returned_orders  return_rate_pct
--    Jaipur            19                8             42.1
--   Lucknow            49               15             30.6
-- Bangalore            33                8             24.2
SELECT
    c.city,
    COUNT(o.order_id) AS total_orders,
    SUM(o.returned) AS returned_orders,
    ROUND(
        100.0 * SUM(o.returned) / COUNT(o.order_id),
        1
    ) AS return_rate_pct
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING 100.0 * SUM(o.returned) / COUNT(o.order_id) > 20
ORDER BY return_rate_pct DESC;

-- Report (e1): Top five customers by spend
-- Actual query output:
-- customer_id    name  total_spend
--        C043 Reyansh      12920.0
--        C026    Isha       8371.6
--        C008   Meera       4564.6
--        C011   Arjun       4111.0
--        C042   Sanya       3785.0
SELECT
    c.customer_id,
    c.name,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_spend
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 5;

-- Report (e2): Ranks three to five using OFFSET
-- Actual query output:
-- customer_id  name  total_spend
--        C008 Meera       4564.6
--        C011 Arjun       4111.0
--        C042 Sanya       3785.0
SELECT
    c.customer_id,
    c.name,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_spend
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;

-- Report (f): Revenue by product category
-- Actual query output:
--     category  order_count  category_revenue
--     Haircare           54           44956.1
--     Skincare           60           27346.0
--     Babycare           30           16805.0
-- PersonalCare           36           10753.1
SELECT
    p.category,
    COUNT(o.order_id) AS order_count,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS category_revenue
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY category_revenue DESC;

-- Report (g): Customer names starting with A
-- Actual query output:
-- customer_id   name      city
--        C001  Aarav    Mumbai
--        C003  Aditi    Mumbai
--        C031 Aditya    Jaipur
--        C036  Aisha     Delhi
--        C004 Ananya   Lucknow
--        C030  Anika Bangalore
--        C044   Aria Bangalore
--        C011  Arjun Bangalore
--        C021  Aryan Bangalore
--        C041  Ayaan   Lucknow
SELECT
    customer_id,
    name,
    city
FROM customers
WHERE name LIKE 'A%'
ORDER BY name;

-- Report (h): Distinct acquisition sources
-- Actual query output:
-- acquisition_source
--                 Ad
--            Organic
--           Referral
--             Social
SELECT DISTINCT acquisition_source
FROM customers
ORDER BY acquisition_source;

-- Report (i): Add and populate customer loyalty tiers
-- Run this section once on a freshly seeded database.
ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);

UPDATE customers
SET loyalty_tier = CASE
    WHEN city_tier = 1 THEN 'Gold'
    ELSE 'Silver'
END;

-- Actual query output:
-- loyalty_tier  customer_count
--         Gold              28
--       Silver              17
SELECT
    loyalty_tier,
    COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier;
