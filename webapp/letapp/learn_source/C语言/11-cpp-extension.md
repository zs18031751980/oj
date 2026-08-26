# C++ 知识点详解

> 适合 C 基础打好后继续学习。
> **对应视频：** 侯捷 C++ 面向对象高级开发（https://www.bilibili.com/video/BV1nL5KzqEZz）
> - 上：C++ 基础增强、类与对象、构造/析构函数、拷贝构造、内存管理
> - 下：继承、多态、虚函数、STL 标准模板库

---

### C 和 C++ 到底有什么区别？

一句话总结：**C++ 是 C 的超集，在 C 的基础上加了面向对象、泛型编程、STL 标准库等特性。** 所有合法的 C 代码基本都能在 C++ 里跑，但 C++ 多了很多东西。

| 对比项  | C 语言                       | C++                              |
|---|---|---|
| 编程思想 | **面向过程**：关注"怎么一步步做"        | 面向对象 + 面向过程兼备：关注"谁来做"            |
| 结构体  | struct 只能放数据，不能放函数         | struct 可以放数据 + 函数（和 class 几乎一样）  |
| 输入输出 | `scanf` / `printf`         | `cin` / `cout`（更方便、更安全）          |
| 字符串  | 用 `char[]` + `string.h` 函数 | 有 `string` 类，可以直接 `+` 拼接、`==` 比较 |
| 内存分配 | `malloc` / `free`          | `new` / `delete`（会自动调用构造/析构函数）   |
| 函数   | 同名函数不能有多个                  | 支持**函数重载**（同名但参数不同）              |
| 错误检查 | 编译期不严格检查类型匹配               | 编译期更严格，类型检查更安全                   |
| 标准库  | 很少，几乎什么都要自己写               | STL 提供大量现成容器和算法                  |

**学习建议：** 先学好 C 语言基础（前十章），再学 C++ 新增的这些特性，会发现很多 C 里很麻烦的事在 C++ 里变得很简单。
---

### 1. 命名空间 namespace

**问题：** 在一个大项目里，你写了一个叫 `print` 的函数，同事也写了一个叫 `print` 的函数，名字冲突了怎么办？
**C 的做法：** 没有好办法，只能自己注意命名不要重复，或者加前缀（比如 `my_print`、`utils_print`）。
**C++ 的做法：** 用 namespace 把代码分组。

```cpp
#include <iostream>
using namespace std;    // 使用标准命名空间（这样可以直接写 cout，不用写 std::cout）

namespace MyLib {
    void print() {
        cout << "MyLib 的 print" << endl;
    }
}

namespace YourLib {
    void print() {
        cout << "YourLib 的 print" << endl;
    }
}

int main() {
    MyLib::print();     // 调用 MyLib 里的 print
    YourLib::print();   // 调用 YourLib 里的 print
    return 0;
}
```

**`::` 叫"作用域解析运算符"**，告诉编译器"去哪个命名空间里找这个东西"。
`using namespace std;` 的意思是"以后用标准库的东西不用写 `std::` 前缀了"。写小程序可以这么用，大项目不建议（容易冲突）。
---

### 2. 引用 &

**引用 = 给变量起一个别名。** 就像你的真名叫陈智祥，但朋友也叫你小陈，"小陈"和"陈智祥"是同一个人。

```cpp
int a = 10;
int &b = a;    // b 是 a 的别名，b 和 a 指向同一块内存

b = 20;        // 通过 b 修改，a 也变成 20
cout << a;     // 输出 20
```

**和 C 语言指针的区别：**

| 指针（C） | 引用（C++）             |                  |
|---|---|---|
| 声明    | `int *p = &a;`      | `int &b = a;`    |
| 使用    | `*p` 解引用才能访问值       | 直接用 `b`，不用解引用    |
| 能否为空  | `int *p = NULL;` 可以 | 引用必须在声明时就绑定，不能为空 |
| 能否改指向 | `p = &b;` 可以改       | 引用一旦绑定就不能改       |

**引用最大的用处：函数参数传递。**
C 语言里要交换两个数必须传指针：

```c
// C 语言写法
void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}
swap(&x, &y);  // 传地址
```

C++ 里用引用，写法和调用都更自然：

