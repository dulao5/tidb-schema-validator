# TiDB Schema Validator

TiDB Schema Validator is an open-source tool that analyzes MySQL schema definitions (from mysqldump) for compatibility issues before migrating to TiDB. It detects unsupported features like stored procedures, triggers, special indexes, and character sets, providing actionable warnings and automatic fixes. Simplify your database migration with comprehensive schema validation and transformation capabilities.

Key features:

* ✅ Detects 10+ TiDB-incompatible MySQL features
* 🔧 Auto-fix option for schema modification
* 📋 Detailed line-by-line compatibility report
* 🚀 Streamlines MySQL-to-TiDB migration

Perfect for DBAs and developers preparing databases for TiDB deployment.


## Usage

```bash
python mysql-schema-checker.py <input_schema.sql> [--apply]

Without --apply: Outputs incompatible SQL line numbers with warnings

With --apply: Generates modified output_schema.sql
```

## Detectable Features in Schema SQL


| Incompatibility                  | Sample                                                                 |
|----------------------------------|------------------------------------------------------------------------|
| Stored Procedures and Functions  | `CREATE PROCEDURE simpleproc() BEGIN SELECT * FROM t; END;`            |
| Triggers                         | `CREATE TRIGGER ins_bef BEFORE INSERT ON t FOR EACH ROW SET NEW.x=1;`  |
| Events                           | `CREATE EVENT myevent ON SCHEDULE EVERY 1 HOUR DO DELETE FROM t;`      |
| User-Defined Functions           | `CREATE FUNCTION myfunc() RETURNS INT DETERMINISTIC RETURN 1;`         |
| Full-Text Indexes                | `CREATE TABLE t (txt TEXT, FULLTEXT idx(txt)) ENGINE=InnoDB;`          |
| Spatial Types/Indexes            | `CREATE TABLE t (g GEOMETRY NOT NULL SRID 4326, SPATIAL INDEX(g));`    |
| Unsupported Character Sets       | `CREATE TABLE t (a VARCHAR(10) CHARACTER SET ucs2);`                   |
| Column-Level Privileges          | `GRANT SELECT(c1), UPDATE(c2) ON db.t TO user@host;`                   |
| CREATE TABLESPACE                | `CREATE TABLESPACE ts ADD DATAFILE 'ts.ibd' ENGINE=InnoDB;`            |
| Descending Indexes               | `CREATE TABLE t (a INT, b INT, INDEX idx(a DESC, b ASC));`             |
| Subpartitioning                  | `CREATE TABLE t (id INT) PARTITION BY RANGE(id) SUBPARTITION BY HASH(id)|
| Auto-increment Behavior Notice   | `CREATE TABLE t (id INT PRIMARY KEY AUTO_INCREMENT);`                  |


## Sample
```
python mysql-schema-checker.py test.schema.sql --apply
# output some warnings
# output fix file to tidb_compatible_test.schema.sql
```
diff test.schema.sql vs tidb_compatible_test.schema.sql

<img width="1506" alt="Image" src="https://github.com/user-attachments/assets/9b2d226d-ad7f-4bc9-a86e-6d63af8918a3" />

## Runtime Features (Require Manual Verification)
These features cannot be detected in schema dumps and require application-level checks:


| Incompatibility                  | Sample                                                                 |
|----------------------------------|------------------------------------------------------------------------|
| MySQL Trace Optimizer            | _(Runtime feature, no schema representation)_                          |
| XML Functions                    | _(Runtime feature, no schema representation)_                          |
| X-Protocol                       | _(Connection protocol, no schema representation)_                      |
| XA Syntax                        | _(Runtime transaction control, no schema representation)_              |
| CREATE TABLE AS SELECT           | _(Runtime DDL, schema shows table structure without CTAS origin)_      |
| CHECK TABLE                      | _(Runtime maintenance command)_                                        |
| CHECKSUM TABLE                   | _(Runtime verification command)_                                       |
| REPAIR TABLE                     | _(Runtime maintenance command)_                                        |
| OPTIMIZE TABLE                   | _(Runtime maintenance command)_                                        |
| HANDLER Statement                | _(Runtime low-level table access)_                                     |
| Session Tracker (GTID in OK)     | _(Protocol-level feature, no schema representation)_                   |
| SKIP LOCKED                      | _(Runtime locking clause, e.g. SELECT ... FOR UPDATE SKIP LOCKED)_     |
| Lateral Derived Tables           | _(Runtime query syntax, e.g. SELECT ... FROM t1, LATERAL (...))_       |
| Subquery in JOIN ON Clause       | `SELECT ... FROM t1 JOIN t2 ON t1.id = (SELECT id FROM t3 WHERE ...)`  |

Please see [the document](https://docs.pingcap.com/tidb/stable/mysql-compatibility/)
