# Go语言中select语句的执行机制是怎样的？

> 来源: https://notes.kamacoder.com/go/go_select.html

# `# Go语言中select语句的执行机制是怎样的？ 

select 语句的执行机制是怎样的？当多个 case 同时就绪时，如何选择？ 

## `# 简要回答 

Go 语言的 select 语句用于多路复用，允许在多个 channel 操作中选择一个就绪的执行。它会按顺序评估所有 case 中的表达式，然后阻塞等待至少一个 case 就绪。当多个 case 同时就绪时，Go 运行时会随机选择一个执行，这种随机性避免了饥饿问题。select 语句的执行过程分为评估表达式、阻塞等待和选择执行三个阶段，其中随机性选择是其核心特性之一。 

## `# 详细回答 

Go 语言的 select 语句是实现多路复用的关键机制，用于在多个 channel 操作中选择一个执行。其执行机制可以分为三个阶段：首先，select 会按自上而下、从左到右的顺序评估所有 case 中的表达式（包括 channel 表达式和右侧需要发送的值）；其次，进入阻塞状态，等待至少一个 case 中的 channel 操作可以执行；最后，当有 case 就绪时，选择其中一个执行。 

当多个 case 同时就绪时，Go 运行时会通过伪随机算法选择一个执行，这种随机性是为了避免饥饿问题，确保每个 case 都有机会被执行。需要注意的是，select 语句中的 default case 会在所有其他 case 都未就绪时立即执行，不会阻塞。 

select 语句的这种设计使得 Go 程序能够高效地处理多个并发操作，是 Go 语言并发模型中的重要组成部分。 

## `# 知识图解 

![image](../images/file1.kamacoder.com/i/algo/go_select.jpg)
 

## `# 知识扩展 

在运行时，`select` 的底层执行逻辑主要包含以下几个关键步骤： 
  - **生成轮询顺序和加锁顺序**：为了保证公平性和随机性，Go 运行时会使用内部的伪随机数生成器（`fastrand`）打乱所有 case 的轮询顺序（poll order），同时还会生成一个基于 channel 地址排序的加锁顺序（lock order）以防止死锁。   - **加锁并轮询**：按照加锁顺序锁定所有涉及的 channel，然后按照打乱后的轮询顺序检查每个 case 是否就绪。   - **挂起与唤醒**：如果遍历完所有 case 都没有发现就绪的 channel，且没有 default 分支，当前 Goroutine 会被挂起（park），并加入到所有相关 channel 的等待队列中。直到某个 channel 发生读写操作将其唤醒，才会继续执行后续逻辑。 

需要注意的是，select 语句中的 case 书写顺序不会影响最终的选择结果，因为 Go 会在轮询前主动打乱顺序。此外，select 语句中的 default case 会在所有其他 case 都未就绪时立即执行，从而实现非阻塞操作。 

### `# 面试官可能会追问 

Q1：select 语句中的 case 顺序会影响选择结果吗？ 

A1：select 语句中的 case 书写顺序不会影响最终的选择结果。当多个 case 同时就绪时，Go 会通过伪随机算法选择一个执行，与 case 的代码排列顺序无关。这种设计确保了公平性，防止某个 case 被长期忽略。 

Q2：select 语句中的 case 可以是普通的布尔表达式吗？ 

A2：select 语句中的 case 必须是 channel 的 I/O 操作（发送或接收），不能是普通的布尔表达式。这是 Go 语言的设计决策，select 语句专门用于处理 channel 的并发操作。 

Q3：select 语句中的 case 可以是 nil channel 吗？ 

A3：select 语句中的 case 可以是 nil channel，但对 nil channel 的读写操作会永远阻塞。因此，在 select 中遇到 nil channel 的 case 时，该 case 会被忽略（永远不会就绪）。如果 select 语句中所有的 case 都是 nil channel 且没有 default，程序会永远阻塞（甚至可能引发 deadlock 崩溃）。需要注意的是，在 select 中操作 nil channel 本身不会引发 panic。
