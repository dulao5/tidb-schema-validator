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
python tidb-schema-checker.py <input_schema.sql> [--apply]

Without --apply: Outputs incompatible SQL line numbers with warnings

With --apply: modify input_schema.sql in place
```

## Detectable Features in Schema SQL


| Incompatibility                    | Sample                                                                 | action                   |
|------------------------------------|------------------------------------------------------------------------|--------------------------|
| Stored Procedures and Functions    | `CREATE PROCEDURE simpleproc() BEGIN SELECT * FROM t; END;`            | remove                   |
| Triggers                           | `CREATE TRIGGER ins_bef BEFORE INSERT ON t FOR EACH ROW SET NEW.x=1;`  | remove                   |
| Events                             | `CREATE EVENT myevent ON SCHEDULE EVERY 1 HOUR DO DELETE FROM t;`      | remove                   |
| User-Defined Functions             | `CREATE FUNCTION myfunc() RETURNS INT DETERMINISTIC RETURN 1;`         | remove                   |
| Full-Text Indexes                  | `CREATE TABLE t (txt TEXT, FULLTEXT idx(txt)) ENGINE=InnoDB;`          | remove                   |
| Spatial Types/Indexes              | `CREATE TABLE t (g GEOMETRY NOT NULL SRID 4326, SPATIAL INDEX(g));`    | remove                   |
| Unsupported Character Sets         | `CREATE TABLE t (a VARCHAR(10) CHARACTER SET ucs2);`                   | force_replace_to_utf8mb4 |
| Column-Level Privileges            | `GRANT SELECT(c1), UPDATE(c2) ON db.t TO user@host;`                   | remove                   |
| CREATE TABLESPACE                  | `CREATE TABLESPACE ts ADD DATAFILE 'ts.ibd' ENGINE=InnoDB;`            | remove                   |
| Descending Indexes                 | `CREATE TABLE t (a INT, b INT, INDEX idx(a DESC, b ASC));`             | remove `desc`            |
| Subpartitioning                    | `CREATE TABLE t (id INT) PARTITION BY RANGE(id) SUBPARTITION BY HASH(id)`|remove `SUBPARTITION`   |
| Auto-increment Behavior Notice     | `CREATE TABLE t (id INT PRIMARY KEY AUTO_INCREMENT);`                  | warning                  |
| Auto-increment BigintType          | `id int(10) NOT NULL AUTO_INCREMENT`                                   | warning                  |
| Table without PRIMARY or UNIQUE KEY| `CREATE TABLE t (val INT );`                                           | warning                  |


## Sample
```
python tidb-schema-checker.py test.schema.sql
# output some warnings

python tidb-schema-checker.py test.schema.sql --apply
# output some warnings
# modify test.schema.sql in place 
```
diff test.schema.sql before vs after(applied)

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
