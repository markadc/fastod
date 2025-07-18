from fastod import MySQL, SQL

cfg = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "root@0",
    "db": "test",
}

db = MySQL(**cfg)

sql = SQL("test").select("name, id").where(age=22).limit(20)
print(sql.build())  # SELECT name, id FROM test WHERE age = 22 LIMIT 20

sql = SQL("demo").select("name, id").where(age=[18, 22, 66])
print(sql.build())  # SELECT name, id FROM demo WHERE age IN (18, 22, 66)

sql = SQL("demo").select("name, id").where(age=["18", "22", "66"])
print(sql.build())  # SELECT name, id FROM demo WHERE age IN ('18', '22', '66')

sql = SQL("demo").select().where(vip=False, expire=True)
print(sql.build())  # SELECT * FROM demo WHERE vip IS NULL AND expire IS NOT NULL
