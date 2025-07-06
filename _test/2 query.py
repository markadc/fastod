from fastod import MySQL

cfg = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root@0',
    'db': 'test'
}
db = MySQL(**cfg)
test = db["test"]

lines = test.query(limit=10)
print(len(lines))
for line in lines:
    print(line)

lines = test.query(pick="id, name, age", age=[20, 60], limit=5)
print(len(lines))
for line in lines:
    print(line)
