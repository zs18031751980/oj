# Goroutine的创建数量存在限制吗？主要限制因素是什么？

> 来源: https://notes.kamacoder.com/go/go_goroutine_limits.html

# `# Goroutine的创建数量存在限制吗？主要限制因素是什么？ 

请谈谈 Go 语言中 goroutine 的创建数量是否存在限制？其背后的主要限制因素是什么？ 

## `# 简要回答 

Go 语言中 goroutine 的创建数量没有固定的上限，但存在实际的物理和程序配置限制。 主要限制因素包括： 
  - **内存资源**：每个 goroutine 初始栈大小约 2KB，会随需要动态增长。   - **调度器的性能**：过多 goroutine 会增加调度和垃圾回收（GC）的开销。   - **操作系统的线程限制**：Go 的 M:N 调度模型会将 goroutine 映射到系统线程上，Go 运行时默认限制最多创建 10000 个操作系统线程。 

## `# 详细回答 

Go 语言中 goroutine 的创建数量没有固定的上限，但存在实际限制。主要限制因素包括： 
  - **内存资源**：每个 goroutine 初始栈大小约 2KB，会根据需要动态增长。在 64 位系统中，最大栈限制通常为 1GB（32 位系统中为 250MB）。如果无节制地创建大量 goroutine（例如百万级别），会消耗数十 GB 的内存，当内存耗尽（OOM）时会导致程序崩溃。   - **调度器性能**：Go 的调度器采用 M:N 模型，将 M 个 goroutine 映射到 N 个系统线程（通过 P，即逻辑处理器）。当活动 goroutine 数量极为庞大时，虽然上下文切换比系统线程轻量，但仍会增加调度器的负担，并且会显著增加垃圾回收（GC）扫描 goroutine 栈的延迟，从而导致性能下降。   - **操作系统线程限制**：虽然 goroutine 是轻量级的，但最终需要被调度到系统线程（M）上执行。Go 运行时（runtime）默认限制一个 Go 程序最多只能创建 **10000** 个操作系统线程（可以通过 `runtime/debug.SetMaxThreads` 修改）。如果因为阻塞操作导致创建的系统线程超过这个限制，程序也会崩溃。 

在实际应用中，通常建议 goroutine 数量控制在合理范围内，避免过度消耗资源。 

## `# 知识图解 

![image](../images/file1.kamacoder.com/i/algo/go_goroutine_limits.jpg)
 

## `# 知识扩展 

### `# 面试官可能会追问： 

Q1：如何控制 goroutine 的数量？ 

A1：可以通过使用带缓冲的 channel（Worker Pool 模式）来控制并发执行的 goroutine 数量。例如，创建一个缓冲大小为 N 的 channel，在启动执行逻辑前向 channel 发送一个占位值，在逻辑结束后从 channel 接收（释放）该值。这样可以保证同时活跃的 goroutine 数量不超过 N。也可以使用第三方协程池库（如 `ants`）。 

Q2：goroutine 的栈大小是多少？ 

A2：在 Go 1.4 及以后版本中，goroutine 的初始栈大小为 2KB，会根据需要动态增长或收缩。当 goroutine 需要更多栈空间时，Go 的运行时会自动分配更大的连续内存并拷贝原有栈数据进行扩展；最大限制在 64 位架构下为 1GB，32 位架构下为 250MB。 

Q3：如何优雅地关闭 goroutine？ 

A3：优雅关闭 goroutine 通常需要传递**退出信号**，主要方式有： 
  - **使用 `context` 标准库**（推荐）：通过 `context.WithCancel`、`WithTimeout` 等衍生出 ctx，在 goroutine 内部监听 `ctx.Done()`，一旦接收到取消信号就执行清理工作并退出。   - **使用 `channel`**：专门创建一个 `done` 通道，当需要关闭 goroutine 时关闭该通道（`close(done)`），goroutine 内部通过 `select` 监听该通道实现优雅退出。
