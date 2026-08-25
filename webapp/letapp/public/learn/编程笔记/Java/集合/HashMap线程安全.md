# HashMap线程安全

> 来源: https://notes.kamacoder.com/java/hashmap-thread-safety.html

# `# HashMap线程安全 

## `# 简要回答 
  - HashMap为什么是线程不安全的？

    - HashMap的**操作不是原子的**，多个线程操作一个HashMap对象时，可能会导致数据不一致,并发修改异常。   - 如何实现线程安全？

    - 使用**Collections.synchronizedMap()** 方法，返回一个线程安全的Map对象。     - 使用**ConcurrentHashMap**类，它是线程安全的。     - 使用**锁机制**，在HashMap的操作中加显式锁。 

## `# 详细回答 
  - HashMap存在的问题

    - JDK1.7 采用数组+链表的数据结构，在多线程背景下，**数组扩容时可能会导致Entry链死循环**。     - HashMap并发执行**put()操作时会出现数据覆盖问题**，因为put()方法没有加锁，多线程环境可能会出现数据覆盖问题。     - HashMap的迭代器是快速失败迭代器，**并发修改会破坏迭代器的遍历逻辑**，导致数据不一致。   - 实现HashMap线程安全的方法 
  - 使用**Collections.synchronizedMap()方法**，通过该方法创建一个线程安全的HashMap对象，返回一个同步的Map包装器，使所有对Map的操作都同步执行。 

```
Map<String,String> synchronizedMap = Collections.synchronizedMap(new HashMap<>());

```

 
  - 使用**ConcurrentHashMap**类，它专门设计用于多线程环境的哈希表实现。它使用分段锁机制，允许多个线程同时进行读操作，提高并发性能。 

```
Map<String,String> concurrentHashMap = new ConcurrentHashMap<>();

```

 
  - 使用**锁机制**，在HashMap的操作中加显式锁（如ReentrantLock）来保证线程安全。 

```
Map<String,String> map = new HashMap<>();
ReentrantLock lock = new ReentrantLock();

// 在需要线程安全的操作中使用锁
lock.lock();
try {
    // 进行线程安全的操作
} finally {
    lock.unlock();
}

```

 

## `# 知识图解 
  - HashMap死循环形成图解
![image](../images/file1.kamacoder.com/i/bagu/20250905HashMap_safety.jpg)
 

## `# 知识扩展 
  - 扩展

    - 并发编程的3个核心特性：**原子性、可见性、有序性**。     - 迭代器设计模式：

      - 快速失败：迭代器实时检查modCount，一旦发现并发修改就抛出异常，实现强一致性，牺牲并发性能。       - 弱一致性：允许并发修改，迭代器可能不是最新的，支持高并发。   - 面试官可能追问： 
  - Q1：你能从并发编程的角度解释一下HashMap为什么是线程不安全的吗？

    - **原子性**：HashMap的put()方法不是原子操作，并发时会被中断，导致数据覆盖。     - **可见性**：HashMap的modCount数组元素等共享变量未使用volatile修饰，线程A修改后，线程B可能看到旧值，导致迭代器判断错误。     - **有序性**：HashMap红黑树的插入/删除有复杂的指针操作，并发时指令重排序可能会破坏树结构。   - Q2：如果需要“强一致性”的线程安全Map，应该使用什么？

    - 选Collections.synchronizedMap()方法。     - 在ConcurrentHashMap的迭代前后手动加锁。   - Q3："读多写少"的场景下，适合使用哪种线程安全的容器存储键值对？

    - 适合使用ConcurrentHashMap，其**读操作无锁，写操作加桶级锁**，“读多写少”的场景下，ConcurrentHashMap几乎无竞争，性能好。   - Q4：为什么ConcurrentHashMap不支持键为null？但是HashMap支持？

    - 在单线程场景下，null的hash值为0可以正常存储，但ConcurrentHashMap是并发容器，若允许null，调用get()方法时返回null，**无法区分键不存在还是键存在但是值为null**，导致并发场景下的逻辑错误。
