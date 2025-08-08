-- Test Schema for TiDB Compatibility Checker
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Database with unsupported charset
CREATE DATABASE legacy_db CHARACTER SET ucs2;

use legacy_db;

-- Tables with various compatibility issues
CREATE TABLE products (
  id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) CHARACTER SET latin2 COLLATE latin2_bin NOT NULL,
  name2 VARCHAR(255) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  name3 VARCHAR(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FULLTEXT KEY ft_idx (description)  -- Fulltext index
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8;

CREATE TABLE spatial_data (
  id INT(11) NOT NULL AUTO_INCREMENT,
  location GEOMETRY NOT NULL SRID 4326,
  SPATIAL INDEX sp_idx (location),  -- Spatial index
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE partitioned_table (
  id INT NOT NULL,
  created_at DATETIME,
  PRIMARY KEY (id, created_at)
)
PARTITION BY RANGE (YEAR(created_at))
SUBPARTITION BY HASH( TO_DAYS(created_at) )
SUBPARTITIONS 2 (
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
  INDEX idx_name (name DESC)  -- Descending index
);

-- Views (supported but included for completeness)
CREATE VIEW product_summary AS 
SELECT id, name FROM products;

-- Stored Procedures
DELIMITER ;;
CREATE PROCEDURE get_product(IN pid INT)
BEGIN
  SELECT * FROM products WHERE id = pid;
END;;
DELIMITER ;

-- Triggers
DELIMITER ;;
CREATE TRIGGER before_product_insert 
BEFORE INSERT ON products 
FOR EACH ROW 
SET NEW.created_at = NOW();;
DELIMITER ;

-- Events
CREATE EVENT cleanup_old_data
ON SCHEDULE EVERY 1 DAY
DO DELETE FROM partitioned_table WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);

-- Functions
DELIMITER ;;
CREATE FUNCTION calculate_tax(price DECIMAL(10,2)) 
RETURNS DECIMAL(10,2) DETERMINISTIC
BEGIN
  RETURN price * 0.1;
END;;
DELIMITER ;

-- Tablespace (Enterprise feature)
CREATE TABLESPACE legacy_ts ADD DATAFILE 'legacy_data.ibd' ENGINE=InnoDB;

-- Privileges
create user 'app_user'@'%';
create user 'dba'@'%';
GRANT SELECT (id, name), UPDATE (description) ON legacy_db.products TO 'app_user'@'%';
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


