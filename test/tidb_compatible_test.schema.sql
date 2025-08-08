-- Test Schema for TiDB Compatibility Checker
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Database with unsupported charset
CREATE DATABASE legacy_db CHARACTER SET utf8mb4;

use legacy_db;

-- Tables with various compatibility issues
CREATE TABLE products (
  id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  name2 VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  name3 VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4;

CREATE TABLE spatial_data (
  id INT(11) NOT NULL AUTO_INCREMENT,
  location GEOMETRY NOT NULL SRID 4326,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE partitioned_table (
  id INT NOT NULL,
  created_at DATETIME,
  PRIMARY KEY (id, created_at)
)
PARTITION BY RANGE (YEAR(created_at))
 (
        PARTITION p0 VALUES LESS THAN (1990),
        PARTITION p1 VALUES LESS THAN (2000),
        PARTITION p2 VALUES LESS THAN (2010),
        PARTITION p3 VALUES LESS THAN (2020),
        PARTITION p4 VALUES LESS THAN (2030),
        PARTITION pm VALUES LESS THAN MAXVALUE
);

CREATE TABLE desc_index_table (
  id INT,
  name VARCHAR(100),
  INDEX idx_name (name)  -- Descending index
);

-- Views (supported but included for completeness)
CREATE VIEW product_summary AS 
SELECT id, name FROM products;

-- Stored Procedures

-- Triggers

-- Events
ON SCHEDULE EVERY 1 DAY
DO DELETE FROM partitioned_table WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);

-- Functions

-- Tablespace (Enterprise feature)

-- Privileges
create user 'app_user'@'%';
create user 'dba'@'%';
GRANT ALL ON legacy_db.* TO 'dba'@'%';

-- Supported features (should pass)
CREATE TABLE valid_table (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  content TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_title ON valid_table (title);

SET FOREIGN_KEY_CHECKS = 1;


