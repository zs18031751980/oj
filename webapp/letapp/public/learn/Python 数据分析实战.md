# Python 数据分析实战

## 课程目标

围绕一个完整的小数据分析流程，建立"读取数据 → 清洗数据 → 分析数据 → 展示结果"的完整思路。我们将用一个真实的销售数据案例来逐步演示每一步的操作，让零基础的同学也能跟着做下来。

---

## 建议内容

### 数据读取

数据分析的第一步就是把数据"拿"到 Python 中来。最常见的数据来源是 CSV 文件和 Excel 文件。

#### 读取 CSV 文件
CSV（逗号分隔值）是最通用的数据交换格式，几乎任何数据处理软件都支持它。

```python
import pandas as pd

# 基础读取
df = pd.read_csv("sales_data.csv")

# 如果 CSV 文件编码不对会出现乱码，试试指定编码
df = pd.read_csv("sales_data.csv", encoding="utf-8")
# 如果还不行，试试 gbk（中文 Windows 系统常用）
df = pd.read_csv("sales_data.csv", encoding="gbk")

# 常用参数说明
df = pd.read_csv(
    "sales_data.csv",
    encoding="utf-8",
    sep=",",           # 分隔符，默认是逗号
    header=0,          # 第几行作为列名（0 表示第一行）
    nrows=1000,        # 只读取前 1000 行（数据量大时很有用）
    usecols=["A", "B", "C"],  # 只读取指定列
    dtype={"id": str}  # 指定列的数据类型
)
```

#### 读取 Excel 文件
```python
# 读取 Excel 文件
df = pd.read_excel("sales_data.xlsx", sheet_name="Sheet1")

# 如果 Excel 有多个工作表
xls = pd.ExcelFile("sales_data.xlsx")
df1 = pd.read_excel(xls, "Sheet1")
df2 = pd.read_excel(xls, "Sheet2")
```

#### 读取后立即检查数据
```python
# 必做三步检查

# 1. 看看数据长什么样
df.head(10)      # 前 10 行
df.tail(5)       # 后 5 行
df.sample(5)     # 随机抽 5 行

# 2. 看看数据的基本信息
df.info()
# 输出示例：
# <class 'pandas.core.frame.DataFrame'>
# RangeIndex: 1000 entries, 0 to 999
# Data columns (total 8 columns):
#  #   Column     Non-Null Count  Dtype
# ---  ------     --------------  -----
#  0   订单编号      1000 non-null   object
#  1   商品名称      1000 non-null   object
#  2   销售量        985 non-null    float64  ← 有缺失值！
#  3   单价          1000 non-null   float64
#  4   总金额        990 non-null    float64  ← 有缺失值！
#  5   下单日期      1000 non-null   object
#  6   客户城市      950 non-null    object   ← 有缺失值！
#  7   是否退货      1000 non-null   object

# 3. 看看数值列的统计摘要
df.describe()
# 输出：计数、均值、标准差、最小值、25%/50%/75% 分位数、最大值
```

---

### 数据清洗

现实中的数据是不完美的，通常会有缺失值、重复值、异常值等问题。数据清洗就是"把脏数据洗干净"的过程。

#### 缺失值处理
```python
# 1. 查看缺失值情况
df.isnull().sum()           # 每列缺失值的数量
df.isnull().sum() / len(df) # 每列缺失值的比例

# 2. 处理缺失值的方式

# 方式一：删除有缺失值的行（简单粗暴）
df_clean = df.dropna()                     # 删除任何有缺失值的行
df_clean = df.dropna(subset=["销售量"])     # 只在指定列有缺失时才删除

# 方式二：填充缺失值
df["销售量"] = df["销售量"].fillna(0)                     # 用 0 填充
df["销售量"] = df["销售量"].fillna(df["销售量"].mean())   # 用平均值填充
df["销售量"] = df["销售量"].fillna(df["销售量"].median()) # 用中位数填充
df["销售量"] = df["销售量"].ffill()                       # 用上一个值填充（时间序列常用）
df["销售量"] = df["销售量"].bfill()                       # 用下一个值填充

# 方式三：插值填充（适用于时间序列数据）
df["销售量"] = df["销售量"].interpolate()
```

