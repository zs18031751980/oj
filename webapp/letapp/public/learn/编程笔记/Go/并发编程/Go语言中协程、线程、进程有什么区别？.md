# Go语言中协程、线程、进程有什么区别？

> 来源: https://notes.kamacoder.com/go/go_goroutine_thread_process.html

# `# Go语言中协程、线程、进程有什么区别？ 

协程和线程和进程的区别？ 

## `# 简要回答 
  - 进程是操作系统资源分配的基本单位，拥有独立的内存空间和系统资源。   - 线程是进程内的执行单元，共享进程资源，由操作系统调度。   - 协程是用户态的轻量级线程，由程序自身管理调度，不需要操作系统内核参与，上下文切换开销极小。 

Go 语言的 goroutine 就是一种协程实现，每个 goroutine 初始栈大小仅 2KB，可动态增长，因此能轻松创建成千上万甚至数十万个而不影响性能。 

## `# 详细回答 

进程、线程和协程是不同层次的并发执行单元。 
  - 

进程是操作系统资源分配的基本单位，每个进程有独立的内存空间、文件描述符等资源，进程间通信需要通过 IPC 机制。   - 

线程是进程内的执行单元，共享进程资源，由操作系统内核调度，线程切换需要陷入内核态，开销较大。   - 

协程是用户态的轻量级线程，由程序自身管理调度，不需要操作系统内核参与。 

Go 语言的 goroutine 就是协程的一种实现，每个 goroutine 初始栈大小仅 2KB，在 64 位系统下可动态增长到 1GB。 

goroutine 的调度由 Go 运行时负责，采用 M:N 模型，将多个 goroutine 映射到少量操作系统线程上，上下文切换只需保存少量寄存器状态，开销远小于线程切换。 

## `# 知识图解 

![image](../images/file1.kamacoder.com/i/algo/go_process_thread_coroutine.jpg)
 

## `# 知识扩展 

### `# 面试官可能会追问 

Q1：Go 的 goroutine 是如何实现的？与其他语言的协程有什么区别？ 

A1：Go 的 goroutine 由 Go 运行时实现，基于 **GMP 调度模型**。 

G 代表 goroutine，M 代表操作系统线程，P 代表逻辑处理器。 

每个 P 维护一个本地的 goroutine 队列，当 goroutine 阻塞时，P 会切换去执行其他 goroutine。 

与其他语言的协程（如多数语言的无栈协程 async/await）相比，Go 的 goroutine 是**有栈协程**，且由 Go 运行时**自动调度**，无需开发者手动管理状态机，使用起来更加轻量和透明。 

Q2：goroutine 的调度策略是什么？ 

A2：Go 的 goroutine 调度策略主要包括： 
  - **抢占式调度**：基于信号的异步抢占机制，避免某个 goroutine 长时间占用 CPU；   - **work-stealing（工作窃取）机制**：当某个 P 的本地队列为空时，会从其他 P 的队列或全局队列中“窃取” G 来执行，以此平衡各个 P 的负载；   - **系统调用处理（Handoff 机制）**：当 goroutine 进行阻塞式系统调用时，执行该 G 的 M 会与当前的 P 解绑，P 会寻找或创建新的 M 来继续调度执行队列中的其他 goroutine。这些策略共同保证了 Go 程序的高效并发执行。 

Q3：如何在 Go 中优雅地关闭 goroutine？ 

A3：在 Go 中，优雅关闭 goroutine 的常用方法是使用 `context` 包或 `channel`。 

可以创建一个 `context.WithCancel()` 上下文，当需要关闭 goroutine 时，调用 `cancel()` 函数，goroutine 通过监听 `ctx.Done()` 通道来感知关闭信号并主动退出。 

另一种方法是使用一个专用的关闭信号通道（如 `chan struct{}`），当需要关闭时，向通道发送信号或关闭该通道，goroutine 监听该通道并执行清理逻辑后退出。