```cpp
// C++ 写法
void swap(int &a, int &b) {  // a, b 是外面实参的别名
    int temp = a;
    a = b;
    b = temp;
}
swap(x, y);  // 直接传变量，不用加 &
```

---

### 3. 函数重载

**C 语言不允许同名函数。** 如果你要写一个 `max` 求两个 int 的最大值，再写一个 `max` 求两个 float 的最大值，C 语言会报错，只能叫 `max_int` 和 `max_float`。
**C++ 允许同名函数，只要参数列表不同就行：**

```cpp
int max(int a, int b) {
    return (a > b) ? a : b;
}

float max(float a, float b) {
    return (a > b) ? a : b;
}

int max(int a, int b, int c) {  // 参数个数不同也行
    return max(max(a, b), c);
}

int main() {
    cout << max(3, 5) << endl;       // 调用两个参数的 int 版本 → 5
    cout << max(1.5f, 2.5f) << endl;  // 调用 float 版本 → 2.5
    cout << max(1, 2, 3) << endl;     // 调用三个参数的版本 → 3
    return 0;
}
```

编译器根据你调用时传的参数类型和个数，**自动选择**对应的函数。
**注意：** 只有返回值不同、参数完全相同的两个函数**不能**构成重载（编译器无法区分）。
---

### 4. const

`const` = 这个值一旦赋值就不能改（"只读"）。

```cpp
const int PI = 3;     // PI 不能再改了
// PI = 4;             // 编译报错！

const int &ref = a;   // const 引用：可以通过它读 a，但不能通过它改 a
```

**和 C 的 `#define` 比：**
- `#define PI 3.14` 是简单的文本替换，编译器看不到 PI 这个名字
- `const double PI = 3.14` 是真正的变量，有类型检查，调试时能看到名字
C++ 里优先用 `const`，更安全更清晰。
---

### 5. new 和 delete（C++ 版的 malloc/free）

```cpp
// C 语言写法
int *p = (int *)malloc(5 * sizeof(int));
*p = 10;
free(p);

// C++ 写法
int *p = new int(10);              // 申请一个 int，值为 10
int *arr = new int[5];             // 申请 5 个 int 的数组
arr[0] = 10;

delete p;          // 释放单个
delete[] arr;      // 释放数组（注意加 []）
```

**new/delete 和 malloc/free 的区别：**

| malloc/free（C） | new/delete（C++）     |                           |
|---|---|---|
| 类型安全           | 返回 `void*`，需要手动强制转换 | 自动返回正确类型的指针               |
| 初始化            | 申请的内存是垃圾值           | `new int(10)` 可以直接初始化为 10 |
| 构造/析构          | 不会调用构造函数和析构函数       | 自动调用（对 class 对象很重要）       |
| 失败处理           | 返回 `NULL`           | 抛出异常                      |

**规则：** C++ 里用了 `new` 就必须用 `delete`，用了 `new[]` 就必须用 `delete[]`，不能混用。
---

### 6. string 字符串类

**C 语言的字符串（char 数组）问题：**
- 长度固定，容易越界
- 操作麻烦（`strcpy`、`strcat` 容易出错）
- 不能直接用 `+` 拼接，不能直接用 `==` 比较
**C++ 的 string 类解决了这些问题：**

```cpp
#include <string>
using namespace std;

string s1 = "Hello";
string s2 = " World";

// 拼接（C 里要用 strcat）
string s3 = s1 + s2;       // s3 = "Hello World"

// 比较（C 里要用 strcmp）
if (s1 == "Hello") { ... }  // 直接用 ==！
if (s1 != s2) { ... }

// 获取长度
int len = s1.length();      // 或 s1.size()

// 访问字符
char ch = s1[0];            // ch = 'H'

// 查找子串
int pos = s1.find("ll");    // 返回 2（从 0 开始数，"ll" 在位置 2）

// 截取子串
string sub = s1.substr(0, 3); // 从位置 0 开始取 3 个字符 → "Hel"
```

**总结：** 能用 `string` 就用 `string`，比 C 的 `char[]` + `string.h` 方便太多。
---

### 7. cin 和 cout（C++ 的输入输出）

