-- 0. Create and Use the Gym Management Database
CREATE DATABASE IF NOT EXISTS GymManagement;
USE GymManagement;

-- 1. Trainers Table
CREATE TABLE Trainers (
    TrainerID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Experience INT NOT NULL CHECK (Experience >= 0),
    Specialization VARCHAR(100) NOT NULL,
    Gender ENUM('Male', 'Female', 'Other') NOT NULL,
    Phone CHAR(10) UNIQUE NOT NULL,
    Salary DECIMAL(10,2) NOT NULL CHECK (Salary > 0)
);

-- 2. Members Table
CREATE TABLE Members (
    MemberID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Age INT NOT NULL CHECK (Age BETWEEN 15 AND 80),
    Gender ENUM('Male', 'Female', 'Other') NOT NULL,
    Phone CHAR(10) UNIQUE NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Address TEXT,
    JoinDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    MembershipType ENUM('Monthly', 'Quarterly', 'Yearly') NOT NULL,
    TrainerID INT,
    FOREIGN KEY (TrainerID) REFERENCES Trainers(TrainerID) ON DELETE SET NULL
);

-- 3. Workout Plans Table
CREATE TABLE WorkoutPlans (
    PlanID INT AUTO_INCREMENT PRIMARY KEY,
    PlanName VARCHAR(100) NOT NULL,
    Duration INT NOT NULL CHECK (Duration > 0),
    Goal VARCHAR(100) NOT NULL,
    TrainerID INT,
    FOREIGN KEY (TrainerID) REFERENCES Trainers(TrainerID) ON DELETE SET NULL
);

-- 4. Payments Table
CREATE TABLE Payments (
    PaymentID INT AUTO_INCREMENT PRIMARY KEY,
    MemberID INT NOT NULL,
    Amount DECIMAL(10,2) NOT NULL CHECK (Amount > 0),
    Date DATETIME DEFAULT CURRENT_TIMESTAMP,
    PaymentMethod ENUM('Cash', 'Card', 'Online') NOT NULL,
    Status ENUM('Pending', 'Completed') NOT NULL,
    ServiceType ENUM('Membership', 'Class Booking', 'Personal Training', 'Other') NOT NULL,
    FOREIGN KEY (MemberID) REFERENCES Members(MemberID) ON DELETE CASCADE
);

-- 5. Attendance Table
CREATE TABLE Attendance (
    AttendanceID INT AUTO_INCREMENT PRIMARY KEY,
    MemberID INT NOT NULL,
    CheckInTime DATETIME DEFAULT CURRENT_TIMESTAMP,
    CheckOutTime DATETIME,
    FOREIGN KEY (MemberID) REFERENCES Members(MemberID) ON DELETE CASCADE,
    CHECK (CheckOutTime IS NULL OR CheckOutTime > CheckInTime)
);

-- 6. Class Bookings Table
CREATE TABLE ClassBookings (
    BookingID INT AUTO_INCREMENT PRIMARY KEY,
    MemberID INT NOT NULL,
    TrainerID INT NOT NULL,
    ClassDate DATE NOT NULL,
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,
    FOREIGN KEY (MemberID) REFERENCES Members(MemberID) ON DELETE CASCADE,
    FOREIGN KEY (TrainerID) REFERENCES Trainers(TrainerID) ON DELETE CASCADE
);

-- 7. Injury Reports Table
CREATE TABLE InjuryReports (
    InjuryID INT PRIMARY KEY AUTO_INCREMENT,
    MemberID INT NOT NULL,
    TrainerID INT,
    InjuryDate DATE NOT NULL,
    InjuryType VARCHAR(255) NOT NULL,
    Description TEXT,
    ResponsibleParty ENUM('Member', 'Trainer', 'Gym Management', 'Equipment Issue') NOT NULL,
    Resolution TEXT,
    Status ENUM('Reported', 'Under Review', 'Resolved') DEFAULT 'Reported',
    FOREIGN KEY (MemberID) REFERENCES Members(MemberID),
    FOREIGN KEY (TrainerID) REFERENCES Trainers(TrainerID)
);

