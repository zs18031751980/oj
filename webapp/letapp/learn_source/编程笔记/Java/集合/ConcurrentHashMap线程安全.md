# ConcurrentHashMap线程安全

> 来源: https://notes.kamacoder.com/java/concurrenthashmap-thread-safety.html

# `# ConcurrentHashMap线程安全 

## `# 简要回答 
  - ConcurrentHashMap在JDK1.7中使用**数组+链表**的结构，数组分为大数组**Segment**和小数组**HashEntry**。ConcurrentHashMap的线程安全主要通过**Segment加ReentrantLock**来实现的。   - 在JDK1.8中，ConcurrentHashMap使用**数组+链表+红黑树**的结构,通过**CAS操作或者synchronized**来保证线程安全，缩小了锁的粒度，从而提高并发性能。 

## `# 详细回答 
  - JDK1.7

    - ConcurrentHashMap**分段锁技术**：将数据分成一段一段存储，每一段数据配一把锁，当一个线程占用锁访问其中一个段数据时，其他段的数据也能被其他线程访问，实现并发访问。     - 对每个**Segment独立加锁（继承ReentrantLock）**，小数组HashEntry用于存储键值对数据。ConcurrentHashMap包含Segment数组，Segment包含HashEntry数组，HashEntry是链表结构的元素,**并发度为Segment的数量**。     - 读写操作：**读操作**无锁，volatile保证可见性，根据HashEntry的volatile字段保证读操作能获取最新值。**写操作**对目标加锁，完成后释放，同一Segment写操作互斥。   - JDK1.8

    - 通过**CAS/局部synchronized**实现线程安全。     - ConcurrentHashMap对**头结点加锁**保证线程安全，锁粒度变小，发生冲突和加锁频率降低，并发操作性能提高。     - 添加元素时：判断容器是否为空，如果为空利用CAS设置该节点；如果不为空则使用synchronized，遍历桶中的数据，替换或新增节点到桶中，最后再判断是否需要转为红黑树，这样可以保证并发访问时的线程安全。     - 读写操作：**读操作**无锁，通过volatile保证可见性，支持并发读。**写操作**采用上述方法实现线程安全。 

## `# 适用场景 

| 版本  锁机制  优势 
| JDK1.7  分段锁Segment  实现简单，适合中等并发 
| JDK1.8  CAS+局部synchronized  锁粒度更高，高并发性能好 

## `# 代码示例 

```
import java.util.concurrent.ConcurrentHashMap;

public class ConcurrentHashMapDemo {
    public static void main(String[] args) throws InterruptedException {
        // 创建ConcurrentHashMap实例
        ConcurrentHashMap<String, Integer> concurrentMap = new ConcurrentHashMap<>();

        // 添加元素
        concurrentMap.put("apple", 10);
        concurrentMap.put("banana", 20);

        // 并发场景：启动两个线程同时操作map
        Thread thread1 = new Thread(() -> {
            // 原子操作：如果key不存在则添加
            concurrentMap.putIfAbsent("orange", 15);
            // 原子操作：更新值（将banana的数量加5）
            concurrentMap.computeIfPresent("banana", (k, v) -> v + 5);
        });

        Thread thread2 = new Thread(() -> {
            // 原子操作：获取并移除元素
            Integer value = concurrentMap.remove("apple");
            System.out.println("Thread2 移除了 apple: " + value);
        });

        // 启动线程
        thread1.start();
        thread2.start();
        // 等待线程执行完毕
        thread1.join();
        thread2.join();

        // 输出最终结果
        System.out.println("最终映射: " + concurrentMap);
    }
}
// 结果：
// Thread1 移除了 apple: 10
// 最终映射: {orange=15, banana=25}
// 若使用HashMap,可能会出现异常或者丢失数据

```

 

## `# 知识图解 
  - JDK1.7分段锁机制示意
![image](../images/file1.kamacoder.com/i/bagu/20250907ConcurrentHashMap.jpg)
 

## `# 知识扩展 
  - 面试官可能追问： 
  - Q1：JDK1.7的分段锁为什么早在JDK1.8被弃用了？

    - 分段锁的并发读度会受到**Segment数量限制**（默认为16）,高并发下仍有竞争。     - 每个Segment是独立哈希表，包含数组、链表等，**内存开销大**。     - **JDK1.8使用更细粒度的锁**，并发度理论上与数组长度相等，性能更好。   - Q2:JDK1.8中synchronized锁的是什么？为什么不直接使用ReentrantLock？

    - 锁的是哈希桶数组中某个索引位置的**头节点**，仅影响当前冲突链，锁粒度极小。     - synchronized在JDK1.6新增了**锁升级机制**后，性能与ReentrantLock基本相同，且更轻量级，更适合这种局部短时间锁定场景。   - Q3:CAS操作具体会用在哪里？失败了会怎么样？

    - 用于初始化哈希桶，数组索引为空时插入第一个节点，修改节点值，标记扩容状态等无锁场景。     - CAS失败时会自旋重试（有限次数），仍失败则退化为加锁，避免无限循环浪费CPU。   - Q4:扩容时怎么保证线程安全？会不会丢失数据？

    - 扩容时通过volatile标记状态，多线程协同扩容时，每个线程负责迁移一部分哈希桶，通过**CAS标记已迁移的索引**，避免重复操作。     - **写入操作会先协助完成扩容**，再执行插入，确保数据不会丢失。
