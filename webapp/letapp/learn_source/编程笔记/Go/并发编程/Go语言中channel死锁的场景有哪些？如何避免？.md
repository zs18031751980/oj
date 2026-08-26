# Go语言中channel死锁的场景有哪些？如何避免？

> 来源: https://notes.kamacoder.com/go/go_deadlock.html

# `# Go语言中channel死锁的场景有哪些？如何避免？ 

Go 语言中的 “死锁”一般指什么？有哪些通用的避免策略？ 

## `# 简要回答 

Go 语言中的死锁是指**多个 goroutine 互相等待对方释放资源**，导致所有或部分 goroutine 都无法继续执行的状态。 

死锁通常发生在 goroutine 之间形成循环依赖时。 

## `# 详细回答 

Go 语言中的死锁是指**多个 goroutine 互相等待对方释放资源**，导致相关 goroutine 都无法继续执行的状态。 

死锁通常发生在 goroutine 之间形成循环依赖时，例如 goroutine A 等待 goroutine B 释放资源，而 goroutine B 又等待 goroutine A 释放资源。 

避免死锁的通用策略包括： 
  - 保持锁的获取顺序一致，所有 goroutine 都按照相同的顺序获取锁；   - 避免嵌套锁，减少锁的持有时间；   - 使用带超时的同步机制，如 context.WithTimeout 或 time.After 配合 select 语句；   - 避免 goroutine 之间的循环依赖；   - 使用缓冲 channel 减少阻塞。 

## `# 知识图解 

![image](../images/file1.kamacoder.com/i/algo/go_deadlock1.jpg)
 

## `# 知识扩展 

Go 语言的死锁检测机制是通过运行时的死锁检测系统实现的。当程序发生死锁时，Go 运行时会检测到这种情况并打印死锁信息，包括死锁的 goroutine 数量、每个 goroutine 的状态和调用栈。 

### `# 面试官可能会追问 

Q1：**死锁的四个必要条件是什么？** 

A1：死锁的四个必要条件是互斥条件、请求与保持条件、不可剥夺条件和循环等待条件。 
  - 互斥条件指资源只能被一个进程/协程使用；   - 请求与保持条件指进程在请求新资源时保持已有的资源；   - 不可剥夺条件指资源只能由持有它的进程主动释放；   - 循环等待条件指进程之间形成循环等待资源的关系。 

Q2：**channel 死锁的场景有哪些？** 

A2：基于 channel 的死锁通常发生在一个或多个 goroutine 因为 channel 的发送或接收操作被永久阻塞，且没有其他 goroutine 能够解除这种阻塞状态时。 

Q2：**Go 语言中的死锁和活锁有什么区别？** 

A2：死锁是指 goroutine 被彻底挂起，互相等待资源释放。 

活锁是指 goroutine 并没有被阻塞，反而处于活跃状态，但由于逻辑设计问题陷入了无限的循环重试或状态切换中，无法取得实质性进展。解决活锁通常需要引入随机的退避时间等机制。
