-- ===========================================
-- WOPLA DATABASE SETUP - SQL SERVER 2022
-- ===========================================

-- 1. CREATE DATABASE
USE master;
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = N'WoplaDB')
BEGIN
    ALTER DATABASE WoplaDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE WoplaDB;
    PRINT 'Existing WoplaDB dropped.';
END
GO

CREATE DATABASE WoplaDB;
GO

USE WoplaDB;
GO

-- 2. CREATE TABLES

-- Users Table
CREATE TABLE Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    Email NVARCHAR(120) UNIQUE NOT NULL,
    PasswordHash NVARCHAR(256) NOT NULL,
    FirstName NVARCHAR(50) NOT NULL,
    LastName NVARCHAR(50) NOT NULL,
    Role NVARCHAR(50) NOT NULL CHECK (Role IN ('super_admin', 'client_admin', 'employee')),
    CompanyID INT NULL,
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE()
);
GO

-- Companies Table
CREATE TABLE Companies (
    CompanyID INT IDENTITY(1,1) PRIMARY KEY,
    CompanyName NVARCHAR(200) UNIQUE NOT NULL,
    CompanyEmail NVARCHAR(120) UNIQUE NOT NULL,
    Status NVARCHAR(20) DEFAULT 'Active',
    CreatedAt DATETIME2 DEFAULT GETDATE()
);
GO

-- Vendors Table
CREATE TABLE Vendors (
    VendorID INT IDENTITY(1,1) PRIMARY KEY,
    VendorName NVARCHAR(200) UNIQUE NOT NULL,
    ContactEmail NVARCHAR(120) NOT NULL,
    Status NVARCHAR(20) DEFAULT 'Active',
    CreatedAt DATETIME2 DEFAULT GETDATE()
);
GO

-- Dishes Table
CREATE TABLE Dishes (
    DishID INT IDENTITY(1,1) PRIMARY KEY,
    DishName NVARCHAR(200) NOT NULL,
    VendorID INT NOT NULL,
    CompanyID INT NULL,
    Price DECIMAL(10,2) NOT NULL,
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (VendorID) REFERENCES Vendors(VendorID)
);
GO

-- Orders Table
CREATE TABLE Orders (
    OrderID INT IDENTITY(1,1) PRIMARY KEY,
    CompanyID INT NOT NULL,
    EmployeeID INT NULL,
    DishID INT NOT NULL,
    OrderDate DATE NOT NULL,
    Notes NVARCHAR(500) NULL,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (CompanyID) REFERENCES Companies(CompanyID),
    FOREIGN KEY (DishID) REFERENCES Dishes(DishID)
);
GO

-- KioskCounters Table (for lunch_kiosk.html)
CREATE TABLE KioskCounters (
    CounterID INT IDENTITY(1,1) PRIMARY KEY,
    DishID INT NOT NULL,
    CounterDate DATE NOT NULL,
    BaseCount INT DEFAULT 0,
    AdditionalCount INT DEFAULT 0,
    LastUpdated DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (DishID) REFERENCES Dishes(DishID)
);
GO

-- 3. INSERT DEFAULT DATA

-- Super Admin
INSERT INTO Users (Email, PasswordHash, FirstName, LastName, Role, IsActive) 
VALUES ('admin@wopla.com', 'Admin@123', 'Super', 'Admin', 'super_admin', 1);
GO

-- Sample Companies
INSERT INTO Companies (CompanyName, CompanyEmail, Status) VALUES
('Alpha Corp', 'alpha@corp.com', 'Active'),
('Beta Solutions', 'beta@corp.com', 'Active');
GO

-- Sample Vendors
INSERT INTO Vendors (VendorName, ContactEmail, Status) VALUES
('Karachi Kitchen', 'kk@contact.com', 'Active'),
('Punjab Dhaba', 'punjab@dhaba.com', 'Active');
GO

-- Sample Dishes
INSERT INTO Dishes (DishName, VendorID, CompanyID, Price, IsActive) VALUES
('Chicken Biryani', 1, 1, 12.99, 1),
('Mutton Karahi', 1, 2, 15.99, 1),
('Paneer Tikka', 2, 1, 8.99, 1),
('Butter Chicken', 2, 2, 13.99, 1);
GO

-- Sample Users
DECLARE @AlphaID INT = (SELECT CompanyID FROM Companies WHERE CompanyName = 'Alpha Corp');
DECLARE @BetaID INT = (SELECT CompanyID FROM Companies WHERE CompanyName = 'Beta Solutions');

INSERT INTO Users (Email, PasswordHash, FirstName, LastName, Role, CompanyID, IsActive) VALUES
('ali@alpha.com', 'Welcome@123', 'Ali', 'Khan', 'client_admin', @AlphaID, 1),
('sarah@alpha.com', 'Welcome@123', 'Sarah', 'Ahmed', 'employee', @AlphaID, 1),
('fatima@beta.com', 'Welcome@123', 'Fatima', 'Zafar', 'client_admin', @BetaID, 1);
GO

-- Sample Kiosk Counters
INSERT INTO KioskCounters (DishID, CounterDate, BaseCount) VALUES
(1, CAST(GETDATE() AS DATE), 45),
(2, CAST(GETDATE() AS DATE), 22),
(3, CAST(GETDATE() AS DATE), 38);
GO

