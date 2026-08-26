# JSON、序列化与文件处理库详解

## 一、nlohmann/json — 最流行的 C++ JSON 库

### 概述
单头文件库，语法简洁，类似 Python 的 json 模块。

**安装：** 已下载到 `include/nlohmann/json.hpp`（单头文件）

### 包含与类型

```cpp
#include <nlohmann/json.hpp>
using json = nlohmann::json;

// 核心类型：json 对象可以自动存储以下类型
json j;
j = nullptr;           // null
j = true;              // bool
j = 42;                // int
j = 3.14;              // float/double
j = "hello";           // string
j = {1,2,3};           // array
j = {{"a",1},{"b",2}}; // object
```

### 从字符串解析

```cpp
// 从字符串
std::string s = R"({"name":"Alice","age":30,"scores":[85,92,78]})";
json j = json::parse(s);

// 从文件
std::ifstream f("data.json");
json j = json::parse(f);
f.close();

// 从 C 字符串
json j = json::parse(raw_cstr);

// 带错误处理的解析
try {
    json j = json::parse(s);
} catch (json::parse_error& e) {
    std::cerr << "解析错误: " << e.what() << " at byte " << e.byte;
}
```

### 访问数据

```cpp
json j = json::parse(R"({"name":"Alice","scores":[85,92,78]})");

// 直接读取
std::string name = j["name"];                       // "Alice"
int first = j["scores"][0];                         // 85

// 带默认值（如果键不存在）
std::string city = j.value("city", "Beijing");      // "Beijing"

// 包含判断
bool has_name = j.contains("name");                 // true

// 类型检查
j.is_null();
j.is_boolean();
j.is_number();
j.is_number_integer();
j.is_number_float();
j.is_string();
j.is_array();
j.is_object();

// 迭代数组
for (auto& item : j["scores"])
    std::cout << (int)item << " ";

// 迭代对象
for (auto& [key, val] : j.items())
    std::cout << key << " = " << val << "\n";
```

### 构建 JSON

```cpp
json j;
j["name"] = "Bob";
j["age"] = 25;
j["scores"] = {90, 85, 88};
j["address"]["city"] = "Shanghai";
j["address"]["zip"] = "200000";

// 用 initializer_list 直接构造
json j2 = {
    {"name", "Carol"},
    {"grades", {
        {"math", 95},
        {"physics", 87}
    }}
};
```

### 转字符串

```cpp
std::string s1 = j.dump();              // 紧凑格式（无空格）
std::string s2 = j.dump(4);             // 带缩进（4空格），更可读

// 写入文件
std::ofstream f("output.json");
f << j.dump(4);
f.close();

// 或者直接用流
std::ofstream("output.json") << j.dump(2);
```

### 访问类型安全

```cpp
// 各种 get 方法
int n = j["age"].get<int>();
std::string s = j["name"].get<std::string>();
std::vector<int> v = j["scores"].get<std::vector<int>>();
std::map<std::string, json> m = j.get<std::map<std::string, json>>();

// 自定义类型（需要 NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE 宏）
struct Person {
    std::string name;
    int age;
};
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Person, name, age)
// 现在可以直接 j.get<Person>() 或 j = person
```

### 合并与比较

```cpp
json j1 = {{"a", 1}, {"b", 2}};
json j2 = {{"b", 3}, {"c", 4}};
j1.merge_patch(j2);  // j1 = {{"a",1},{"b",3},{"c",4}}

bool eq = (j1 == j2);  // 深度相等比较
bool neq = (j1 != j2);
```

### 查询

```cpp
// 查找指针（类似 JSON Pointer）
json j = json::parse(R"({"a":{"b":[0,1,2]}})");
json* found = j.find_pointer("/a/b/1");  // 指向值 1

// 扁平化
json flat = j.flatten();  // 展开为 {"a/b/0":0, "a/b/1":1, "a/b/2":2}
```

### 完整示例：爬取 API

```cpp
#include <nlohmann/json.hpp>
#include <curl/curl.h>
#include <iostream>
using json = nlohmann::json;

size_t write_cb(void* contents, size_t sz, size_t n, void* userp) {
    ((std::string*)userp)->append((char*)contents, sz * n);
    return sz * n;
}

int main() {
    CURL* curl = curl_easy_init();
    std::string resp;
    curl_easy_setopt(curl, CURLOPT_URL, "https://api.github.com/repos/nlohmann/json");
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &resp);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, "C++App");
    curl_easy_perform(curl);
    curl_easy_cleanup(curl);

    json j = json::parse(resp);
    std::cout << "stars: " << j["stargazers_count"] << "\n";
    std::cout << "license: " << j["license"]["spdx_id"] << "\n";
    return 0;
}
```

---

## 二、protobuf — 高效二进制序列化

### 概述
Google Protocol Buffers，比 JSON 更小更快，适合网络传输和存储。

### 安装
vcpkg: `vcpkg install protobuf protobuf`

### 定义消息格式（.proto 文件）

```protobuf
// person.proto
syntax = "proto3";
message Person {
    string name = 1;
    int32 age = 2;
    repeated string tags = 3;
}
```

### 编译 .proto

