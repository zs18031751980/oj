# new 和 malloc 的区别

> 来源: https://notes.kamacoder.com/cpp/new-vs-malloc.html

# `# new 和 malloc 的区别 

面试官问"new 和 malloc 有什么区别"，很多人能列出几条差异，但追问"new 的底层调用链路是什么""placement new 怎么用""delete[] 为什么不能用 delete 替代"就答不清楚了。这道题的核心是理解：new 做了两件事（分配内存 + 调构造），malloc 只做一件事（分配内存）。 

## `# 简要回答 

`new` 是 C++ 运算符，一次操作完成两件事：先通过 `operator new` 分配内存，再在这块内存上调用构造函数初始化对象。`malloc` 是 C 标准库函数，只负责分配一块指定大小的原始内存，不调用任何构造函数。对应地，`delete` 先调析构再释放内存，`free` 只释放内存不调析构。`new` 失败抛 `bad_alloc` 异常，`malloc` 失败返回 `NULL`。`new` 返回具体类型指针（类型安全），`malloc` 返回 `void*` 需要强转。 

## `# 详细回答 

**new 做了什么** 

`new MyClass(10)` 这一行代码，编译器实际上拆成两步：第一步调用 `operator new(sizeof(MyClass))` 分配内存——这个函数内部通常就是调 `malloc`；第二步在分配到的内存地址上调用 `MyClass` 的构造函数。所以 new 的完整调用链路是：`new` → `operator new` → `malloc` → `mmap`/`brk`（操作系统底层）。 

对应地，`delete obj` 也是两步：先调用 `obj->~MyClass()` 析构函数，再调用 `operator delete(obj)` 释放内存（内部通常调 `free`）。 

**malloc 做了什么** 

`malloc(sizeof(MyClass))` 只做一件事：向操作系统申请一块指定大小的原始内存，返回 `void*` 指针。这块内存里是垃圾值，没有任何初始化。你不能在 malloc 返回的内存上直接当对象用——成员变量没初始化，虚函数表指针没设置，行为是未定义的。 

对应地，`free(obj)` 只释放内存，不调用析构函数。如果对象持有堆内存（比如 `string` 成员），直接 free 会导致内存泄漏。 

**其他关键差异** 

`new` 不需要手动计算大小（编译器自动算 `sizeof`），`malloc` 必须手动传大小参数。`new` 可以被类重载（自定义内存池），`malloc` 不能重载。`new[]` 分配数组时会额外记录元素个数，`delete[]` 根据这个数字批量调析构；如果用 `delete` 代替 `delete[]`，只会析构第一个元素，剩下的全部泄漏。 

![new与malloc调用链路对比](/learn/编程笔记/C++/images/file1.kamacoder.com/i/web/20260523163713_cpp26.png)
 

## `# 知识拓展 

**Q：能不能用 malloc 分配内存后手动调构造函数？** 

可以，用 placement new：`MyClass* obj = new (mem) MyClass(10);`，其中 `mem` 是 malloc 返回的指针。placement new 不分配内存，只在指定地址上调构造函数。析构时也要手动调 `obj->~MyClass()`，然后再 `free(mem)`。内存池就是这么实现的。 

**Q：new 的底层一定调 malloc 吗？** 

不一定。`operator new` 的默认实现通常调 malloc，但你可以重载 `operator new` 用自己的分配器（比如从内存池分配）。标准只要求 `operator new` 返回一块足够大的对齐内存，不规定底层实现。 

**Q：什么时候该用 malloc 而不是 new？** 

和 C 代码交互时（C 没有 new）；分配 POD 类型的原始内存块（比如网络缓冲区 `char*`）；实现自定义内存分配器时。现代 C++ 中，绝大多数场景应该用 new（或者更好的选择：智能指针 + make_shared/make_unique），只有底层系统编程才需要 malloc。 

**Q：delete[] 为什么不能用 delete 替代？** 

`new[]` 分配数组时，编译器会在内存块头部多分配几个字节记录元素个数 N。`delete[]` 读取这个 N，然后循环调用 N 次析构函数，最后释放整块内存。如果用 `delete` 代替，它只调用一次析构（第一个元素），剩下 N-1 个元素的析构函数不会被调用，资源泄漏。对于 POD 类型（没有析构函数）混用不会崩溃，但属于未定义行为，不要这么做。
