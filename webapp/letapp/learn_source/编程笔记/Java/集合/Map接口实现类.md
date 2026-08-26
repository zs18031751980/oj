# Map接口实现类

> 来源: https://notes.kamacoder.com/java/map-implementations.html

# `# Map接口实现类 

## `# 简要回答 
  - **`HashMap`**: HashMap是基于哈希表实现的，可以提供快速的键值对存取，但是不保证迭代顺序。它允许 `null` 键和 `null` 值，但它是非线程安全的。   - **`LinkedHashMap`**: LinkedHashMap继承自 `HashMap`，它通过内部维护的双向链表来维护元素的插入顺序或访问顺序。LinkedHashMap也允许 `null` 键和 `null` 值，但它也是非线程安全的。   - **`TreeMap`**: TreeMap是基于红黑树实现的，它按照键的自然顺序 或者是 自定义的比较器进行排序。TreeMap并不允许 `null` 键，它也是非线程安全的。   - **`ConcurrentHashMap`**: ConcurrentHashMap是目前常用的高性能的线程安全 `Map`。它通过分段锁（JDK 1.7）或 CAS + `synchronized`（JDK 1.8+）来实现并发控制。ConcurrentHashMap不允许 `null` 键。   - **`Hashtable`**: Hashtable算是比较传统的线程安全 `Map`，它的所有操作都通过 `synchronized` 关键字同步，因此性能较低。Hashtable既不允许 `null` 键，也不允许 `null` 值。   - **`Properties`**: 它是 `Hashtable` 的子类，主要用于读写键和值都是 `String` 类型的配置文件。  

## `# 详细回答 
  - **HashMap** :

    - **底层数据结构：**  

① 在 **JDK 1.8 之前**，`HashMap` 的底层就是**数组 + 链表**。  

② 在 **JDK 1.8 及之后**，如果table数组中某一条链表的元素个数达到或超过了**TREEIFY_THRESHOLD**（默认是8），并且table数组的长度达到或超过了**MIN_TREEIFY_CAPACITY**（**默认是64**），底层就会对该链表进行树化，将其转化为一棵红黑树。当红黑树的节点数量减少到 6 时，则会又退化为链表。     - **核心特性：**  

① **无序性：** HashMap不保证键值对的迭代顺序。  

② **允许 `null` 键和 `null` 值：** HashMap允许有 `null` 键但最多只能有一个 `null` 键，`null` 值可以同时存在多个。  

③ **非线程安全：** 在多线程环境下并发修改 `HashMap` 可能导致数据不一致 或者 出现 `ConcurrentModificationException`。     - **时间复杂度：**  

① 在**理想的哈希分布**下，HashMap的 `put()`, `get()`, `remove()` 等操作的平均时间复杂度均为 **O(1)** 。  

② 在**最坏**情况下（例如所有键的哈希值都相同，导致链表过长），这时时间复杂度会退化为 **O(N)** ，但 JDK 1.8 引入红黑树后，这种情况的概率大大降低。     - **适用场景：**  

① **绝大多数需要存储键值对的场景。** 它是 Java 中使用最广泛的 `Map` 实现。  

② 不需要保持元素插入顺序或对键进行排序的场景。   - **LinkedHashMap** :

    - **底层数据结构：**  

① `LinkedHashMap` 继承自 `HashMap`，因此其底层也基于 **数组 + 链表/红黑树**（同 JDK 1.8+ 的 `HashMap`）。  

② 在此基础上，`LinkedHashMap` 额外维护了一个**双向链表**，这个链表连接了 `Map` 中所有的键值对（Entry 或 Node），从而能够保持元素的特定顺序。     - **核心特性：**  

① **保持插入顺序（默认）：** 默认情况下，迭代器会按照元素插入的顺序返回键值对。  

② **保持访问顺序（LRU 策略）：** 可以通过构造函数设置 `accessOrder` 参数为 `true`，使其按照元素的最近访问顺序（即 LRU 策略，最近访问的元素会被移到链表末尾）进行排序。  

③ **允许 `null` 键和 `null` 值：** 同 `HashMap`。  

④ **非线程安全：** 同 `HashMap`。     - **时间复杂度：**  

① `put()`, `get()`, `remove()` 等操作的平均时间复杂度为 **O(1)** 。链表的维护操作对性能影响很小。     - **适用场景：**  

① **需要保持元素插入顺序的缓存或处理队列。**  

② **实现 LRU (Least Recently Used) 缓存策略：** 通过重写 `removeEldestEntry` 方法，可以在 `Map` 达到指定容量上限时自动移除最不常用的元素，非常适合作为固定大小的缓存。   - **TreeMap** :

    - **底层数据结构：**  

① `TreeMap` 的底层是基于**红黑树（Red-Black Tree）**实现的。红黑树是一种自平衡的二叉查找树，它能保证树的高度保持对数级别，从而提供稳定的性能。     - **核心特性：**  

① **按键排序：** 键值对会根据键的自然顺序（即键类必须实现 `Comparable` 接口）或在构造时提供的 `Comparator` 进行排序。  

② **不允许 `null` 键：** 因为需要对键进行比较操作来确定其在树中的位置，而 `null` 无法参与比较，所以 `TreeMap` 不允许 `null` 键。  

③ **允许 `null` 值：** 可以有多个 `null` 值。  

