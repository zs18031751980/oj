# Boost 库详解 — C++ 万能工具箱

## 概述

Boost 被称为"C++ 准标准库"，C++ 标准库很多特性（智能指针、正则、文件系统、线程等）都是从 Boost 吸纳的。

**安装：** 建议通过 vcpkg：`vcpkg install boost`，或下载源码编译。也可使用预编译二进制。

**包含路径：** `#include <boost/xxx.hpp>`

**编译链接：** 大部分 Boost 库是头文件（无需编译），少部分需要链接 lib（如 filesystem, thread, regex, serialization）。

---

## 一、字符串与文本处理

### 1.1 Boost.LexicalCast（类型转换）
```cpp
#include <boost/lexical_cast.hpp>

int n = boost::lexical_cast<int>("42");
double d = boost::lexical_cast<double>("3.14");
std::string s = boost::lexical_cast<std::string>(123);
// 转换失败抛 boost::bad_lexical_cast 异常
```

### 1.2 Boost.Format（格式化输出，类似 printf）
```cpp
#include <boost/format.hpp>

std::string s = (boost::format("x = %d, y = %.2f") % 42 % 3.1415).str();
// "x = 42, y = 3.14"
```

### 1.3 Boost.StringAlgo（字符串算法）
```cpp
#include <boost/algorithm/string.hpp>

std::string s = "  Hello, World!  ";
boost::trim(s);                                  // 去首尾空格 → "Hello, World!"
boost::to_upper(s);                              // 转大写
boost::to_lower(s);                              // 转小写

std::vector<std::string> parts;
boost::split(parts, "a,b,c", boost::is_any_of(",")); // 分割 → ["a","b","c"]

std::string joined = boost::join(parts, "-");    // 拼接 → "a-b-c"

boost::replace_all(s, "World", "Boost");         // 替换全部
boost::erase_all(s, "o");                        // 删除全部

bool starts = boost::starts_with(s, "Hello");    // 前缀判断
bool ends = boost::ends_with(s, "!");            // 后缀判断
bool contains = boost::contains(s, "World");     // 包含判断
```

---

## 二、日期时间

```cpp
#include <boost/date_time/posix_time/posix_time.hpp>
#include <boost/date_time/gregorian/gregorian.hpp>
namespace pt = boost::posix_time;
namespace gr = boost::gregorian;

// 日期
gr::date d1(2024, 1, 1);
gr::date d2 = gr::from_simple_string("2024/12/31");
gr::date_duration dd = d2 - d1;   // 天数差

// 时间点
pt::ptime t1(gr::date(2024,1,1), pt::hours(10));
pt::ptime t2 = pt::second_clock::local_time();           // 当前时间
pt::time_duration td = t2 - t1;
long secs = td.total_seconds();

// 时间字符串
std::string s = pt::to_simple_string(t2);                // "2024-Jul-27 22:15:30"
```

---

## 三、文件系统

```cpp
#include <boost/filesystem.hpp>
namespace fs = boost::filesystem;

fs::path p("C:/data/file.txt");
p.filename();              // "file.txt"
p.stem();                  // "file"
p.extension();             // ".txt"
p.parent_path();           // "C:/data"
p.root_name();             // "C:"

fs::exists(p);             // 是否存在
fs::is_directory(p);       // 是否是目录
fs::is_regular_file(p);    // 是否是普通文件
fs::file_size(p);          // 文件大小

fs::create_directory("C:/data/newdir");
fs::remove("C:/data/old.txt");
fs::rename("old.txt", "new.txt");
fs::copy_file("src.txt", "dst.txt");

// 遍历目录
for (auto& entry : fs::recursive_directory_iterator("C:/data"))
    if (fs::is_regular_file(entry.path()))
        std::cout << entry.path() << "\n";
```

> **注意：** C++17 已将 filesystem 纳入标准库 → `<filesystem>` / `std::filesystem`，功能与 Boost.Filesystem 几乎相同。

---

## 四、正则表达式

