# epoll为什么比select/poll高效？

> 来源: https://notes.kamacoder.com/base/poll-efficiency.html

# epoll为什么比select/poll高效？

## 简要回答

epoll高效的核心原因：

**事件驱动**：只**返回就绪的文件描述符**，无需遍历**所有fd**

**内核回调**：通过**回调机**制通知就绪事件，**O(1)时间复杂度**

**共享内存**：**避免**用户空间和内核空间的**数据拷贝**

**水平触发与边缘触发**：提供**更灵活的**事件**通知模式**

## 详细回答

三种I/O多路复用机制对比：

  1. select 的问题
**线性扫描**：每次调用需要遍历所有fd**，O(n)时间复杂度**

**fd_set大小限制**：通**常1024个文件**描述符

内存拷贝：**每次**调用**都需要**在用户空间和内核空间**拷贝fd_set**

重复初始化：**每次调用后需要重新设置监控的fd**

  1. poll 的改进
**链表结构**：**突破1024限**制，使用pollfd数组

**但仍有性能问题**：仍然**需要遍历所有fd**，O(n)时间复杂度

**内存拷贝**：同样**需要拷贝整个pollfd数组**

  1. epoll 的高效设计
红黑树存储：高效的fd管理，**插入删除O(log n)**

就绪链表：**只返回就绪的fd，无需遍历所有fd**

事件回调：内核通过**回调机制直接通知就绪事件**

内存共享：**epoll_ctl和epoll_wait共享内核数据结构**

边缘触发：**避免重复通知，提高性能**

**epoll 核心原理：**

epoll_create：**创建epoll实例，返回epoll文件描述符**

epoll_ctl：**向epoll实例中添加/修改/删除监控的fd**

epoll_wait：**等待I/O事件发生**，只**返回就绪的fd列表**

## 代码示例

```
public:
    bool start(int port) {
        // 创建服务器socket
        server_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (server_fd < 0) return false;

        // 设置端口复用
        int opt = 1;
        setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

        // 绑定地址
        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        addr.sin_addr.s_addr = INADDR_ANY;

        if (bind(server_fd, (sockaddr*)&addr, sizeof(addr)) < 0) {
            close(server_fd);
            return false;
        }

        // 监听
        if (listen(server_fd, 128) < 0) {
            close(server_fd);
            return false;
        }

        // 创建epoll实例
        epoll_fd = epoll_create1(0);
        if (epoll_fd < 0) {
            close(server_fd);
            return false;
        }

        // 添加服务器socket到epoll
        epoll_event ev{};
        ev.events = EPOLLIN;  // 监听可读事件
        ev.data.fd = server_fd;
        if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, server_fd, &ev) < 0) {
            close(epoll_fd);
            close(server_fd);
            return false;
        }

        return true;
    }

```


## 知识拓展

  1. 水平触发 vs 边缘触发

水平触发（LT）：

fd就绪时持续通知，直到数据被处理完，
编程更简单，不容易遗漏事件，
可能产生不必要的重复通知

边缘触发（ET）：

只在fd状态变化时通知一次，
需要一次性处理完所有数据，
性能更高，但编程更复杂，
必须使用非阻塞I/O

  1. epoll 的局限性

**仅限Linux**：Windows不支持

**文件描述符类型限制：不支持普通文件**

内存占用：每个epoll实例需要内核资源

小连接数场景：可能不如select/poll高效

  - 使用场景

**高并发网络服务器**：Web服务器、游戏服务器

**实时通信系统**：聊天服务器、视频会议

**代理服务器**：Nginx、HAProxy

**数据库连接池**：管理大量数据库连接

**文件服务器**：处理大量文件I/O

**任何需要处理大量并发连接的场景**

  - 知识图解

![image](/learn/计算机基础/images/file1.kamacoder.com/i/bagu/2026012901.png)

  - 面试官很能追问

Q1：epoll的边缘触发模式为什么要用非阻塞I/O？

A1：
边缘触发只通知一次，必须一次性读取所有可用数据

如果使用阻塞I/O，读取时可能会阻塞，导致其他fd饿死

非阻塞I/O确保读取到EAGAIN/EWOULDBLOCK时立即返回

避免进程阻塞，保证所有就绪fd都能及时处理

Q2：epoll如何避免惊群效应？

A2：
**惊群效应**：多个进程/线程等待同一个fd，事件发生时全部被唤醒

解决方案：
EPOLLEXCLUSIVE标志（Linux 4.5+）：确保只有一个epoll实例被唤醒

SO_REUSEPORT：内核级别负载均衡

应用层同步：使用互斥锁控制只有一个worker处理连接

单线程accept + 多线程处理

Q3：epoll和select的文件描述符限制？

A3：
select：FD_SETSIZE限制（通常1024），编译时确定

poll：理论上无限制，但性能随fd数量线性下降
epoll：只与系统内存有关，通常支持数十万fd
查看限制：cat /proc/sys/fs/file-max