④ **非线程安全：** 同 `HashMap`。     - **时间复杂度：**  

① `put()`, `get()`, `remove()` 等操作的时间复杂度为 **O(logN)** ，其中 N 是 `Map` 中元素的数量。这是因为红黑树的高度是 O(logN)。     - **适用场景：**  

① **需要对键进行排序的场景。** 例如，按字母顺序存储用户，按日期存储事件，或者需要获取某个范围内的键值对。  

② **需要执行范围查询（如 `subMap()`、`headMap()`、`tailMap()`）的场景。**  

③ 需要高效地查找最小/最大键、或键的最近邻居的场景。   - **ConcurrentHashMap** :

    - **底层数据结构：**  

① **JDK 1.7 及之前：** 采用**分段锁（Segment）**的机制。`ConcurrentHashMap` 内部维护一个 `Segment` 数组，每个 `Segment` 都是一个独立的 `ReentrantLock`，并管理着一个哈希表（类似于 `HashMap`）。通过对不同的 `Segment` 加锁，实现了对 `Map` 的分段并发控制，降低了锁的粒度。  

② **JDK 1.8 及之后（包括 JDK 17.0）：** 放弃了 `Segment` 概念，改用 **CAS (Compare And Swap) + `synchronized` 关键字**（针对哈希桶的头节点）+ **数组 + 链表/红黑树**。在链表/红黑树的头节点上使用 `synchronized` 锁，进一步降低了锁的粒度，提高了并发性能。读操作通常不需要加锁，写操作只锁住当前操作的哈希桶。     - **核心特性：**  

① **高性能线程安全：** 提供了比 `Hashtable` 更好的并发性能，读操作通常不需要加锁。  

② **不允许 `null` 键：** 但允许 `null` 值（JDK 8+）。  

③ **无序：** 不保证迭代顺序。     - **时间复杂度：**  

① `put()`, `get()`, `remove()` 等操作的平均时间复杂度为 **O(1)** 。     - **适用场景：**  

① **高并发环境下需要线程安全的键值对存储。** 例如，共享缓存、会话管理、计数器等。它是现代 Java 并发编程中 `Map` 的首选。   - **Hashtable** :

    - **底层数据结构：**  

① `Hashtable` 的底层基于**数组 + 链表**，与 JDK 1.8 之前的 `HashMap` 类似。     - **核心特性：**  

① **线程安全：** `Hashtable` 的所有公共方法都使用了 `synchronized` 关键字进行修饰，这意味着在任何时候只有一个线程可以访问 `Hashtable` 的方法。这种**粗粒度的全表锁**机制保证了线程安全。  

② **不允许 `null` 键和 `null` 值：** 如果尝试插入 `null` 键或 `null` 值，会抛出 `NullPointerException`。  

③ **无序性：** 不保证迭代顺序。     - **时间复杂度：**  

① 在单线程环境下，`put()`, `get()`, `remove()` 等操作的平均时间复杂度为 **O(1)** 。  

② 但在高并发环境下，由于其粗粒度的全表锁，多个线程的竞争会导致严重的性能瓶颈，实际性能会急剧下降。     - **适用场景：**  

① **基本已被淘汰，不推荐在新代码中使用。** 主要出现在一些遗留系统中，现代应用应优先选择 `ConcurrentHashMap`。   - **Properties** :

    - **底层数据结构：**  

① `Properties` 类继承自 `Hashtable`。     - **核心特性：**  

① **键和值都必须是 `String` 类型：** 这是 `Properties` 最显著的特点，它专门设计用于存储字符串类型的键值对。  

② **常用于与 I/O 流结合：** 提供了 `load()` 和 `store()` 方法，可以直接从输入流加载键值对或将键值对保存到输出流，通常用于读写 `.properties` 文件。  

③ **线程安全：** 由于继承自 `Hashtable`，它也具备线程安全特性，但同样面临性能瓶颈。     - **时间复杂度：**  

① 同 `Hashtable`，平均时间复杂度为 **O(1)** 。     - **适用场景：**  

① **读写 `.properties` 配置文件：** 这是其最主要的用途，例如存储数据库连接信息、应用程序配置参数等。  

## `# 知识图解 
  - **Map类实现类的选择策略**，如下图所示 ；
![image](../images/file1.kamacoder.com/i/bagu/Collection_selecting_strategy.jpg)
   - **Java集合框架体系图**，如下图所示：  
 ![image](../images/file1.kamacoder.com/i/bagu/Collection_framework_simpleV.jpg)
  

## `# 知识拓展 
  - **`Collections.synchronizedMap(Map<K,V> m)`：** 
    - 这是一个工具方法，可以将任何非线程安全的 `Map`（如 `HashMap`、`LinkedHashMap`、`TreeMap`）包装成一个线程安全的 `Map`。     - 它的实现机制是**对传入的 `Map` 对象进行包装，并在每个方法调用时对整个 `Map` 对象加锁**。虽然能提供线程安全，但由于是粗粒度的锁，其并发性能通常不如 `ConcurrentHashMap`。在并发度要求不高的场景下可以使用。   - **`WeakHashMap`：** 
    - 其键是弱引用，当键不再被其他强引用指向时，即使 `WeakHashMap` 中还存有它的引用，垃圾回收器也会回收这个键值对。     - 适用于实现简单的缓存，当内存不足时，可以自动清理不再被引用的键值对，避免内存泄漏。
