from fastod import MySQL

cfg = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root@0',
    'db': 'test'
}

db = MySQL(**cfg)

# 生成测试表（默认1w条数据）
# db.gen_test_table('test_20250622')

t = db['test_20250622']
# 删除测试表
# t.remove()

lines = t.query(limit=10)
for line in lines:
    print(line)
