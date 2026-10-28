-- New synthetic validation data, not transcribed report data.
-- Run once after schema.sql on a fresh disposable instance.
USE ShopGadgetsOnlinePlace;
INSERT INTO Customers(CustomerID,FirstName,LastName,Email) VALUES
(1,'Synthetic','Alpha','customer1@example.invalid'),
(2,'Synthetic','Beta','customer2@example.invalid'),
(3,'Synthetic','Gamma','customer3@example.invalid');
INSERT INTO Suppliers(SupplierID,Name) VALUES
(1,'Synthetic Tech'),(2,'Synthetic Parts'),(3,'Synthetic Unused');
INSERT INTO Products(ProductID,Name,Price,StockQuantity,SupplierID) VALUES
(1,'Synthetic Widget',12.50,4,1),(2,'Synthetic Cable',10.00,10,1),
(3,'Synthetic Free Sample',0.00,0,2),(4,'Synthetic Unassigned',25.00,1,NULL);
INSERT INTO Orders(OrderID,CustomerID,OrderDate,Status) VALUES
(1,1,'2024-01-01 10:00:00','Processing'),
(2,1,'2024-01-02 10:00:00','Shipped'),
(3,2,'2024-01-03 10:00:00','Cancelled');
INSERT INTO OrderDetails(OrderDetailID,OrderID,ProductID,Quantity,Price) VALUES
(1,1,1,2,12.50),(2,1,2,1,10.00),(3,2,2,2,10.00);
INSERT INTO Employees(EmployeeID,FirstName,LastName,Email,Department,Role) VALUES
(1,'Synthetic','Staff','employee1@example.invalid','Demo','Example');
-- Passwords and phone numbers are deliberately not populated.
