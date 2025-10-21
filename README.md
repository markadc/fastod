# FastOD - Fast Operation Database

[![PyPI version](https://img.shields.io/pypi/v/fastod.svg)](https://pypi.org/project/fastod/)
[![Python version](https://img.shields.io/pypi/pyversions/fastod.svg)](https://pypi.org/project/fastod/)
[![License](https://img.shields.io/pypi/l/fastod.svg)](https://github.com/markadc/fastod/blob/main/LICENSE)

**从此告别 SQL 语句，直接调用方法就可以实现增删改查！**

一个简单、直观、强大的 MySQL 数据库操作工具，让你无需编写 SQL 语句即可完成常见的数据库操作。

## ✨ 核心特性

- 🚀 **零 SQL 编写**：完全面向对象的 API，告别繁琐的 SQL 语句
- 🎯 **直观易用**：简单暴力的使用方式，上手即用
- 🔄 **灵活连接**：支持传统连接和 URL 连接两种方式
- 💾 **智能插入**：自动推导数据类型，支持单条/批量插入
- 🛡️ **冲突处理**：内置三种插入模式处理数据冲突
- 🔍 **强大查询**：支持条件查询、随机查询、分页等多种查询方式
- 📊 **批量操作**：高效的批量插入、更新、删除操作
- 🎲 **测试友好**：一键生成测试数据表

## 📋 环境要求

- Python 3.10+
- MySQL 数据库

## 📦 安装

```bash
pip install fastod
```

## 🚀 快速开始

### 1️⃣ 连接数据库

**方式一：传统参数连接**

```python
from fastod import MySQL

# 直接传参
db = MySQL(
    host="localhost",
    port=3306,
    username="root",
    password="your_password",
    db="test"
)

# 使用配置字典
MYSQL_CONF = {
    'host': 'localhost',
    'port': 3306,
    'username': 'root',
    'password': 'your_password',
    'db': 'test'
}
db = MySQL(**MYSQL_CONF)
```

**方式二：URL 连接**

```python
MYSQL_URL = "mysql://root:your_password@localhost:3306/test"
db = MySQL.from_url(MYSQL_URL)
```

### 2️⃣ 获取表对象

```python
# 方式1：使用索引方式
people = db['people']

# 方式2：使用方法
people = db.pick_table('people')
```

### 3️⃣ 生成测试数据（可选）

```python
# 一键创建测试表并插入数据
# 创建 people 表，每次插入 1000 条，总共插入 10000 条测试数据
people = db.gen_test_table('people', once=1000, total=10000)
```

## 📖 使用指南

### 📝 插入数据

**单条插入**

```python
data = {'id': 10001, 'name': '小明', 'age': 10, 'gender': '男'}

# 基本插入
people.insert_data(data)

# 模式1：数据冲突时报错（默认行为）
# 模式2：数据冲突时忽略，使用 unique 参数
people.insert_data(data, unique='id')

# 模式3：数据冲突时更新，使用 update 参数
people.insert_data(data, update='age=age+1')
```

**批量插入**

```python
data = [
    {'id': 10002, 'name': '小红', 'age': 12, 'gender': '女'},
    {'id': 10003, 'name': '小强', 'age': 13, 'gender': '男'},
    {'id': 10004, 'name': '小白', 'age': 14, 'gender': '男'}
]

# 自动识别为批量插入
people.insert_data(data)
```

### 🗑️ 删除数据

```python
# 基本删除：WHERE id=1
people.delete(id=1)

# IN 条件删除：WHERE id IN (1, 2, 3)
people.delete(id=[1, 2, 3])

# 带限制的删除：WHERE age=18 LIMIT 100
people.delete(age=18, limit=100)
```

### ✏️ 更新数据

```python
# 基本更新：UPDATE people SET name='tony', job='理发师' WHERE id=1
people.update(new={'name': 'tony', 'job': '理发师'}, id=1)

# 多条件更新：UPDATE people SET job='程序员' WHERE name='thomas' AND phone='18959176772'
people.update(new={'job': '程序员'}, name='thomas', phone='18959176772')
```

### 🔍 查询数据

```python
# 查询所有字段：SELECT * FROM people WHERE id=1
people.query(id=1)

# 查询指定字段：SELECT name, age FROM people WHERE id=2
people.query(pick='name, age', id=2)

# IN 条件查询：SELECT * FROM people WHERE age=18 AND gender IN ('男', '女')
people.query(age=18, gender=['男', '女'])

# 复杂查询：SELECT name FROM people WHERE age=18 AND gender IN ('男', '女') LIMIT 5
people.query(pick='name', age=18, gender=['男', '女'], limit=5)

# 查询数量
count = people.query_count(age=18)

# 检查数据是否存在
exists = people.exists(name='小明')
```

**特殊条件查询**

```python
# NULL 查询：WHERE age IS NULL
people.query(age=None)

# NOT NULL 查询：WHERE age IS NOT NULL
people.query(age=True)

# IS NULL 查询：WHERE age IS NULL
people.query(age=False)
```

### 🎲 随机数据

```python
# 随机返回 1 条数据（返回 dict）
data = people.random()

# 随机返回 5 条数据（返回 list）
data_list = people.random(limit=5)
```

### 🔄 遍历表（大数据量扫描）

```python
# 遍历整张表，默认每轮扫描 1000 条
people.scan()

# 自定义处理函数
def show(lines):
    for idx, item in enumerate(lines, start=1):
        print(f'第{idx}条  {item}')

# 限制范围遍历：id 从 101 到 222，每轮扫描 100 条
people.scan(sort_field='id', start=101, end=222, once=100, dealer=show)

# 添加额外条件：在限制范围的基础上，只查询 age=18 的数据
people.scan(
    sort_field='id',
    start=101,
    end=222,
    once=100,
    dealer=show,
    add_cond='age=18'
)
```

## 🔧 高级功能

### SQL 构建器

```python
from fastod.core.db import GenSQL

# 快速构建 SQL 语句
sql = GenSQL('people').select('name, age').where(age=18).limit(10).build()
# 输出: SELECT name, age FROM people WHERE age = 18 LIMIT 10
```

### 批量更新

```python
# 更新单条数据（基于 depend 字段）
people.update_one({'id': 1, 'name': '新名字'}, depend='id')

# 批量更新多条数据
data = [
    {'id': 1, 'name': '小明', 'age': 20},
    {'id': 2, 'name': '小红', 'age': 21},
]
people.update_many(data, depend='id')

# 单条 SQL 批量更新（使用 CASE WHEN）
people.update_some(data, depend='id')
```

### 去重插入

```python
# 基于指定字段去重后插入
items = [
    {'phone': '13800138000', 'name': '用户1'},
    {'phone': '13800138001', 'name': '用户2'},
]
# 只插入表中不存在的 phone
people.dedup_insert_data(items, dedup='phone')
```

### 获取字段范围

```python
# 获取字段最小值
min_age = people.get_min('age')

# 获取字段最大值
max_age = people.get_max('age')
```

## 📚 API 返回值

所有操作都会返回 `Feedback` 对象，包含以下属性：

```python
result = people.query(id=1)

# 属性说明
result.ok        # bool: 操作是否成功
result.affect    # int: 影响的行数
result.result    # list/dict/None: 查询结果
result.error     # str/None: 错误信息
```

## 📝 更新日志

### v0.2.5 (2025-07-06)

- ✨ 新增 `GenSQL` 对象，快速构建 SQL 语句
- 🔧 多项性能优化和代码改进

### v0.2.4 (2025-06-28)

- 📦 SQLResponse 统一存在三个属性

### v0.2.3 (2025-06-27)

- 🔍 kwargs 中解析的 `True` 值为 `IS NOT NULL`，`False` 值为 `IS NULL`

## ⚠️ 注意事项

1. **Python 版本**：需要 Python 3.10 或更高版本
2. **连接池**：自动管理数据库连接池，无需手动管理连接
3. **数据安全**：所有操作都使用参数化查询，防止 SQL 注入
4. **唯一索引**：使用 `unique` 和 `update` 参数时，确保字段有唯一索引
5. **批量操作**：大数据量操作建议使用 `scan` 方法分批处理

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👨‍💻 作者

**WangTuo** - [markadc@126.com](mailto:markadc@126.com)

---

⭐ 如果这个项目对你有帮助，请给一个 Star！