```cpp
#include <iostream>
using namespace std;

int a;
float b;
string s;

cin >> a;           // 从键盘读一个整数（不需要 &！）
cin >> a >> b;      // 连续读多个
cout << a << endl;  // 输出 a 并换行（endl = 换行 + 刷新缓冲区）
cout << "a = " << a << ", b = " << b << endl;  // 链式输出
```

**和 C 语言的 printf/scanf 对比：**

| C（printf/scanf） | C++（cout/cin）     |              |
|---|---|---|
| 格式控制            | 用 `%d`、`%f` 等格式符  | 自动识别类型，不用格式符 |
| 取地址             | scanf 需要 `&`      | cin 不需要 `&`  |
| 安全性             | 格式符和变量类型不匹配会出 bug | 类型安全，编译器会检查  |
| 速度              | 较快                | 稍慢（但日常使用无感）  |

**OJ 刷题小提示：** 有些 OJ 系统用 `cin/cout` 可能会超时，可以加上这行关闭同步来加速：

```cpp
ios::sync_with_stdio(false);
cin.tie(nullptr);
```

---

### 8. 面向对象编程（OOP）

这是 C++ 和 C 最本质的区别。C 语言是"面向过程"的，关注步骤；C++ 是"面向对象"的，关注"谁来做"。
**生活类比：**
- **面向过程（C）**：你自己做一顿饭 -- 洗菜、切菜、炒菜、装盘（关注每一步怎么做）
- **面向对象（C++）**：你去饭店，告诉厨师"我要一份宫保鸡丁"。厨师（对象）内部怎么做的你不用管，他给你成品（关注"谁"来做）

#### 类和对象

**类 = 设计图纸，对象 = 按图纸造出来的实物。**

```cpp
class Student {
public:                    // public = 外面可以访问
    string name;
    int age;
    float score;

    void printInfo() {     // 类里面可以放函数！
        cout << name << " " << age << " " << score << endl;
    }

    float getGrade() {      // 方法（函数）
        if (score >= 90) return 'A';
        if (score >= 80) return 'B';
        if (score >= 60) return 'C';
        return 'D';
    }
};

int main() {
    Student s1;                // 按照类创建一个对象（实例化）
    s1.name = "Alice";         // 用 . 访问成员
    s1.age = 20;
    s1.score = 95;
    s1.printInfo();            // 调用对象的方法
    cout << s1.getGrade() << endl;  // 输出 A
    return 0;
}
```

**和 C 的 struct 对比：** C 的 struct 只能放数据不能放函数，C++ 的 class 可以放数据+函数。C++ 的 struct 也能放函数（和 class 几乎一样，唯一区别是默认访问权限：class 默认 private，struct 默认 public）。

#### 访问控制（封装）

```cpp
class BankAccount {
private:              // private = 只有类内部能访问，外面不能直接改
    string owner;
    double balance;

public:               // public = 外面可以访问
    BankAccount(string name, double money) {  // 构造函数
        owner = name;
        balance = money;
    }

    void deposit(double amount) {   // 存钱
        if (amount > 0)
            balance += amount;
    }

    void withdraw(double amount) {  // 取钱
        if (amount > 0 && amount <= balance)
            balance -= amount;
    }

    double getBalance() {           // 查余额
        return balance;
    }
};
```

**为什么要封装？** 保护数据不被乱改。余额 `balance` 是 private 的，外面不能直接 `account.balance = -100`，只能通过 `deposit()` 和 `withdraw()` 来操作，这样就能在里面加验证逻辑。

#### 构造函数和析构函数

**构造函数 = 创建对象时自动调用的"初始化函数"。**

```cpp
class Student {
private:
    string name;
    int age;
public:
    // 构造函数：函数名和类名相同，没有返回值
    Student(string n, int a) {
        name = n;
        age = a;
    }

    // 析构函数：函数名是 ~类名，没有返回值，没有参数
    // 对象被销毁时自动调用（通常用来释放动态内存）
    ~Student() {
        cout << name << " 被销毁了" << endl;
    }
};
```

```cpp
Student s1("Alice", 20);   // 调用构造函数，初始化
// s1 离开作用域时，自动调用析构函数
```