-- 4. CREATE STORED PROCEDURES

-- Get Dashboard Stats
CREATE PROCEDURE sp_GetDashboardStats
AS
BEGIN
    SELECT 
        (SELECT COUNT(*) FROM Companies WHERE Status = 'Active') AS TotalCompanies,
        (SELECT COUNT(*) FROM Users WHERE Role = 'client_admin') AS TotalClientAdmins,
        (SELECT COUNT(*) FROM Orders WHERE OrderDate = CAST(GETDATE() AS DATE)) AS TodaysOrders,
        (SELECT COUNT(*) FROM Vendors WHERE Status = 'Active') AS ActiveVendors;
END;
GO

-- Create Order
CREATE PROCEDURE sp_CreateOrder
    @CompanyID INT,
    @EmployeeID INT,
    @DishID INT,
    @OrderDate DATE,
    @Notes NVARCHAR(500) = NULL
AS
BEGIN
    INSERT INTO Orders (CompanyID, EmployeeID, DishID, OrderDate, Notes)
    VALUES (@CompanyID, @EmployeeID, @DishID, @OrderDate, @Notes);
    
    SELECT 'success' AS Status, SCOPE_IDENTITY() AS OrderID;
END;
GO

-- Get Available Dishes
CREATE PROCEDURE sp_GetAvailableDishes
    @CompanyID INT = NULL
AS
BEGIN
    SELECT 
        d.DishID,
        d.DishName,
        v.VendorName,
        d.Price,
        d.IsActive
    FROM Dishes d
    JOIN Vendors v ON d.VendorID = v.VendorID
    WHERE d.IsActive = 1 
        AND (d.CompanyID = @CompanyID OR d.CompanyID IS NULL)
        AND v.Status = 'Active';
END;
GO

-- Update Kiosk Counter
CREATE PROCEDURE sp_UpdateKioskCounter
    @DishID INT,
    @Change INT
AS
BEGIN
    DECLARE @Today DATE = CAST(GETDATE() AS DATE);
    
    IF NOT EXISTS (SELECT 1 FROM KioskCounters WHERE DishID = @DishID AND CounterDate = @Today)
    BEGIN
        INSERT INTO KioskCounters (DishID, CounterDate, BaseCount)
        VALUES (@DishID, @Today, 0);
    END
    
    UPDATE KioskCounters
    SET AdditionalCount = AdditionalCount + @Change
    WHERE DishID = @DishID AND CounterDate = @Today;
    
    SELECT 'success' AS Status;
END;
GO

-- 5. CREATE SIMPLE VIEWS

-- View for Dashboard
CREATE VIEW vw_Dashboard AS
SELECT 
    (SELECT COUNT(*) FROM Companies) AS TotalCompanies,
    (SELECT COUNT(*) FROM Users WHERE Role = 'client_admin') AS TotalAdmins,
    (SELECT COUNT(*) FROM Orders WHERE OrderDate = CAST(GETDATE() AS DATE)) AS TodaysOrders,
    (SELECT COUNT(*) FROM Vendors) AS TotalVendors;
GO

-- View for Orders
CREATE VIEW vw_Orders AS
SELECT 
    o.OrderID,
    c.CompanyName,
    u.FirstName + ' ' + u.LastName AS EmployeeName,
    d.DishName,
    v.VendorName,
    o.OrderDate,
    o.Notes
FROM Orders o
JOIN Companies c ON o.CompanyID = c.CompanyID
LEFT JOIN Users u ON o.EmployeeID = u.UserID
JOIN Dishes d ON o.DishID = d.DishID
JOIN Vendors v ON d.VendorID = v.VendorID;
GO

-- 6. VERIFICATION AND TEST
PRINT '=== DATABASE CREATION COMPLETE ===';
PRINT '';

-- Show table counts
SELECT 'Users' AS Table_Name, COUNT(*) AS Records FROM Users
UNION ALL
SELECT 'Companies', COUNT(*) FROM Companies
UNION ALL
SELECT 'Vendors', COUNT(*) FROM Vendors
UNION ALL
SELECT 'Dishes', COUNT(*) FROM Dishes
UNION ALL
SELECT 'Orders', COUNT(*) FROM Orders
UNION ALL
SELECT 'KioskCounters', COUNT(*) FROM KioskCounters;
GO

PRINT '';
PRINT '=== TEST STORED PROCEDURES ===';

-- Test Dashboard Stats
EXEC sp_GetDashboardStats;
GO

-- Test Get Available Dishes
EXEC sp_GetAvailableDishes @CompanyID = 1;
GO

PRINT '';
PRINT '=== TEST VIEWS ===';
SELECT * FROM vw_Dashboard;
SELECT TOP 5 * FROM vw_Orders ORDER BY OrderDate DESC;
GO

PRINT '';
PRINT '========================================';
PRINT 'WOPLA DATABASE SETUP SUCCESSFUL!';
PRINT '========================================';
PRINT 'Database: WoplaDB';
PRINT 'Super Admin: admin@wopla.com / Admin@123';
PRINT '========================================';
GO