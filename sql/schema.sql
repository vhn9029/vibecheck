-- VibeCheck SQL Server database schema

USE VibeCheckDB;
GO

IF OBJECT_ID('dbo.journal_entries', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.journal_entries (
        id INT IDENTITY(1,1) PRIMARY KEY,
        song NVARCHAR(150) NOT NULL,
        artist NVARCHAR(150) NOT NULL,
        mood NVARCHAR(50) NOT NULL,
        note NVARCHAR(1000) NULL,
        created_at DATETIME2 NOT NULL
            DEFAULT SYSUTCDATETIME()
    );
END;
GO
