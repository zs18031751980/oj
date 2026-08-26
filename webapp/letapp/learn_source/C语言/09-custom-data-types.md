# 第九章：用户自己建立数据类型

> **对应视频：**
> - 翁恺 P90-P94：字符串、字符串变量、字符串输入输出、字符串数组、单字符输入输出、字符串函数(strlen/strcmp/strcpy)、字符串搜索函数、枚举
> - 小甲鱼 059-062
> - 链接：https://www.bilibili.com/video/BV1eV31zhEr1/?p=90
>
> **说明：** 翁恺课程中"结构体"内容分布在字符串相关章节中，枚举有独立讲解。结构体和链表的系统讲解建议配合小甲鱼 059-062 补充。

**前面用的 int、float、char 都是"基础类型"，只能存一个数据。结构体让你可以"自定义类型"，把多个不同类型的数据打包在一起。**

### 结构体 -- 把相关数据打包

假设你要描述一个学生：有名字（字符串）、年龄（整数）、成绩（小数）。用基础类型要三个独立变量，容易搞混。用结构体可以打包成一个整体：

```c
struct Student {
    char name[20];   // 名字，字符数组
    int age;         // 年龄，整数
    float score;     // 成绩，浮点数
};
```

这样 `struct Student` 就成了一个新类型，就像 int 一样用。
**创建和初始化：**

```c
struct Student s1 = {"Alice", 20, 95.5};  // 创建时就赋值
struct Student s2;                          // 先创建，后赋值
s2.age = 21;
s2.score = 88.5;
strcpy(s2.name, "Bob");  // 字符串不能直接 = 赋值，要用 strcpy
```

**访问成员用 `.`（点号）：**

```c
printf("Name: %s, Age: %d, Score: %.1f\n", s1.name, s1.age, s1.score);
// 输出：Name: Alice, Age: 20, Score: 95.5
```

### 结构体指针

指向结构体的指针，用 `->` 访问成员（比 `(*p).` 方便）：

```c
struct Student s = {"Alice", 20, 95.5};
struct Student *p = &s;

printf("%s\n", p->name);    // Alice（(*p).name 的简写）
printf("%d\n", (*p).age);   // 20（和 p->age 一样）
```

`.` 和 `->` 的区别：
- **`s.name`**：s 是结构体变量本身，用 `.`
- **`p->name`**：p 是指向结构体的指针，用 `->`

### 结构体数组

数组里每个元素都是一个结构体，就像一个 Excel 表格：

```c
struct Student class[3] = {
    {"Alice", 20, 95},
    {"Bob", 21, 88},
    {"Charlie", 20, 76}
};

// 用循环访问
for (int i = 0; i < 3; i++) {
    printf("%s: %.1f\n", class[i].name, class[i].score);
}
```

### 共用体 union -- 所有成员共享同一块内存

```c
union Data {
    int i;
    float f;
    char str[4];
};
```

和结构体的区别：struct 的成员各有各的内存，union 的成员**共用同一块内存**。同一时间只能存一种类型的值。

```c
union Data d;
d.i = 42;         // 存了一个整数
printf("%d\n", d.i);   // 42
d.f = 3.14;       // 现在存了浮点数，之前的 42 被覆盖了
printf("%d\n", d.i);   // 输出一个奇怪的数（因为那块内存现在存的是 3.14 的二进制形式）
```

### 枚举 enum -- 给数字起名字

```c
enum Color { RED, GREEN, BLUE };
// RED = 0, GREEN = 1, BLUE = 2（自动从 0 开始编号）

enum Weekday { MON = 1, TUE, WED, THU, FRI, SAT, SUN };
// MON = 1, TUE = 2, ... SUN = 7（从指定值开始编号）

enum Color c = RED;    // c 的值就是 0
```

好处：`MON` 比 `1` 更有可读性，代码里写 `day == MON` 比 `day == 1` 更清楚。

### typedef -- 给类型起别名

```c
typedef struct Student {
    char name[20];
    int age;
} Stu;   // 给 struct Student 起了个短名叫 Stu

Stu s = {"Alice", 20};  // 不用再写 struct Student 了
```

### 链表基础

**数组的问题**：大小固定，创建后不能增减。
**链表**：每个节点存数据 + 下一个节点的地址，像一条链子一样串起来。大小可以随时增减。

```c
struct Node {
    int data;          // 存数据
    struct Node *next; // 指向下一个节点的指针
};
```

```
[10] → [20] → [30] → NULL
 ↑
head（链表的头，从这里开始）
```

核心操作：
- **创建节点**：用 `malloc` 分配内存，初始化数据和 next 指针
- **遍历链表**：从 head 开始，`p = p->next` 一个一个往后走，直到 `p == NULL`
- **插入节点**：修改前后节点的指针指向
- **删除节点**：把要删的节点跳过，然后 `free` 释放内存

> **参考视频：** 翁恺 P119-P125 | 小甲鱼 059-062

---