```bash
protoc --cpp_out=. person.proto
# 生成 person.pb.h 和 person.pb.cc
```

### 使用

```cpp
#include "person.pb.h"

// 构建
Person p;
p.set_name("Alice");
p.set_age(30);
p.add_tags("student");
p.add_tags("math");

// 序列化
std::string data;
p.SerializeToString(&data);     // 二进制字符串
// 或 p.SerializeToOstream(&f);  // 写入文件

// 反序列化
Person p2;
p2.ParseFromString(data);       // 从二进制字符串
// 或 p2.ParseFromIstream(&f);

std::cout << p2.name() << " " << p2.age() << "\n";
for (int i = 0; i < p2.tags_size(); ++i)
    std::cout << p2.tags(i) << "\n";
```

### 与 JSON 对比

| 特性 | JSON | protobuf |
|------|------|----------|
| 格式 | 文本（可读） | 二进制（不可读） |
| 大小 | 大 | 小（约 1/10） |
| 速度 | 慢 | 快 |
| 模式定义 | 无 | 需要 .proto 文件 |
| 版本兼容 | 需手动 | 内置向前/向后兼容 |
| 跨语言 | 所有语言 | 所有主流语言 |

---

## 三、tinyxml2 — XML 解析

### 概述
轻量级 XML 解析库（仅 2 个文件：tinyxml2.h / tinyxml2.cpp）。

### 安装
直接下载 tinyxml2.h 和 tinyxml2.cpp 放到项目中即可。

### 解析 XML

```cpp
#include "tinyxml2.h"
using namespace tinyxml2;

XMLDocument doc;
doc.LoadFile("config.xml");

// 根元素
XMLElement* root = doc.RootElement();

// 查询子元素
XMLElement* name = root->FirstChildElement("name");
if (name) std::cout << name->GetText();

// 读取属性
const char* id = root->Attribute("id");

// 迭代
for (XMLElement* e = root->FirstChildElement(); e; e = e->NextSiblingElement())
    std::cout << e->Value() << ": " << e->GetText() << "\n";

// 从字符串解析
doc.Parse(xml_cstr);
```

### 创建 XML

```cpp
XMLDocument doc;
XMLDeclaration* decl = doc.NewDeclaration();
doc.InsertFirstChild(decl);

XMLElement* root = doc.NewElement("root");
root->SetAttribute("version", "1.0");
doc.InsertEndChild(root);

XMLElement* item = doc.NewElement("item");
item->SetText("Hello");
root->InsertEndChild(item);

doc.SaveFile("output.xml");
```

---

## 四、stb_image — 轻量图片读写

### 概述
单头文件图片库，支持 JPEG、PNG、BMP、GIF 等格式。

### 包含
```cpp
// 在 **一个** .cpp 文件中定义实现
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

// 使用只需要声明
#include "stb_image.h"
```

### 读取图片

```cpp
int w, h, channels;
// 读取为 RGB（3 通道）
unsigned char* data = stbi_load("image.jpg", &w, &h, &channels, 3);
// data 是 w × h × 3 的数组，按行排列 RGBRGB...

if (data) {
    // 访问像素 (x,y) 的 R 值 = data[(y * w + x) * 3 + 0]
    // G = data[(y * w + x) * 3 + 1]
    // B = data[(y * w + x) * 3 + 2]
    stbi_image_free(data);
}

// 读取灰度（强制 1 通道）
unsigned char* gray = stbi_load("image.jpg", &w, &h, &channels, 1);
```

### 写入图片

```cpp
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

// 写入 PNG
stbi_write_png("output.png", w, h, 3, data, w * 3);

// 写入 JPG（质量 90）
stbi_write_jpg("output.jpg", w, h, 3, data, 90);

// 写入 BMP
stbi_write_bmp("output.bmp", w, h, 3, data);
```

### 完整示例

```cpp
#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image.h"
#include "stb_image_write.h"

int main() {
    int w, h, n;
    unsigned char* img = stbi_load("input.jpg", &w, &h, &n, 3);
    if (!img) return -1;

    // 转为灰度（简单平均）
    for (int i = 0; i < w * h; ++i) {
        unsigned char gray = (img[i*3] + img[i*3+1] + img[i*3+2]) / 3;
        img[i*3] = img[i*3+1] = img[i*3+2] = gray;
    }

    stbi_write_jpg("output_gray.jpg", w, h, 3, img, 95);
    stbi_image_free(img);
    return 0;
}
```

---

## 五、数据格式对比

| 格式 | 库 | 适用场景 | 可读 | 大小 | 速度 |
|------|-----|---------|------|------|------|
| JSON | nlohmann/json | 配置文件、API 通信、人类可读 | ★★★★★ | ★★ | ★★★ |
| Protobuf | protobuf | 内部 RPC、高性能通信、存储 | ★ | ★★★★★ | ★★★★★ |
| XML | tinyxml2 | 遗留系统、文档格式 | ★★★ | ★ | ★★ |
| CSV | 手动/C++ 标准库 | 表格数据、Excel 导入导出 | ★★★ | ★★★ | ★★★ |
| 图片 | stb_image | 图像处理、纹理加载 | 不可读 | — | ★★★★ |
