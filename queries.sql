-- New/adapted portfolio examples; not exact submitted query answers.
-- Run after seed.sql in the disposable test database only.
USE ShopGadgetsOnlinePlace;

-- case: filter
-- Comparison/logical/special operators; adapted to new fixtures.
-- expect: ["1", "2"]
SELECT ProductID FROM Products WHERE Price > 0 AND Price < 30 AND (StockQuantity >= 4 OR SupplierID IN (SELECT SupplierID FROM Suppliers WHERE Name LIKE '%Tech%')) ORDER BY ProductID;

-- case: ordered_customers
-- Ascending order with deterministic ID tie-break.
-- expect: ["1", "2", "3"]
SELECT CustomerID FROM Customers ORDER BY LastName,CustomerID;

-- case: aggregates
-- COUNT, SUM, AVG, MIN and MAX over synthetic rows.
-- expect: ["3\t55.00\t11.875000\t0.00\t25.00"]
SELECT (SELECT COUNT(*) FROM Orders),(SELECT SUM(Quantity*Price) FROM OrderDetails),AVG(Price),MIN(Price),MAX(Price) FROM Products;

-- case: left_join
-- All products, including product 4 with no supplier.
-- expect: ["1\t1", "2\t1", "3\t2", "4\tNULL"]
SELECT p.ProductID,s.SupplierID FROM Products p LEFT JOIN Suppliers s ON p.SupplierID=s.SupplierID ORDER BY p.ProductID;

-- case: right_join
-- All suppliers: RIGHT JOIN preserves its right-hand Suppliers table.
-- expect: ["1\t1", "1\t2", "2\t3", "3\tNULL"]
SELECT s.SupplierID,p.ProductID FROM Products p RIGHT JOIN Suppliers s ON p.SupplierID=s.SupplierID ORDER BY s.SupplierID,p.ProductID;

-- case: inner_join
-- Orders matched to customers.
-- expect: ["1\t1", "2\t1", "3\t2"]
SELECT o.OrderID,c.CustomerID FROM Orders o INNER JOIN Customers c ON o.CustomerID=c.CustomerID ORDER BY o.OrderID;

-- case: order_totals
-- New useful aggregate; includes orders with no details.
-- expect: ["1\t35.00", "2\t20.00", "3\t0.00"]
SELECT o.OrderID,COALESCE(SUM(d.Quantity*d.Price),0) FROM Orders o LEFT JOIN OrderDetails d ON o.OrderID=d.OrderID GROUP BY o.OrderID ORDER BY o.OrderID;

-- case: update
-- New comparison/logical/special-operator update, rolled back.
-- expect: ["2\t11"]
START TRANSACTION; UPDATE Products SET StockQuantity=StockQuantity+1 WHERE Price <= 10 AND StockQuantity > 0 AND ProductID IN (2,3); SELECT ProductID,StockQuantity FROM Products WHERE ProductID=2; ROLLBACK;

-- case: delete
-- Comparison delete on unreferenced cancelled order; rolled back.
-- expect: ["1", "2"]
START TRANSACTION; DELETE FROM Orders WHERE Status='Cancelled'; SELECT OrderID FROM Orders ORDER BY OrderID; ROLLBACK;