```cpp
#include <boost/regex.hpp>

std::string s = "hello 42 world 3.14";
boost::regex pattern(R"(\d+\.?\d*)");  // 匹配数字
boost::smatch matches;

// 查找
if (boost::regex_search(s, matches, pattern))
    std::cout << matches[0];  // "42"

// 遍历全部
auto begin = boost::sregex_iterator(s.begin(), s.end(), pattern);
auto end = boost::sregex_iterator();
for (auto it = begin; it != end; ++it)
    std::cout << (*it).str() << "\n";

// 替换
std::string result = boost::regex_replace(s, pattern, "[$&]");
// "hello [42] world [3.14]"
```

---

## 五、智能指针与内存

Boost 的智能指针现已纳入 C++ 标准：

```cpp
// Boost 版本（C++11 前）
boost::shared_ptr<int> p = boost::make_shared<int>(42);
boost::weak_ptr<int> wp = p;
boost::scoped_ptr<int> sp(new int(10));  // 不能拷贝，离开作用域自动释放
boost::intrusive_ptr<T> ip;              // 引用计数侵入式
```

C++11 后直接用 `std::shared_ptr`, `std::make_shared`, `std::weak_ptr`, `std::unique_ptr`。

---

## 六、多线程

```cpp
#include <boost/thread.hpp>

// 线程
boost::thread t([]{
    std::cout << "hello from thread\n";
});
t.join();

// 互斥锁
boost::mutex mtx;
{
    boost::lock_guard<boost::mutex> lock(mtx);
    // 临界区
}

// 读写锁
boost::shared_mutex rw_mtx;
// 读锁
{
    boost::shared_lock<boost::shared_mutex> lock(rw_mtx);
}
// 写锁
{
    boost::unique_lock<boost::shared_mutex> lock(rw_mtx);
}

// 条件变量
boost::condition_variable cv;
boost::mutex cv_mtx;
cv.wait(lock, []{ return ready; });
cv.notify_one();
cv.notify_all();

// 线程池（需要 boost.asio）
// 见网络通信章节
```

C++11 后多线程用 `std::thread`, `std::mutex`, `std::shared_mutex`(C++17), `std::condition_variable` 即可。

---

## 七、随机数

```cpp
#include <boost/random.hpp>

// 生成器
boost::mt19937 rng(static_cast<unsigned>(time(nullptr)));

// 均匀分布 [0, 1)
boost::uniform_real<double> dist01(0.0, 1.0);
double r = dist01(rng);

// 正态分布
boost::normal_distribution<double> norm(0.0, 1.0);
double n = norm(rng);

// 整数均匀分布
boost::uniform_int<int> dice(1, 6);
int roll = dice(rng);

// 从容器随机选择
std::vector<int> v = {1,2,3,4,5};
boost::uniform_int<size_t> idx(0, v.size()-1);
int selected = v[idx(rng)];
```

---

## 八、序列化

```cpp
#include <boost/archive/text_oarchive.hpp>
#include <boost/archive/text_iarchive.hpp>
#include <boost/serialization/vector.hpp>
#include <fstream>

class Point {
    int x, y;
    friend class boost::serialization::access;
    template<class Archive>
    void serialize(Archive& ar, const unsigned int version) {
        ar & x & y;
    }
};

// 写入
std::ofstream ofs("data.txt");
boost::archive::text_oarchive oa(ofs);
Point p{1, 2};
oa << p;

// 读取
std::ifstream ifs("data.txt");
boost::archive::text_iarchive ia(ifs);
Point p2;
ia >> p2;
```

---

## 九、数学与数值

```cpp
#include <boost/math/special_functions.hpp>

// 特殊函数
double beta = boost::math::beta(a, b);
double gamma = boost::math::tgamma(x);   // Gamma 函数
double erf = boost::math::erf(x);        // 误差函数
double bessel = boost::math::cyl_bessel_j(n, x);  // 贝塞尔函数

// 数值积分
#include <boost/math/quadrature/exp_sinh.hpp>
using boost::math::quadrature::exp_sinh;
auto f = [](double x) { return exp(-x*x); };
double Q = exp_sinh<double>().integrate(f, 0, std::numeric_limits<double>::infinity());

// 多项式
#include <boost/math/tools/polynomial.hpp>
using boost::math::tools::polynomial;
polynomial<double> a({1, 2, 1});  // x^2 + 2x + 1
polynomial<double> b({1, 1});     // x + 1
auto c = a * b;                    // 多项式乘法
```

