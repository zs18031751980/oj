# ArrayList与LinkedList的区别

> 来源: https://notes.kamacoder.com/java/arraylist-vs-linkedlist.html

# `# ArrayList与LinkedList的区别 

## `# 简要回答 

### `# ArrayList 和 LinkedList 的概念 
  - **`ArrayList`** ：

    - **定义**：是`java.util` 包下的一个类，是 `List` 接口的实现，提供了可变长度的列表功能。     - **底层实现**：基于**动态数组**（`Object[]` 数组）实现。   - **`LinkedList`** ：

    - **定义**：是 `java.util` 包下的一个类，是 `List` 接口的实现，同时实现了 `Deque`（双端队列）接口。     - **底层实现**：基于**双向链表**实现。 

### `# ArrayList 和 LinkedList 的区别 
  - 

如下表所示： 

| 维度  `ArrayList`(基于数组)  `LinkedList`(基于双向链表) 
| **底层数据结构**  `Object[]` 数组  双向链表（每个节点存储数据、前驱和后继指针） 
| **随机访问**  **高效** (O(1))，通过索引直接定位。  **低效** (O(n))，需要从头或尾遍历。 
| **中间增删**  **低效** (O(n))，需要移动大量元素。  **高效** (O(1)，找到位置后)，只需修改指针。 
| **首尾增删**  尾部**高效** (平摊O(1)，末尾操作)，但可能涉及扩容。  **高效** (O(1))，直接修改头尾指针。 
| **线程安全**  **非线程安全**。  **非线程安全**。  

## `# 详细回答 

### `# ArrayList 和 LinkedList 的概念 
  - **`ArrayList`** ：

    - **定义**：`ArrayList` 是属于 `java.util` 包下的一个集合类，实现了 **`List`** 接口，允许存储重复元素，并保持元素的插入顺序。     - **底层实现**：ArrayList类源码中维护了一个Object类型的数组elementData，用来存储ArrayList集合中的元素。     - **适用场景**：  

① 需要存储的元素数量不确定，但 **查询操作** 比较频繁的场景。  

② 需要在**列表末尾**频繁**增删**元素的场景。   - **`LinkedList`** ：

    - **定义**：`LinkedList` 也属于 `List` 接口下的实现类，但它同时还实现了 `Deque` 接口（双端队列），这意味着它既可以作为列表使用，也可以作为队列（Queue）和栈（Stack）使用。     - **底层实现**：`LinkedList` 的底层是基于**双向链表**实现的。`LinkedList` 内部维护着对 **头节点(`first`)** 和 **尾节点(`last`)** 的引用。     - **适用场景**：  

① 需要频繁在**列表的中间、开头或结尾**进行**插入和删除**操作的场景。  

② 需要实现**队列（FIFO）** 或 **栈(LIFO)** 数据结构的场景。 

### `# ArrayList 和 LinkedList 的区别 
  - **底层数据结构**：

    - **`ArrayList`**：底层是**`Object[]` 数组**。数组在内存中是连续存储的，因此可以通过索引直接访问任意位置的元素。     - **`LinkedList`**：底层是**双向链表**。元素在内存中不一定是连续存储的，每个节点通过指针连接到前一个和后一个节点。   - **随机访问（`get(index)` / `set(index, E)`）效率**：

    - **`ArrayList`**：**高效**。时间复杂度为 **O(1)**。由于底层是数组，可以通过索引直接计算出元素的内存地址，实现快速随机访问。     - **`LinkedList`**：**低效**。时间复杂度为 **O(n)**。要访问特定索引的元素，需要从链表的头部或尾部开始遍历，直到找到目标位置。   - **中间位置插入和删除（`add(index, E)` / `remove(index)`）效率**：

    - **`ArrayList`**：**低效**。时间复杂度为 **O(n)**。在数组的中间位置插入或删除元素时，需要将插入点之后的所有元素向后或向前移动一位，操作量与元素数量成正比。     - **`LinkedList`**：**高效**。时间复杂度为 **O(1)**（在找到插入/删除位置的前提下）。一旦找到要操作的节点，只需修改前后节点的指针即可，无需移动大量元素。然而，**寻找目标位置本身仍然是 O(n)**。   - **首尾位置插入和删除（`add(E)` / `remove(E)` / `addFirst()` / `removeLast()`）效率**：

    - **`ArrayList`**：在**末尾**添加和删除元素是**高效**的（平摊 O(1)），因为通常只需在数组末尾操作，但偶尔会涉及扩容开销。在**头部**添加和删除则为 O(n)。     - **`LinkedList`**：在**首尾**添加和删除元素是**高效**的（O(1)），因为它直接操作头尾节点的指针，无需遍历。   - **线程安全性**：

    - **`ArrayList`** 和 **`LinkedList`** 都是**非线程安全**的。在多线程环境下使用时，如果存在写操作，需要进行外部同步（例如使用 `Collections.synchronizedList()` 包装，或使用 `java.util.concurrent` 包下的并发集合）。  

## `# 知识拓展 
  - **ArrayList 和 LinkedList 的对比图**如下所示：  
 ![image](/learn/编程笔记/Java/images/file1.kamacoder.com/i/bagu/ArrayList_versus_LinkedList.jpg)
   - **面试官可能的追问1：在实际开发中，你如何根据业务场景选择 `ArrayList` 还是 `LinkedList`？** **简答：** 选择 `ArrayList` 还是 `LinkedList` 主要取决于对集合的操作模式：

    - **选择 `ArrayList` 的场景**：- **读多写少**，特别是需要频繁地通过索引进行随机访问（`get(index)`）。

      - 主要在列表的**末尾进行添加或删除**操作。       - 对内存使用效率有一定要求，且元素数量变化不频繁。     - **选择 `LinkedList` 的场景**：- **写多读少**，特别是需要频繁地在列表的**中间、开头或结尾进行插入和删除操作**。

      - 需要将集合作为**队列（Queue）**或**栈（Stack）**来使用。     - **总结**：如果操作模式未知，通常会从 `ArrayList` 开始，因为其随机访问性能优异，且在大多数常见场景下表现良好。只有当性能分析显示中间增删是瓶颈时，才考虑 `LinkedList`。   - **面试官可能的追问2：`ArrayList` 和 `Vector` 有什么区别？为什么现在更推荐使用 `ArrayList` 而非 `Vector`？** **简答：** 
    - **区别**：- **线程安全性**：`Vector` 是**线程安全**的（所有公共方法都通过 `synchronized` 关键字同步），而 `ArrayList` 是**非线程安全**的。

      - **扩容机制**：`Vector` 默认扩容为当前容量的**两倍**，而 `ArrayList` 默认扩容为当前容量的**1.5倍**。       - **迭代器**：`Vector` 有一个遗留的 `elements()` 方法，`ArrayList` 只有 `iterator()`。     - **推荐 `ArrayList` 的原因**：- **性能**：`Vector` 的所有操作都加了 `synchronized` 锁，这带来了额外的性能开销和锁竞争。在单线程环境下，这种同步是完全不必要的负担，导致 `Vector` 性能远低于 `ArrayList`。

      - **并发方案**：在多线程环境下，有更高效的线程安全集合方案（如 `java.util.concurrent` 包下的 `CopyOnWriteArrayList` 或使用 `Collections.synchronizedList()` 包装 `ArrayList`），它们通常提供更好的并发性能或更细粒度的控制。       - **历史遗留**：`Vector` 是 Java 早期版本（JDK 1.0）就存在的类，设计上不如 `ArrayList` 灵活和高效。
