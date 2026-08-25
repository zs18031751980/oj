# Java异常类型

> 来源: https://notes.kamacoder.com/java/java-exceptions.html

# `# Java异常类型 

## `# 简要回答 
  - Java 中的异常都继承自 `java.lang.Throwable` 类，它分为两大类：`Error` 和 `Exception`。

    - **`Error`(错误)** ：  

表示 **JVM 内部** 或 **系统级别**的问题，通常是很严重的，程序无法恢复。例如：`OutOfMemoryError` (内存溢出)、`StackOverflowError` (栈溢出)。     - **`Exception`(异常)** ：  

表示程序在 **编译时** 或 **运行时** 可能发生的问题，通常是**可捕获和处理**的。`Exception` 又分为两大子类：  

① **编译期异常 (Checked Exception)** ：是指编译器**强制检查**的异常，必须进行 `try-catch` 捕获处理 或者 `throws` 声明处理，常见的编译期异常有 `IOException` (输入输出异常)、`SQLException` (数据库操作异常)。  

② **运行期异常 (Runtime Exception / Unchecked Exception)** ：是指编译器**不强制检查**的异常，通常是程序逻辑错误导致的，可选择性处理，常见的运行期异常有 `NullPointerException` (空指针异常)、`ArrayIndexOutOfBoundsException` (数组越界异常)。  

## `# 详细回答 
  - Java 中所有的异常都源于 `java.lang.Throwable` 类，它有两个主要的直接子类：`Error` 和 `Exception`。 
  - **`Error`(错误)** ：

    - **定义**：`Error` 类及其子类表示了在 **程序运行期间发生的**、**JVM** 或 **系统级别的** 严重问题，这些问题通常是应用程序**无法预料和恢复**的。例如，JVM 内存耗尽、JVM 错误、线程死锁等。     - **特点**：`Error` 是**非受检查异常 (Unchecked Exception) 的一种特殊形式**，编译器不会强制捕获或声明。由于它们通常是致命的，即使捕获了也难以恢复，因此在开发中，通常不会去捕获 `Error`，而是让程序终止，以便系统管理员介入处理。     - **常见类型**：  

① `java.lang.OutOfMemoryError`：是指当JVM**内存不足**，无法分配对象时抛出。  

② `java.lang.StackOverflowError`：是指当方法调用**栈溢出**时抛出，通常是由于无限递归导致。  

③ `java.lang.NoClassDefFoundError`：当JVM试图加载某个类，但在**运行时找不到该类的定义**时抛出。  

④ `java.lang.VirtualMachineError`：**虚拟机**在运行时发生的**内部错误**。   - **`Exception`(异常)** ：

    - **定义**：`Exception` 类及其子类表示程序在运行过程中可能遇到的、**可以被捕获和处理**的异常情况。这些异常通常是由于**外部因素**（如文件不存在、网络中断）或**程序逻辑错误**导致的。     - **特点**：`Exception` 是我们日常开发中主要关注和处理的异常类型。它进一步分为两大类：编译期异常 和 运行期异常。     - **编译期异常 (Checked Exception / 受检查异常)** ：

      - 这类异常是指所有**直接或间接继承自 `java.lang.Exception`，但不是 `java.lang.RuntimeException` 及其子类**的异常。它们之所以被称为“编译期异常”或“受检查异常”，是因为Java编译器会**强制检查**你是否对这类异常进行了处理（例如 使用 `try-catch` 块捕获，或 使用 `throws` 关键字抛出），如果未处理或声明，代码将无法编译通过。       - 编译期异常通常表示**程序外部环境**可能出现的问题，**是可预见的、可恢复的**。所以开发者在编写代码时，需要明确地考虑这些异常，并提供相应的处理逻辑。       - **常见类型**：  

① `java.io.IOException`：是指所有 **I/O操作**（如文件读写、网络通信）可能抛出的异常的基类。  

② `java.io.FileNotFoundException`：是指尝试**打开一个不存在的文件**时抛出的异常。  

③ `java.sql.SQLException`：在**数据库访问操作**中发生的异常。  

④ `java.lang.ClassNotFoundException`：是指当应用程序试图**通过类的字符串名称加载类**，但找不到该类定义时抛出。  

⑤ `java.lang.InterruptedException`：当**一个线程**在等待、休眠或占用途中，**被另一个线程中断**时抛出。     - **运行期异常 (RuntimeException / Unchecked Exception / 非受检查异常)** ：

      - 这类异常是 **`RuntimeException` 类及其所有子类**。它们被称为“运行期异常”或“非受检查异常”，是因为编译器**不会强制检查**你是否捕获或声明它们，因为即使不处理，代码也能编译通过。       - 运行期异常通常表示**程序内部**的逻辑错误、编程缺陷或不合法的参数。这类异常通常是由于程序员的疏忽导致的，例如，尝试访问空对象的成员、数组越界等。       - **常见类型**：  

① `java.lang.NullPointerException`：是指尝试**对一个 `null` 对象进行操作**时抛出的异常。  

② `java.lang.ArrayIndexOutOfBoundsException`：是指**数组索引**超出其有效范围时抛出的异常。  

③`java.lang.ClassCastException`：是指在进行**强制类型转换**时，如果对象不是目标类型的实例，则抛出。  

④ `java.lang.IllegalArgumentException`：是指向方法传递了一个**不合法或不正确的参数**时抛出的异常。  

⑤ `java.lang.NumberFormatException`：是指尝试将一个**不符合数字格式**的字符串转换为数字时抛出的异常。  

⑥ `java.lang.ArithmeticException`：是指发生**不合法的算术运算**时抛出的异常，例如除以零。  

⑦ `java.lang.IndexOutOfBoundsException`：是指**所有索引超出范围**异常的基类（包括数组、字符串、集合等）。  

## `# 知识拓展 
  - **Java异常体系图**，如下所示：  
 ![image](../images/file1.kamacoder.com/i/bagu/Exception_System.jpg)
   - **面试官可能的追问1：为什么Java要区分编译期异常和运行期异常？这种设计有什么好处和坏处？** 
    - **简答：** 这种区分是Java异常处理的核心设计理念，可以平衡程序的健壮性和开发效率。  

① **好处**：编译期异常 会强制开发者处理那些外部环境可能导致的问题（如文件不存在、网络中断），使得程序对这些可预见且可能恢复的错误**更加健壮**。运行期异常通常**指示编程错误**，不强制处理有助于快速发现和修复这些错误，避免代码中充斥大量无意义的 `try-catch` 块。  

② **坏处**：代码冗余，对于一些不重要的编译期异常，强制处理可能导致代码中出现大量 `try-catch` 块，增加代码的冗余度和可读性负担。而且，开发者有时会为了通过编译而捕获所有编译期异常，但可能没有提供有效的处理逻辑，反而掩盖了问题。   - **面试官可能的追问2：在实际开发中，我们应该如何选择抛出编译期异常还是运行期异常？** 
    - **简答：**  

① 当异常是**可预见的、可恢复的，并且是由于外部环境或调用者错误**导致的，应该**抛出编译期异常**。这强制调用者处理这些异常，提高程序的健壮性。例如，文件操作、网络连接、数据库访问等。  

② 当异常是**不可预见的、通常是由于程序逻辑错误或编程缺陷**导致的，应该**抛出运行期异常**。这表明调用者应该在调用前避免这些错误，或者通过**更严格的输入校验和边界检查**来预防。例如，非法参数（`IllegalArgumentException`）、空指针（`NullPointerException`）等。
