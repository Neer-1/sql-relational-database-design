"""Synthetic tests on a NEW private Windows MySQL instance; never connects to an existing server."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mysql-bin', type=Path, required=True, help='Existing trusted MySQL 8.0 bin directory')
    parser.add_argument('--work-dir', type=Path, required=True, help='Existing disposable output parent outside repository')
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('This isolated shared-memory runner is validated on Windows only.')
    source = Path(__file__).resolve().parent
    parent = args.work_dir.resolve(strict=True)
    if parent == source or source in parent.parents:
        parser.error('Output must be outside the publication repository.')
    binaries = args.mysql_bin.resolve(strict=True)
    for name in ['mysqld.exe', 'mysql.exe']:
        if not (binaries / name).is_file():
            parser.error('Missing MySQL binary: ' + name)
    work = Path(tempfile.mkdtemp(prefix='a06-mysql-', dir=parent))
    data = work / 'data'
    channel = 'A06_' + uuid.uuid4().hex
    env = os.environ.copy()
    env.pop('MYSQL_PWD', None)
    env['MYSQL_TEST_LOGIN_FILE'] = str(work / 'unused-login.cnf')
    flags = subprocess.CREATE_NO_WINDOW
    results = []
    server = None
    report = {'status': 'RUNNING', 'results': results, 'run_directory': str(work)}

    def call(command, **kwargs):
        return subprocess.run([str(x) for x in command], capture_output=True, text=True,
                              timeout=90, creationflags=flags, env=env, **kwargs)

    client = [binaries / 'mysql.exe', '--no-defaults', '--password=', '--protocol=MEMORY',
              '--shared-memory-base-name=' + channel, '--user=root', '--batch',
              '--skip-column-names', '--default-character-set=utf8mb4']

    def check(label, sql, expected=None, error=None, database=True):
        prefix = "SET SESSION sql_mode='STRICT_ALL_TABLES,NO_ENGINE_SUBSTITUTION'; "
        if database:
            prefix += 'USE ShopGadgetsOnlinePlace; '
        proc = call(client + ['--execute', prefix + sql])
        ok = proc.returncode == 0 if error is None else proc.returncode != 0 and ('ERROR ' + str(error)) in proc.stderr
        if expected is not None:
            ok = ok and proc.stdout.strip().splitlines() == expected
        results.append(dict(label=label, passed=ok, expected=expected, expected_error=error,
                            stdout=proc.stdout, stderr=proc.stderr))
        if not ok:
            raise AssertionError(label + ': ' + proc.stdout + proc.stderr)
        return proc.stdout.strip()

    try:
        init = call([binaries / 'mysqld.exe', '--no-defaults', '--initialize-insecure',
                     '--basedir=' + str(binaries.parent), '--datadir=' + str(data), '--mysqlx=0'])
        (work / 'initialize.log').write_text(init.stdout + init.stderr, encoding='utf-8')
        if init.returncode:
            raise RuntimeError('Initialization failed; inspect initialize.log')
        server = subprocess.Popen([str(binaries / 'mysqld.exe'), '--no-defaults', '--standalone',
            '--basedir=' + str(binaries.parent), '--datadir=' + str(data), '--skip-networking',
            '--mysqlx=0', '--shared-memory', '--shared-memory-base-name=' + channel,
            '--skip-log-bin', '--innodb-buffer-pool-size=32M', '--default-storage-engine=InnoDB',
            '--character-set-server=utf8mb4', '--collation-server=utf8mb4_0900_ai_ci',
            '--log-error=' + str(work / 'server.log'), '--pid-file=' + str(work / 'server.pid')],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags, env=env)
        for _ in range(60):
            if server.poll() is not None:
                raise RuntimeError('Private server exited during startup')
            if call(client + ['--execute', 'SELECT 1']).returncode == 0:
                break
            time.sleep(.5)
        else:
            raise TimeoutError('Private server startup timed out')
        check('TCP disabled', 'SELECT @@skip_networking', ['1'], database=False)
        report['mysql_version'] = check('version', 'SELECT VERSION()', database=False)
        report['datadir'] = check('private datadir', 'SELECT @@datadir', database=False)
        if Path(report['datadir']).resolve() != data.resolve():
            raise AssertionError('Unexpected datadir')
        schema = (source / 'schema.sql').read_text(encoding='utf-8-sig')
        seed = (source / 'seed.sql').read_text(encoding='utf-8-sig')
        check('fresh schema', schema, database=False)
        check('six tables', "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()", ['6'])
        check('six primary keys', "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema=DATABASE() AND constraint_type='PRIMARY KEY'", ['6'])
        check('four foreign keys', "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema=DATABASE() AND constraint_type='FOREIGN KEY'", ['4'])
        check('two unique constraints', "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema=DATABASE() AND constraint_type='UNIQUE'", ['2'])
        check('no check constraints', "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema=DATABASE() AND constraint_type='CHECK'", ['0'])
        check('25 nullable non-key columns', "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND is_nullable='YES'", ['25'])
        check('six InnoDB tables', "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND engine='InnoDB'", ['6'])
        report['columns'] = check('column metadata', "SELECT table_name,column_name,column_type,is_nullable,column_key,extra FROM information_schema.columns WHERE table_schema=DATABASE() ORDER BY table_name,ordinal_position")
        report['referential_actions'] = check('referential actions', "SELECT table_name,referenced_table_name,update_rule,delete_rule FROM information_schema.referential_constraints WHERE constraint_schema=DATABASE() ORDER BY table_name,referenced_table_name")
        check('valid related seed', seed)
        check('six seed counts', 'SELECT (SELECT COUNT(*) FROM Customers),(SELECT COUNT(*) FROM Suppliers),(SELECT COUNT(*) FROM Products),(SELECT COUNT(*) FROM Orders),(SELECT COUNT(*) FROM OrderDetails),(SELECT COUNT(*) FROM Employees)', ['3\t3\t4\t3\t3\t1'])
        check('schema repeat refuses existing database', schema, error=1007, database=False)
        check('seed repeat rejects duplicate key', seed, error=1062)
        for table, pk in [('Customers','CustomerID'),('Suppliers','SupplierID'),('Products','ProductID'),('Orders','OrderID'),('OrderDetails','OrderDetailID'),('Employees','EmployeeID')]:
            check('duplicate primary key ' + table, f'INSERT INTO {table}({pk}) VALUES(1)', error=1062)
        for table, value in [('Customers','customer1@example.invalid'),('Employees','employee1@example.invalid')]:
            check('duplicate email ' + table, f"INSERT INTO {table}(Email) VALUES('{value}')", error=1062)
            check('case-insensitive email ' + table, f"INSERT INTO {table}(Email) VALUES('{value.upper()}')", error=1062)
            check('multiple NULL emails ' + table, f'START TRANSACTION; INSERT INTO {table}(Email) VALUES(NULL),(NULL); SELECT COUNT(*) FROM {table} WHERE Email IS NULL; ROLLBACK;', ['2'])
        edges=[('Products','SupplierID','Suppliers','SupplierID'),('Orders','CustomerID','Customers','CustomerID'),('OrderDetails','OrderID','Orders','OrderID'),('OrderDetails','ProductID','Products','ProductID')]
        for child, column, parent_table, pk in edges:
            check('invalid FK '+child+'.'+column, f'INSERT INTO {child}({column}) VALUES(999)', error=1452)
            check('invalid FK update '+child+'.'+column, f'UPDATE {child} SET {column}=999 WHERE {column}=1', error=1452)
            check('referenced parent delete '+child+'.'+column, f'DELETE FROM {parent_table} WHERE {pk}=1', error=1451)
            check('referenced parent update '+child+'.'+column, f'UPDATE {parent_table} SET {pk}=999 WHERE {pk}=1', error=1451)
        check('all nullable relationships accepted', 'START TRANSACTION; INSERT INTO Products(ProductID,SupplierID) VALUES(80,NULL); INSERT INTO Orders(OrderID,CustomerID) VALUES(80,NULL); INSERT INTO OrderDetails(OrderDetailID,OrderID,ProductID) VALUES(80,NULL,NULL); SELECT (SELECT SupplierID IS NULL FROM Products WHERE ProductID=80),(SELECT CustomerID IS NULL FROM Orders WHERE OrderID=80),(SELECT OrderID IS NULL AND ProductID IS NULL FROM OrderDetails WHERE OrderDetailID=80); ROLLBACK;', ['1\t1\t1'])
        check('omitted OrderID accepted', 'START TRANSACTION; INSERT INTO OrderDetails(OrderDetailID,ProductID) VALUES(80,1); SELECT OrderID IS NULL FROM OrderDetails WHERE OrderDetailID=80; ROLLBACK;', ['1'])
        check('negative price stock quantity accepted', 'START TRANSACTION; INSERT INTO Products(ProductID,Price,StockQuantity) VALUES(80,-1,-1); INSERT INTO OrderDetails(OrderDetailID,Price,Quantity) VALUES(80,-1,-1); SELECT (SELECT Price FROM Products WHERE ProductID=80),(SELECT StockQuantity FROM Products WHERE ProductID=80),(SELECT Quantity FROM OrderDetails WHERE OrderDetailID=80),(SELECT Price FROM OrderDetails WHERE OrderDetailID=80); ROLLBACK;', ['-1.00\t-1\t-1\t-1.00'])
        check('zero boundary values accepted', 'START TRANSACTION; INSERT INTO OrderDetails(OrderDetailID,Price,Quantity) VALUES(80,0,0); SELECT Price,Quantity FROM OrderDetails WHERE OrderDetailID=80; ROLLBACK;', ['0.00\t0'])
        check('decimal and integer limits', 'START TRANSACTION; INSERT INTO Products(ProductID,Price,StockQuantity) VALUES(80,99999999.99,2147483647),(81,-99999999.99,-2147483648); SELECT Price,StockQuantity FROM Products WHERE ProductID>=80 ORDER BY ProductID; ROLLBACK;', ['99999999.99\t2147483647','-99999999.99\t-2147483648'])
        check('decimal overflow rejected', 'INSERT INTO Products(Price) VALUES(100000000)', error=1264)
        check('integer overflow rejected', 'INSERT INTO Products(StockQuantity) VALUES(2147483648)', error=1264)
        check('varchar overflow rejected', "INSERT INTO Suppliers(Name) VALUES(REPEAT('x',256))", error=1406)
        check('decimal fractional rounding', 'START TRANSACTION; INSERT INTO Products(ProductID,Price) VALUES(80,1.235); SELECT Price FROM Products WHERE ProductID=80; ROLLBACK;', ['1.24'])
        check('duplicate order-product pair accepted', 'START TRANSACTION; INSERT INTO OrderDetails(OrderID,ProductID,Quantity,Price) VALUES(1,1,1,12.5); SELECT COUNT(*) FROM OrderDetails WHERE OrderID=1 AND ProductID=1; ROLLBACK;', ['2'])
        check('arbitrary status accepted', "START TRANSACTION; UPDATE Orders SET Status='SyntheticUnknown' WHERE OrderID=1; SELECT Status FROM Orders WHERE OrderID=1; ROLLBACK;", ['SyntheticUnknown'])
        queries = (source / 'queries.sql').read_text(encoding='utf-8')
        for block in queries.split('-- case: ')[1:]:
            name = block.splitlines()[0]
            expected = json.loads(re.search(r'^-- expect: (.+)$', block, re.M).group(1))
            sql = '\n'.join(line for line in block.splitlines()[1:] if not line.startswith('--'))
            check('example '+name, sql, expected)
        check('examples rolled back mutations', 'SELECT StockQuantity FROM Products WHERE ProductID=2; SELECT COUNT(*) FROM Orders;', ['10','3'])
        check('no non-null orphan relationships', 'SELECT (SELECT COUNT(*) FROM Products p LEFT JOIN Suppliers s ON p.SupplierID=s.SupplierID WHERE p.SupplierID IS NOT NULL AND s.SupplierID IS NULL),(SELECT COUNT(*) FROM Orders o LEFT JOIN Customers c ON o.CustomerID=c.CustomerID WHERE o.CustomerID IS NOT NULL AND c.CustomerID IS NULL),(SELECT COUNT(*) FROM OrderDetails d LEFT JOIN Orders o ON d.OrderID=o.OrderID WHERE d.OrderID IS NOT NULL AND o.OrderID IS NULL),(SELECT COUNT(*) FROM OrderDetails d LEFT JOIN Products p ON d.ProductID=p.ProductID WHERE d.ProductID IS NOT NULL AND p.ProductID IS NULL)', ['0\t0\t0\t0'])
        check('drop disposable schema', 'DROP DATABASE ShopGadgetsOnlinePlace', database=False)
        check('repeat fresh setup', schema + '\n' + seed, database=False)
        check('repeat setup aggregate', 'SELECT SUM(Quantity*Price) FROM OrderDetails', ['55.00'])
        check('final cleanup', 'DROP DATABASE ShopGadgetsOnlinePlace', database=False)
        check('schema absent', "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name='ShopGadgetsOnlinePlace'", ['0'], database=False)
        report['status'] = 'PASS'
    except Exception as exc:
        report['status'] = 'FAIL'
        report['error'] = str(exc)
        raise
    finally:
        if server is not None:
            shutdown = call(client + ['--execute', 'SHUTDOWN'])
            report['shutdown_returncode'] = shutdown.returncode
            try:
                server.wait(timeout=30)
            except subprocess.TimeoutExpired:
                server.terminate()
                server.wait(timeout=10)
                report['status'] = 'FAIL'
                report['error'] = 'Graceful shutdown timed out; process terminated'
            report['server_exit'] = server.returncode
            if shutdown.returncode != 0 or server.returncode != 0:
                report['status'] = 'FAIL'
        (work / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(str(work))
    if report['status'] != 'PASS':
        raise RuntimeError('Cleanup/server status failed; inspect results.json')
    print(str(len(results)) + ' checks passed; schema dropped and isolated server stopped.')


if __name__ == '__main__':
    main()