-- 8. Employee Table
CREATE TABLE Employee (
    EmployeeID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Role ENUM('Staff', 'Trainer', 'Gym Faculty') NOT NULL,
    Phone CHAR(10) UNIQUE NOT NULL,
    Salary DECIMAL(10,2) NOT NULL CHECK (Salary > 0)
);

-- 9. Gym Community Table
CREATE TABLE GymCommunity (
    CommunityID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    CommunityType ENUM('Staff', 'Trainer', 'Gym Faculty', 'Member') NOT NULL,
    Contact CHAR(10) UNIQUE NOT NULL,
    EmployeeID INT,
    MemberID INT,
    ReferenceID INT,
    RecordType ENUM('Class Booking', 'Workout Plan', 'Attendance', 'Injury Report'),
    FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID) ON DELETE CASCADE,
    FOREIGN KEY (MemberID) REFERENCES Members(MemberID) ON DELETE CASCADE
);

-- ✅ Insert Data
INSERT INTO Members (Name, Age, Gender, Phone, Email, Address, MembershipType, TrainerID) VALUES
('Mike Johnson', 25, 'Male', '7654321098', 'mike@gmail.com', '123 Street, City', 'Monthly', 1),
('Sarah Lee', 30, 'Female', '6543210987', 'sarah@gmail.com', '456 Street, City', 'Yearly', 2);

-- ✅ Update GymCommunity Table
INSERT INTO GymCommunity (Name, CommunityType, Contact, EmployeeID)
SELECT Name, Role, Phone, EmployeeID FROM Employee;

INSERT INTO GymCommunity (Name, CommunityType, Contact, MemberID)
SELECT Name, 'Member', Phone, MemberID FROM Members;

-- ✅ Triggers

DELIMITER //

-- Prevent Negative Payments
CREATE TRIGGER PreventNegativePayment 
BEFORE INSERT ON Payments
FOR EACH ROW
BEGIN
    IF NEW.Amount <= 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Payment amount must be greater than zero';
    END IF;
END //

-- Prevent Negative Experience for Trainers
CREATE TRIGGER PreventNegativeExperience 
BEFORE INSERT ON Trainers
FOR EACH ROW
BEGIN
    IF NEW.Experience < 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Experience cannot be negative';
    END IF;
END //

-- Auto Assign Gym Management for Equipment Failures
CREATE TRIGGER Assign_Equipment_Issue_Responsibility
BEFORE INSERT ON InjuryReports
FOR EACH ROW
BEGIN
    IF NEW.InjuryType = 'Equipment Failure' THEN
        SET NEW.ResponsibleParty = 'Gym Management';
    END IF;
END //

DELIMITER ;

-- ✅ Procedure

DELIMITER //
CREATE PROCEDURE UpdatePaymentStatus()
BEGIN
    UPDATE Payments 
    SET Status = 'Pending' 
    WHERE Date < CURDATE() AND Status = 'Completed';
END //
DELIMITER ;

-- ✅ Report Queries

-- 1. All members with trainer names
SELECT M.MemberID, M.Name AS MemberName, T.Name AS TrainerName
FROM Members M
LEFT JOIN Trainers T ON M.TrainerID = T.TrainerID;

-- 2. Members with pending payments
SELECT M.MemberID, M.Name, P.Amount, P.Status
FROM Members M
JOIN Payments P ON M.MemberID = P.MemberID
WHERE P.Status = 'Pending';

-- 3. Count members per membership type
SELECT MembershipType, COUNT(*) AS TotalMembers
FROM Members
GROUP BY MembershipType;

-- 4. Most booked trainers
SELECT T.TrainerID, T.Name AS TrainerName, COUNT(C.BookingID) AS TotalBookings
FROM Trainers T
JOIN ClassBookings C ON T.TrainerID = C.TrainerID
GROUP BY T.TrainerID, T.Name
ORDER BY TotalBookings DESC;

-- 5. Attendance for specific member
SELECT A.MemberID, M.Name, A.CheckInTime, A.CheckOutTime
FROM Attendance A
JOIN Members M ON A.MemberID = M.MemberID
WHERE M.Name = 'Mike Johnson';

-- 6. View all Employees
SELECT * FROM Employee;

-- 7. View all GymCommunity
SELECT * FROM GymCommunity;
