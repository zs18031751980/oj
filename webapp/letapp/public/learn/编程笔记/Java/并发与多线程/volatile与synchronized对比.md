# volatile与synchronized对比

> 来源: https://notes.kamacoder.com/java/volatile-vs-synchronized.html

# `# volatile与synchronized对比 

## `# 简要回答 
  - synchronized是确保**数据的一致性**和**线程安全**，解决多个线程之间访问资源的同步性。而volatile是确保变量在多个线程的**可见性**和**有序性**。   - volatile不需要获取/释放锁，性能较高且轻量级。   - synchronized可以修饰**方法以及代码块**，volatile只能修饰**变量**。 

## `# 详细回答 
  - 机制和用途：

    - synchronized用于提供**线程间的同步机制**，当一个线程进入一个由synchronized修饰的代码块或方法时，它会获取一个**监视器锁**（monitor lock），这保证了同一时间只有一个线程可以执行这段关系代码。     - volatile用于**修饰变量**，当一个线程修改了一个volatile变量的值，其他线程能够**立即看到修改**，还可以**防止指令重排序**。   - 原子性

    - synchronized可以保证被修饰的代码块的**原子性**，这段代码在执行过程中不会被其他线程打断。     - volatile只能保证单个读写操作的原子性，对于复合操作（自增、减）**不能保证原子性**。   - 互斥性

    - synchronized提供了**互斥性**，同一时间只有一个线程可以执行被其修饰的代码块和方法。     - volatile**没有提供互斥性**，它只能保证可见性和有序性。   - 性能

    - synchronized的性能相对较低，因为它需要获取和释放锁。     - volatile的性能较高，因为它不需要获取和释放锁，更加轻量级，不过提供的同步级别较低。   - 使用范围

    - synchronized可以修饰方法以及代码块。     - volatile只能修饰变量。 

## `# 使用场景 

| 需求  选volatile  选synchronized 
| 操作类型  简单无复合  复合、多步操作 
| 原子性  无  有 
| 性能  追求极致性能（轻量）  允许性能损耗（强同步保证） 
| 线程协作  仅状态传递  有协作（如等待/唤醒机制） 

## `# 代码示例 
  - volatile状态标记 

```
private volatile boolean isRunning = true;

// 线程A：修改状态（一次写）
public void stop() { isRunning = false; }

// 线程B/C：读取状态（多次读）
public void work() { while (isRunning) { ... } }

```

 
  - volatile禁止指令重排序 

```
private static volatile Singleton instance;
public static Singleton getInstance() {
    if (instance == null) {
        synchronized (Singleton.class) {
            if (instance == null) {
                instance = new Singleton(); // volatile 禁止此处重排序
            }
        }
    }
    return instance;
}

```

 
  - synchronized保证复合操作原子性 

```
private int count = 0;

// 多线程同时调用，需保证count++的原子性
public synchronized void increment() { count++; }

```

 
  - synchronized多变量 

```
private int total;
private int used;

// 保证total和used的同步更新
public synchronized void allocate(int amount) {
    if (used + amount <= total) {
        used += amount;
        // 其他依赖used和total的操作...
    }
}

```

 
  - volatile和synchronized实现单例模式 

```
public class Singleton {
    // 1. volatile修饰单例引用，禁止指令重排序
    private static volatile Singleton instance;

    // 2. 私有构造器，防止外部实例化
    private Singleton() {}

    // 3. 双重检查锁定获取实例
    public static Singleton getInstance() {
        // 第一次检查：避免不必要的同步（提高性能）
        if (instance == null) {
            // 同步块：保证只有一个线程进入初始化流程
            synchronized (Singleton.class) {
                // 第二次检查：防止多线程并发时重复初始化
                if (instance == null) {
                    // 若不加volatile，可能发生指令重排序导致的问题
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}

```

 

## `# 知识图解 
  - volatile关键字的作用示意图 

![image](../images/file1.kamacoder.com/i/bagu/20250914_volatile.jpg)
 
  - synchronized底层示意图 

![image](../images/file1.kamacoder.com/i/bagu/Monitor.jpg)
 
  - 使用volatile和synchronized的单例模式
![image](../images/file1.kamacoder.com/i/bagu/20250914_volatile_synchronized.jpg)
 

## `# 知识扩展 
  - 面试官可能追问： 
  - Q1：volatile的可见性是通过内存屏障实现的，具体会插入哪些内存屏障？这些内存屏障如何阻止指令重排序？

    - 对于**写操作**，在写操作前插入StoreStore屏障，在写操作后插入StoreLoad屏障。     - 对于**读操作**，在读操作前插入LoadLoad屏障，在读操作后插入LoadStore屏障。   - Q2：当volatile变量和synchronized代码块同时修饰同一变量时，会有冲突吗？执行优先级如何？

    - 当volatile变量和synchronized代码块同时作用于同一变量时，**不会产生冲突**，两者的作用是互补而非对立的。它们的执行逻辑遵循 Java 内存模型（JMM）的规范，存在明确的协作关系而非 “优先级” 之分。   - Q3：synchronized的wait()/notify()机制为什么必须在同步块中使用？volatile能否实现类似的线程间通信？

    - wait()/notify()是synchronized机制中用于线程间协作的核心方法，必须在同步块中使用。     - wait()会**释放锁并且阻塞当前线程**，notify()则会**唤醒一个等待该锁的线程**，二者都基于当前线程有锁的前提。如果不在同步块中调用可能会抛出异常。     - volatile可以实现简单的线程状态传递，无法替代synchronized的线程协作机制，**没有精确唤醒能力以及原子性保证**。   - Q4：双重检锁已经有了synchronized，为什么还要使用volatile？

    - 第一行代码不在同步代码块之内，可能会出现对象地址不为空，内容为空情况。     - 代码在编译运行时可能会出现重排序，在多线程环境下可能会出现报错。
