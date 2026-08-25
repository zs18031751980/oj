# volatile关键字的作用

> 来源: https://notes.kamacoder.com/cpp/volatile-keyword.html

# `# volatile关键字的作用 

面试官问："volatile关键字是干什么的？它能保证线程安全吗？" 

这题在嵌入式和后端面试里都常见。很多人能答出"防止编译器优化"，但说不清具体防止了哪种优化，更答不上volatile和std::atomic的本质区别。 

## `# 简要回答 

volatile告诉编译器：**这个变量的值可能被程序之外的因素修改**（硬件寄存器、中断服务程序等），所以**每次访问都必须从内存读取，不能用寄存器里的缓存值**。 

核心作用就一个：**禁止编译器对该变量的读写做优化**。 

## `# 详细回答 

**编译器优化的问题** 

正常情况下，编译器看到一个变量在两次读取之间没有写操作，会认为"值没变"，直接用寄存器里缓存的旧值代替第二次内存读取。对普通变量这没问题，但对硬件寄存器或被ISR修改的变量就错了——值确实在程序不知情的情况下变了。 

**volatile做了什么** 
  - 禁止编译器把变量缓存到寄存器，**每次读写都走内存**   - 禁止编译器重排与volatile变量相关的指令（仅限编译器层面，CPU重排需要内存屏障）   - 禁止编译器把对volatile变量的读写当作"无效操作"消除 

**典型场景** 

硬件寄存器映射：`volatile uint32_t* reg = (volatile uint32_t*)0x4000;`，硬件随时改值，不加volatile编译器会把第二次读取优化掉。 

ISR修改的全局变量：主程序轮询一个flag，ISR里置flag为1。不加volatile，编译器可能把flag缓存到寄存器，主程序永远看不到ISR的修改。 

**volatile不能做什么** 

volatile**不保证原子性**，也**不保证内存顺序**。`volatile int i; i++;` 仍然是读-改-写三步，多线程下照样出问题。多线程同步必须用`std::atomic`。 

![volatile关键字作用](../images/file1.kamacoder.com/i/web/20260525123939_cpp49.png)
 

## `# 知识拓展 

面试官可能追问： 

**Q1: volatile能保证原子性吗？** 

不能。volatile只保证每次读写都走内存，但`i++`仍然是读、加、写三步操作。多线程下两个线程可能同时读到旧值，各自加1写回，结果只加了1而不是2。要原子性必须用`std::atomic`。 

**Q2: volatile和std::atomic有什么区别？** 

三个维度：原子性——atomic保证，volatile不保证；内存顺序——atomic可以指定memory_order控制CPU重排，volatile只阻止编译器重排；用途——volatile用于硬件交互和ISR通信，atomic用于多线程同步。 

**Q3: volatile和const能同时用吗？** 

能。`const volatile uint32_t* status_reg;` 表示"程序不能写这个地址（const），但值可能被硬件改（volatile）"。典型场景是只读的硬件状态寄存器。 

**Q4: 多线程里用volatile代替锁行不行？** 

不行。volatile既不保证原子性，也不提供内存屏障。在现代C++里，多线程共享变量要么用`std::atomic`，要么用互斥锁保护。用volatile做多线程同步是历史遗留的错误做法。
