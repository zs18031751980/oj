# 哪些操作会导致Goroutine阻塞？调度器会怎么做？

> 来源: https://notes.kamacoder.com/go/go_goroutine_blocked.html

# `# 哪些操作会导致Goroutine阻塞？调度器会怎么做？ 

Go语言中，哪些操作或场景会导致Goroutine发生阻塞？当一个Goroutine发生阻塞时，Go调度器会怎么做？ 

## `# 简要回答 

Go 中导致 Goroutine 阻塞的常见场景包括：等待 channel 操作、等待锁（互斥锁 / 读写锁）、系统调用、网络 I/O 操作、time.Sleep、select 语句等。 

当 Goroutine 阻塞时，Go 调度器的处理方式取决于阻塞的类型： 
  - **仅阻塞 G，不阻塞 M**：调度器会将该 Goroutine 挂起，把它从当前 M 上移除，然后让当前 M 继续从 P 的本地队列或全局队列中获取其他就绪的 Goroutine 执行。   - **同时阻塞 G 和 M：Go 的系统监控会介入，将当前的 P 与被阻塞的 M 分离，并把 P 交给其他空闲的 M 或新建一个 M 去继续执行队列中的其他任务，以此保证 CPU 资源不被浪费。 

## `# 详细回答 

Go 中导致 Goroutine 阻塞的常见场景及底层机制区别如下： 
  - **Channel 操作**：发送或接收 channel 时，如果 channel 未准备好，Goroutine 会主动调用 `gopark` 挂起自身。   - **锁操作**：获取互斥锁（`sync.Mutex`）或读写锁（`sync.RWMutex`）时，如果锁已被持有，当前 Goroutine 会被加入等待队列并阻塞。   - **网络 I/O**：Go 运行时的**网络轮询器使用底层的异步 I/O。进行网络调用时，Goroutine 会在 Netpoller 中等待，但不会阻塞底层系统线程 M**。   - **同步系统调用**：如传统的文件 I/O、CGO 调用等。这类操作不仅会阻塞 Goroutine，**还会导致底层的操作系统线程 M 一起被阻塞**。   - **time.Sleep**：主动让 Goroutine 休眠，它会被加入到调度器的定时器堆中等待唤醒。   - **select 语句**：当所有 case 都不满足且没有 default 分支时，Goroutine 会阻塞等待直至任一 case 就绪。   - **同步原语**：如 `sync.WaitGroup` 的 Wait、`sync.Cond` 的 Wait 等。 

**当 Goroutine 阻塞时，Go 调度器的具体应对机制：** 
  - **异步阻塞（非 M 阻塞）**：调度器轻量级地解除 G 与 M 的绑定，M 会继续留在 P 上，并从 P 的本地队列、全局队列，或者通过 **work-stealing 机制**从其他 P 窃取 Goroutine 来执行。   - **同步阻塞（M 被阻塞）**：调度器的后台监控线程一旦发现某个 M 因系统调用阻塞过长，就会强制将 M 和 P 解绑。P 会带走它的本地任务队列，寻找到一个新的或者空闲的 M 继续执行。当原来的系统调用结束时，原来的 G 会尝试获取一个空闲的 P 恢复执行，如果获取不到，就会被放入全局队列等待。 

## `# 知识图解 

![image](../images/file1.kamacoder.com/i/algo/go_goroutine_blocking.png)
 

## `# 知识扩展 

Go 的调度器采用了 G-M-P 模型，其中 G 代表 Goroutine，M 代表操作系统线程，P 代表逻辑处理器。每个 P 都有一个本地队列，用于存放就绪的 Goroutine。为了保证高并发和资源的最大化利用，Go 运行时大量使用了 `gopark`（挂起）和 `goready`（唤醒）机制来管理处于上述阻塞状态的 Goroutine。 

### `# 面试官可能会追问 

Q1：Go 的 G-M-P 模型是什么？ 

A1：Go 的 G-M-P 模型是 Go 调度器的核心，其中 G 代表 Goroutine，M 代表操作系统线程，P 代表逻辑处理器。每个 P 维护一个本地的 Goroutine 就绪队列。M 必须绑定一个 P 才能执行 Goroutine代码。P 的数量由环境变量 `GOMAXPROCS` 决定，通常等于 CPU 核心数。这种模型通过 P 实现了对并发执行上下文的管理，大幅减少了 M 之间的锁竞争。 

Q2：Go 的 work-stealing 机制是什么？ 

A2：Go 的 work-stealing 机制是调度器的一种负载均衡策略。当当前 P 的本地队列执行为空，且全局队列也没有可运行的 Goroutine 时，该 P 会尝试从其他 P 的本地队列中窃取 Goroutine。为了减少与被窃取 P 之间的锁竞争，**窃取操作通常从目标 P 队列的尾部拿走一半的 Goroutine**。这种机制确保了所有的 CPU 核心都在尽力工作，避免“一核有难，多核围观”的现象。 

Q3：Go 的调度器如何处理锁操作？ 

A3：当 Goroutine 获取锁时，如果锁已被其他 Goroutine 持有，Goroutine 会被阻塞。此时，Go 调度器会将其从当前 M 上移除，然后从 P 的本地队列或全局队列中选择一个就绪的 Goroutine 继续执行。当锁被释放时，被阻塞的 Goroutine 会被重新放入就绪队列中等待执行。
