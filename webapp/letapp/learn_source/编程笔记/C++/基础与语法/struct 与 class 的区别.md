# struct 与 class 的区别

> 来源: https://notes.kamacoder.com/cpp/struct-vs-class.html

# `# struct 与 class 的区别 

面试官问"struct 和 class 有什么区别"，大多数人只答出"默认访问权限不同"就停了。但面试官往往会追问：继承时默认权限呢？模板参数里能用 struct 吗？实际项目中怎么选？能把这几层都答清楚，才算完整。 

## `# 简要回答 

C++ 中 struct 和 class 在语法能力上完全等价，区别只有两个默认行为：struct 成员和继承默认 public，class 默认 private。另外模板参数只能用 `class` 或 `typename`，不能用 `struct`。工程惯例上，struct 用于纯数据聚合，class 用于有封装行为的类型。 

## `# 详细回答 

**语法层面的区别（只有三点）** 

**第一，默认成员访问权限不同。** struct 的成员默认 public，外部可以直接访问；class 的成员默认 private，必须通过公开接口访问。但两者都可以显式写 `public`/`protected`/`private`，所以这只是默认值的差异，不是能力的差异。 

**第二，默认继承权限不同。** `struct Derived : Base` 默认是 public 继承，`class Derived : Base` 默认是 private 继承。private 继承会导致基类的 public 成员在派生类外部不可访问。实际写代码时都会显式写继承权限，不依赖默认行为。 

**第三，模板参数声明。** `template<class T>` 或 `template<typename T>` 都合法，但不能写 `template<struct T>`。这是语法规定，和 struct/class 的语义无关。 

**工程惯例（非语法强制）** 
  - **struct**：纯数据聚合，所有成员 public，没有不变量需要维护。典型场景：配置项、坐标点、网络协议包头、POD 类型。   - **class**：有封装需求，内部状态需要通过接口维护不变量。典型场景：业务对象、资源管理器、带构造/析构逻辑的类型。 

这个惯例不是编译器强制的，但团队代码风格一致性很重要——看到 struct 就知道"这是个透明的数据包"，看到 class 就知道"这里有封装逻辑"。 

![struct与class访问控制对比](../images/file1.kamacoder.com/i/web/20260525123930_cpp43.png)
 

## `# 知识拓展 

**Q：struct 里能写 private 成员吗？** 

能。struct 和 class 语法能力完全一样，只是默认值不同。你可以在 struct 里写 private、写构造函数、写虚函数，编译器不会阻止。但这样做违反工程惯例，会让读代码的人困惑。 

**Q：什么是 POD 类型？和 struct 什么关系？** 

POD（Plain Old Data）是指内存布局与 C 兼容的类型：没有虚函数、没有用户定义的构造/析构、所有成员 public、可以用 `memcpy` 安全拷贝。struct 天然适合定义 POD，因为默认 public 且语义上暗示"纯数据"。但 class 也能定义 POD，只要满足条件就行。 

**Q：C 的 struct 和 C++ 的 struct 有什么区别？** 

C 的 struct 只能有成员变量，不能有成员函数、访问控制、继承。C++ 为了兼容保留了 struct 关键字，但扩展成了和 class 几乎等价的东西。用 `extern "C"` 混编时，共享的结构体定义要保持 C 兼容（不加成员函数和继承）。 

**Q：为什么实际项目中很少看到 struct 继承？** 

因为 struct 的语义是"纯数据聚合"，继承暗示多态和行为扩展，两者语义冲突。如果需要继承体系，用 class 更符合意图表达。Google C++ Style Guide 明确建议：只有当所有成员都是 public 且没有虚函数时才用 struct。