#### 重复值处理
```python
# 1. 检查重复值
df.duplicated()               # 每行是否为重复行
df.duplicated().sum()         # 重复行数量
df[df.duplicated()]           # 查看重复的行

# 2. 基于指定列判断重复
df.duplicated(subset=["订单编号"])  # 检查订单编号是否重复

# 3. 删除重复值
df_clean = df.drop_duplicates()                       # 删除完全重复的行
df_clean = df.drop_duplicates(subset=["订单编号"])     # 基于指定列去重
df_clean = df.drop_duplicates(keep="first")            # 保留第一次出现的（默认）
df_clean = df.drop_duplicates(keep="last")             # 保留最后一次出现的
```

#### 异常值处理
异常值是指明显偏离正常范围的数据，比如销售量为负数、年龄为 200 岁等。

```python
# 1. 通过描述性统计发现异常值
df.describe()
# 如果发现"销售量"的最小值是 -100，那就有问题了

# 2. 通过箱线图发现异常值
import matplotlib.pyplot as plt
df.boxplot(column=["销售量"])
plt.show()  # 箱线图会把异常值显示为孤立点

# 3. 通过业务规则过滤
df = df[df["销售量"] > 0]          # 销售量必须大于 0
df = df[df["单价"] > 0]            # 单价必须大于 0
df = df[df["下单日期"] >= "2020-01-01"]  # 日期范围过滤

# 4. 通过统计方法（3σ 原则）过滤
mean = df["总金额"].mean()
std = df["总金额"].std()
df = df[(df["总金额"] >= mean - 3 * std) & (df["总金额"] <= mean + 3 * std)]

# 5. 通过 IQR（四分位距）方法过滤
Q1 = df["总金额"].quantile(0.25)
Q3 = df["总金额"].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
df = df[(df["总金额"] >= lower) & (df["总金额"] <= upper)]
```

#### 数据类型转换
```python
# 检查每列的数据类型
df.dtypes

# 常见的问题：日期被读成了字符串
df["下单日期"] = pd.to_datetime(df["下单日期"])

# 数值列被读成了字符串（比如数字里有逗号）
df["总金额"] = df["总金额"].str.replace(",", "").astype(float)

# 分类数据转为 category 类型（节省内存）
df["客户城市"] = df["客户城市"].astype("category")
```

---

### 分析与可视化

数据洗干净后，就到了最有趣的部分——分析和可视化。这时候你需要从数据中"问问题"，然后用代码来回答。

#### 分组统计
分组统计是数据分析中最常用的操作，相当于 Excel 的"数据透视表"：

```python
# 按城市分组，计算每个城市的总销售额
city_sales = df.groupby("客户城市")["总金额"].sum().sort_values(ascending=False)
print(city_sales)

# 按城市分组，计算多个统计量
city_stats = df.groupby("客户城市").agg({
    "总金额": ["sum", "mean", "count", "max"],
    "销售量": ["sum", "mean"]
})
print(city_stats)

# 按城市和月份分组
df["月份"] = df["下单日期"].dt.month
city_month = df.groupby(["客户城市", "月份"])["总金额"].sum()
print(city_month)
```

#### 数据透视表
```python
# 创建透视表
pivot = pd.pivot_table(
    df,
    values="总金额",        # 要计算的数值
    index="客户城市",       # 行索引
    columns="月份",         # 列索引
    aggfunc="sum",          # 聚合函数
    fill_value=0            # 空值填充为 0
)
print(pivot)
```

#### 可视化分析

**折线图 —— 展示趋势**：
```python
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体（解决中文乱码）
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 每日销售额趋势
daily_sales = df.groupby("下单日期")["总金额"].sum()
plt.figure(figsize=(12, 6))
plt.plot(daily_sales.index, daily_sales.values, marker="o", linestyle="-", color="blue")
plt.title("每日销售额趋势")
plt.xlabel("日期")
plt.ylabel("销售额（元）")
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

**柱状图 —— 展示对比**：
```python
# 各城市销售额对比
city_sales = df.groupby("客户城市")["总金额"].sum().sort_values(ascending=False).head(10)
plt.figure(figsize=(10, 6))
plt.bar(city_sales.index, city_sales.values, color="skyblue")
plt.title("各城市销售额 TOP 10")
plt.xlabel("城市")
plt.ylabel("销售额（元）")
plt.xticks(rotation=45)
for i, v in enumerate(city_sales.values):
    plt.text(i, v, f"{v:.0f}", ha="center", va="bottom")