---

## 十、Boost.Asio（网络通信）

参见网络通信章节的独立文档。

```cpp
// Asio 核心：io_context + socket
#include <boost/asio.hpp>
namespace asio = boost::asio;

asio::io_context io;
asio::ip::tcp::socket sock(io);
asio::ip::tcp::resolver resolver(io);
asio::connect(sock, resolver.resolve("example.com", "80"));
asio::write(sock, asio::buffer("GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"));

char buf[4096];
size_t len = sock.read_some(asio::buffer(buf));
std::cout << std::string(buf, len);
```

---

## 十一、其他实用组件

```cpp
// 程序选项解析（类似 argparse）
#include <boost/program_options.hpp>
namespace po = boost::program_options;
po::options_description desc("Options");
desc.add_options()
    ("help", "show help")
    ("input", po::value<std::string>(), "input file")
    ("verbose,v", po::bool_switch()->default_value(false), "verbose");
po::variables_map vm;
po::store(po::parse_command_line(argc, argv, desc), vm);

// UUID
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_generators.hpp>
boost::uuids::uuid uid = boost::uuids::random_generator()();
std::string uid_str = boost::uuids::to_string(uid);

// 任意类型（类似 std::any）
#include <boost/any.hpp>
boost::any a = 42;
a = std::string("hello");
int n = boost::any_cast<int>(a);  // 若类型不匹配抛异常

// 可选值（类似 std::optional）
#include <boost/optional.hpp>
boost::optional<int> maybe = boost::make_optional(42);
if (maybe) std::cout << maybe.get();

// 令牌桶 / 限流
#include <boost/tokenizer.hpp>
// 略
```

---

## Boost 子库速查表

| 组件 | 头文件 | 说明 | 需要编译？ |
|------|--------|------|-----------|
| LexicalCast | `boost/lexical_cast.hpp` | 类型转换 | 否 |
| Format | `boost/format.hpp` | 格式化字符串 | 否 |
| StringAlgo | `boost/algorithm/string.hpp` | 字符串算法 | 否 |
| Tokenizer | `boost/tokenizer.hpp` | 分词 | 否 |
| Date_Time | `boost/date_time/` | 日期时间 | 是 |
| Filesystem | `boost/filesystem.hpp` | 文件系统 | 是 |
| Regex | `boost/regex.hpp` | 正则 | 是 |
| Thread | `boost/thread.hpp` | 多线程 | 是 |
| Random | `boost/random.hpp` | 随机数 | 否 |
| Math | `boost/math/` | 数学特殊函数 | 否 |
| Serialization | `boost/serialization/` | 序列化 | 是 |
| Asio | `boost/asio.hpp` | 网络通信 | 是（或仅头文件） |
| ProgramOptions | `boost/program_options.hpp` | 命令行参数 | 是 |
| Uuid | `boost/uuid/uuid.hpp` | UUID 生成 | 是 |
| Any | `boost/any.hpp` | 任意类型 | 否 |
| Optional | `boost/optional.hpp` | 可选值 | 否 |
| Variant | `boost/variant.hpp` | 类型安全联合体 | 否 |
| Spirit | `boost/spirit/` | 解析器生成器 | 仅头文件 |
| Pool | `boost/pool.hpp` | 内存池 | 是 |
| CircularBuffer | `boost/circular_buffer.hpp` | 环形缓冲 | 仅头文件 |
| BidirectionalMap | `boost/bimap.hpp` | 双向映射 | 仅头文件 |
| MultiArray | `boost/multi_array.hpp` | 多维数组 | 仅头文件 |
| PropertyTree | `boost/property_tree/` | 树形配置（XML/JSON/INI） | 仅头文件 |
| Graph | `boost/graph/` | 图论算法库 | 仅头文件 |

---

## 编译示例

```bash
# 链接 Boost 库（filesystem + regex + thread）
g++ -std=c++17 -O2 main.cpp \
    -lboost_filesystem -lboost_regex -lboost_thread \
    -o main
# 如果 Boost 安装在非标准路径
g++ -std=c++17 -O2 main.cpp \
    -I"D:/path/to/boost" \
    -L"D:/path/to/boost/stage/lib" \
    -lboost_filesystem -lboost_regex -o main
```