**构造函数的特殊之处：**
- 函数名和类名一样
- 没有返回值类型（连 `void` 都不写）
- 创建对象时自动调用，只调一次
- 可以有多个（重载），比如无参构造、有参构造、拷贝构造

#### 拷贝构造函数

用一个已有对象创建新对象时调用：

```cpp
Student s1("Alice", 20);
Student s2 = s1;    // 调用拷贝构造函数，把 s1 的数据复制给 s2
```

如果不自己写，编译器会自动生成一个"浅拷贝"版本。但如果类里有指针成员，浅拷贝会导致两个对象指向同一块内存，**非常危险**，这时候必须自己写拷贝构造函数。

#### 继承

**继承 = 子类复用父类的代码。**

```cpp
// 父类（基类）
class Animal {
public:
    string name;
    void eat() {
        cout << name << " 在吃饭" << endl;
    }
};

// 子类（派生类）继承父类
class Dog : public Animal {     // Dog 继承了 Animal
public:
    void bark() {
        cout << name << " 在汪汪叫" << endl;
    }
};

int main() {
    Dog d;
    d.name = "旺财";       // 从父类继承来的 name
    d.eat();                // 从父类继承来的 eat()
    d.bark();               // 自己的方法
    return 0;
}
```

**为什么要继承？** 避免重复代码。`Cat`、`Bird`、`Fish` 都有 `name` 和 `eat()`，不用每个都写一遍，写一次 `Animal` 父类，其他类继承它就行。

#### 多态和虚函数

**多态 = 同一个方法，不同对象调用有不同的行为。**

```cpp
class Animal {
public:
    virtual void speak() {         // virtual = 虚函数
        cout << "动物叫" << endl;
    }
};

class Dog : public Animal {
public:
    void speak() {                 // 子类重写了 speak()
        cout << "汪汪！" << endl;
    }
};

class Cat : public Animal {
public:
    void speak() {
        cout << "喵喵！" << endl;
    }
};

int main() {
    Animal *a1 = new Dog();    // 父类指针指向子类对象
    Animal *a2 = new Cat();

    a1->speak();    // 输出"汪汪！"（不是"动物叫"）
    a2->speak();    // 输出"喵喵！"（不是"动物叫"）
    // 因为 speak 是虚函数，实际调用的是子类的版本

    delete a1;
    delete a2;
    return 0;
}
```

**如果去掉 `virtual`：** `a1->speak()` 会输出"动物叫"，因为编译器根据指针类型（Animal*）决定调用哪个版本，而不是根据实际对象类型。
**纯虚函数和抽象类：**

```cpp
class Shape {                    // 抽象类
public:
    virtual double area() = 0;   // 纯虚函数（= 0 表示"没有实现"）
    // 含有纯虚函数的类不能直接创建对象
};

class Circle : public Shape {
    double radius;
public:
    Circle(double r) : radius(r) {}
    double area() { return 3.14159 * radius * radius; }  // 必须实现
};

class Rectangle : public Shape {
    double w, h;
public:
    Rectangle(double w, double h) : w(w), h(h) {}
    double area() { return w * h; }
};
```

**纯虚函数的意义：** 强制子类必须实现某个方法。就像老板规定"所有员工都必须有工作能力"，具体怎么工作各人自己实现，但不能不实现。
---

### 9. STL 标准模板库

**STL = Standard Template Library，C++ 自带的一堆现成的数据结构和算法。** 这是 C++ 相比 C 语言最大的优势之一。C 语言里你要自己写链表、排序、查找，C++ 里直接用现成的。

#### vector -- 动态数组

**C 的数组大小固定，C++ 的 vector 可以自动扩容。**

```cpp
#include <vector>
using namespace std;

vector<int> v;              // 创建一个空的 int 动态数组

v.push_back(10);            // 末尾添加元素
v.push_back(20);
v.push_back(30);

cout << v[0] << endl;       // 10（和数组一样用下标访问）
cout << v.size() << endl;    // 3（元素个数）
v.pop_back();               // 删除末尾元素，v 变成 {10, 20}

// 用迭代器遍历
for (vector<int>::iterator it = v.begin(); it != v.end(); it++) {
    cout << *it << " ";      // *it 解引用，获取元素值
}

// C++11 更简洁的遍历方式
for (int x : v) {           // 范围 for 循环
    cout << x << " ";
}
```