plt.tight_layout()
plt.show()
```

**散点图 —— 展示两个变量的关系**：
```python
# 销售量和总金额的关系
plt.figure(figsize=(8, 6))
plt.scatter(df["销售量"], df["总金额"], alpha=0.5, color="red")
plt.title("销售量与总金额的关系")
plt.xlabel("销售量")
plt.ylabel("总金额（元）")
plt.grid(True, alpha=0.3)
plt.show()
```

**热力图 —— 展示多个变量之间的相关性**：
```python
# 计算相关系数矩阵
numeric_cols = df.select_dtypes(include=["float64", "int64"])
corr_matrix = numeric_cols.corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", center=0, fmt=".2f")
plt.title("各变量相关性热力图")
plt.tight_layout()
plt.show()
```

**进阶：用 seaborn 一行搞定复杂图表**：
```python
# 箱线图：看不同城市的销售额分布
sns.boxplot(x="客户城市", y="总金额", data=df)

# 小提琴图：箱线图的升级版，还能看到数据的分布形状
sns.violinplot(x="客户城市", y="总金额", data=df)

# 分面散点图：按不同类别分别画散点图
sns.lmplot(x="销售量", y="总金额", hue="是否退货", data=df)
```

---

## 完整分析案例

下面是一个完整的数据分析流程示例，把前面学到的所有步骤串起来：

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文显示
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 1. 读取数据
print("=" * 50)
print("第一步：读取数据")
print("=" * 50)
df = pd.read_csv("sales_data.csv", encoding="utf-8")
print(f"数据形状：{df.shape}")

# 2. 数据清洗
print("\n" + "=" * 50)
print("第二步：数据清洗")
print("=" * 50)
print(f"清洗前数据量：{len(df)}")

# 处理缺失值
df = df.dropna(subset=["销售量", "总金额"])

# 处理重复值
df = df.drop_duplicates(subset=["订单编号"])

# 过滤异常值
df = df[df["销售量"] > 0]
df = df[df["单价"] > 0]

# 转换日期
df["下单日期"] = pd.to_datetime(df["下单日期"])

print(f"清洗后数据量：{len(df)}")

# 3. 数据分析
print("\n" + "=" * 50)
print("第三步：数据分析")
print("=" * 50)

# 总体销售情况
total_sales = df["总金额"].sum()
avg_order = df["总金额"].mean()
print(f"总销售额：{total_sales:.2f} 元")
print(f"平均每单金额：{avg_order:.2f} 元")

# 各城市销售排名
city_rank = df.groupby("客户城市")["总金额"].sum().sort_values(ascending=False)
print("\n各城市销售额排名：")
print(city_rank.head(5))

# 4. 可视化
print("\n" + "=" * 50)
print("第四步：可视化展示")
print("=" * 50)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图1：每日销售趋势
daily = df.groupby("下单日期")["总金额"].sum()
axes[0, 0].plot(daily.index, daily.values, color="blue")
axes[0, 0].set_title("每日销售趋势")
axes[0, 0].tick_params(axis="x", rotation=45)

# 图2：城市销售额 TOP 10
top10 = city_rank.head(10)
axes[0, 1].bar(top10.index, top10.values, color="skyblue")
axes[0, 1].set_title("城市销售额 TOP 10")
axes[0, 1].tick_params(axis="x", rotation=45)

# 图3：销售量分布
axes[1, 0].hist(df["销售量"], bins=30, color="green", alpha=0.7)
axes[1, 0].set_title("销售量分布")

# 图4：相关性热力图
numeric_df = df.select_dtypes(include=["float64", "int64"])
sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", ax=axes[1, 1])
axes[1, 1].set_title("相关性热力图")

plt.tight_layout()
plt.show()
```

---

## 练习建议

1. **从身边的数据开始**：分析自己的支付宝/微信账单、运动记录、学习时长记录，用学到的技能发现有趣的信息
2. **把每一步都拆成函数**：数据读取、清洗、分析、可视化各写成一个函数，再用不同输入数据测试边界情况
3. **尝试不同的数据集**：Kaggle 上有大量免费的真实数据集（如 Titanic、Iris、房价预测等），每个数据集都有不同的特点
4. **多思考"为什么"**：看到数据中的某个现象（比如某个城市销售额特别高），试着分析背后的原因
5. **学会用搜索引擎**：遇到不会的操作时，搜索"pandas + 你想要的功能"通常能快速找到答案。Stack Overflow 和 pandas 官方文档是最好的学习资源