**和 C 数组对比：**
- 大小不用预先确定，`push_back` 自动扩容
- 有 `size()` 方法知道元素个数
- 有 `push_back`、`pop_back`、`insert`、`erase` 等操作
- 会自动管理内存，不用担心越界

#### map -- 键值对

**map 就像字典：通过"键"快速查到"值"。**

```cpp
#include <map>

map<string, int> m;         // 键是 string，值是 int

m["Alice"] = 95;            // 添加键值对
m["Bob"] = 88;
m["Charlie"] = 76;

cout << m["Alice"] << endl;  // 95，通过键查找值

// 遍历
for (auto &p : m) {          // auto 让编译器自动推断类型
    cout << p.first << " " << p.second << endl;  // first=键, second=值
}

// 检查某个键是否存在
if (m.find("David") != m.end()) {
    cout << "找到了" << endl;
} else {
    cout << "没找到" << endl;
}
```

**常见用途：** 统计词频（统计每个单词出现了多少次）、电话簿（名字→号码）、配置映射等。

#### set -- 不重复集合

**set 里的元素自动排序，而且不会重复。**

```cpp
#include <set>

set<int> s;
s.insert(10);
s.insert(30);
s.insert(20);
s.insert(10);     // 重复插入，不会生效，set 里只有一个 10

// 遍历（自动从小到大排序）
for (int x : s) {
    cout << x << " ";   // 输出：10 20 30
}

cout << s.count(10) << endl;  // 1（存在）
cout << s.count(40) << endl;  // 0（不存在）
```

**常见用途：** 去重、判断某个元素是否存在、求交集/并集。

#### stack 和 queue

**stack（栈）= 后进先出（LIFO）：** 像叠盘子，最后放上去的先拿下来

```cpp
#include <stack>

stack<int> stk;
stk.push(10);       // 放入
stk.push(20);
cout << stk.top();  // 20（栈顶元素）
stk.pop();          // 弹出栈顶
cout << stk.top();  // 10
```

**queue（队列）= 先进先出（FIFO）：** 像排队买饭，先来的先服务

```cpp
#include <queue>

queue<int> q;
q.push(10);        // 入队
q.push(20);
cout << q.front(); // 10（队首元素）
q.pop();           // 出队
cout << q.front(); // 20
```

#### sort -- 排序

```cpp
#include <algorithm>
#include <vector>

vector<int> v = {5, 3, 1, 4, 2};
sort(v.begin(), v.end());            // 从小到大排序 → {1, 2, 3, 4, 5}

// 从大到小排序
sort(v.begin(), v.end(), greater<int>());

// 自定义排序规则
sort(v.begin(), v.end(), [](int a, int b) {
    return a > b;    // 降序（lambda 表达式）
});
```

C 语言里要自己写冒泡排序/快排，C++ 里一行 `sort()` 搞定。
---

### 10. 模板与泛型编程

**模板 = 写一个"通用版本"，让它支持多种数据类型。**
比如你想写一个求最大值的函数，既支持 int 又支持 float 又支持 double，不用写三个函数重载，写一个模板就行：

```cpp
// 函数模板
template <typename T>
T myMax(T a, T b) {
    return (a > b) ? a : b;
}

int main() {
    cout << myMax(3, 5) << endl;         // 自动推导 T = int，输出 5
    cout << myMax(1.5, 2.5) << endl;     // 自动推导 T = double，输出 2.5
    cout << myMax('a', 'z') << endl;     // 自动推导 T = char，输出 z
    return 0;
}
```

编译器根据你调用时的参数类型，**自动生成**对应版本的函数。你只写了一份代码，实际上编译器帮你生成了多份。
**类模板：**

```cpp
template <typename T>
class Stack {
private:
    T data[100];
    int top;
public:
    Stack() : top(-1) {}
    void push(T value) { data[++top] = value; }
    T pop() { return data[top--]; }
};
```

这样 `Stack<int>` 就是 int 栈，`Stack<string>` 就是 string 栈，一套代码搞定所有类型。

> **参考视频：** 侯捷 C++ 面向对象高级开发（https://www.bilibili.com/video/BV1nL5KzqEZz）
