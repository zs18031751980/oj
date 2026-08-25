# 编译选项与 CMake 配置指南

## 一、MinGW 编译基础

```bash
# 编译单文件
g++ -std=c++17 -O2 main.cpp -o app

# 编译多文件
g++ -std=c++17 -O2 main.cpp helper.cpp utils.cpp -o app

# 添加包含路径
g++ -std=c++17 -O2 -I"D:/include" main.cpp -o app

# 添加库路径和链接库
g++ -std=c++17 -O2 -I"D:/include" -L"D:/lib" main.cpp -lcurl -o app
```

## 二、关键编译选项

### 优化选项

| 选项 | 说明 |
|------|------|
| `-O0` | 无优化（调试用） |
| `-O1` | 基本优化 |
| `-O2` | 推荐优化级别（大部分场景） |
| `-O3` | 激进优化（可能增加代码体积） |
| `-Os` | 优化体积 |
| `-Ofast` | 最快速度（可能违反严格浮点标准） |
| `-march=native` | 针对本机 CPU 优化 |
| `-mtune=native` | 微调本机 CPU |

### 调试选项

| 选项 | 说明 |
|------|------|
| `-g` | 生成调试信息（GDB） |
| `-ggdb` | GDB 专用调试信息 |
| `-O0 -g` | 调试模式（不优化） |
| `-O1 -g` | 调试+轻微优化 |
| `-fsanitize=address` | 检测内存越界/泄漏 |
| `-fsanitize=undefined` | 检测未定义行为 |

### 标准版本

| 选项 | 对应 C++ 版本 |
|------|--------------|
| `-std=c++11` | C++11 |
| `-std=c++14` | C++14 |
| `-std=c++17` | C++17（推荐） |
| `-std=c++20` | C++20 |
| `-std=c++23` | C++23 |

### 警告选项

```bash
# 常用警告组合
-Wall -Wextra -Wpedantic

# 更严格的
-Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wsign-conversion

# 把警告当错误
-Wall -Wextra -Werror
```

### 预处理

| 选项 | 说明 |
|------|------|
| `-DNDEBUG` | 禁用 assert |
| `-DEIGEN_NO_DEBUG` | Eigen 禁用调试检查 |
| `-DXXX=value` | 定义宏 XXX 为 value |

---

## 三、CMake 基础

### CMakeLists.txt 模板

```cmake
cmake_minimum_required(VERSION 3.16)
project(MyProject VERSION 1.0 LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 优化选项
set(CMAKE_CXX_FLAGS_RELEASE "-O2 -DNDEBUG")
set(CMAKE_CXX_FLAGS_DEBUG "-O0 -g -fsanitize=address")

# 添加可执行文件
add_executable(app main.cpp helper.cpp)

# 添加包含路径
target_include_directories(app PRIVATE
    "D:/桌面/文件/讲解/C++库安装与参考/include"
)

# 链接库
target_link_libraries(app PRIVATE
    curl
    boost_system
)
```

### 构建步骤

```bash
# 调试版本
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build

# 发布版本
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build

# 指定编译器
cmake -B build -G "MinGW Makefiles" -DCMAKE_CXX_COMPILER=g++
cmake --build build
```

---

## 四、各库的 CMake 配置

### Eigen（头文件库）
```cmake
# 无需 find_package，直接加路径
target_include_directories(app PRIVATE
    "D:/桌面/文件/讲解/C++库安装与参考/include"
)
# 或者（如果有官方 CMake）
find_package(Eigen3 REQUIRED)
target_link_libraries(app Eigen3::Eigen)
```

### nlohmann/json（头文件库）
```cmake
# 方式1：直接包含
target_include_directories(app PRIVATE "path/to/json")

# 方式2（推荐，使用 FetchContent）
include(FetchContent)
FetchContent_Declare(json
    GIT_REPOSITORY https://github.com/nlohmann/json
    GIT_TAG v3.11.3)
FetchContent_MakeAvailable(json)
target_link_libraries(app nlohmann_json::nlohmann_json)
```

### Boost
```cmake
find_package(Boost REQUIRED COMPONENTS
    filesystem
    regex
    system
    thread
)
target_link_libraries(app
    Boost::filesystem
    Boost::regex
    Boost::system
    Boost::thread
)
target_include_directories(app PRIVATE ${Boost_INCLUDE_DIRS})
```

### OpenCV
```cmake
find_package(OpenCV REQUIRED)
target_include_directories(app PRIVATE ${OpenCV_INCLUDE_DIRS})
target_link_libraries(app ${OpenCV_LIBS})
```

### libcurl
```cmake
find_package(CURL REQUIRED)
target_link_libraries(app CURL::libcurl)
```

### Qt6
```cmake
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)
qt_standard_project_setup()
add_executable(app main.cpp)
target_link_libraries(app Qt6::Core Qt6::Gui Qt6::Widgets)
```

### OpenGL + ImGui
```cmake
find_package(OpenGL REQUIRED)
target_link_libraries(app
    opengl32      # Windows
    glfw3
    imgui
)
```

### TBB
```cmake
find_package(TBB REQUIRED)
target_link_libraries(app TBB::tbb)
```

### LibTorch
```cmake
find_package(Torch REQUIRED)
target_link_libraries(app ${TORCH_LIBRARIES})
target_include_directories(app PRIVATE ${TORCH_INCLUDE_DIRS})
```

---

## 五、Vcpkg 包管理器

### 安装 vcpkg
```bash
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg integrate install
```

### 常用命令
```bash
# 搜索库
vcpkg search opencv

# 安装库（x64-windows 是最常用 triplet）
vcpkg install opencv4:x64-windows
vcpkg install boost:x64-windows
vcpkg install curl:x64-windows
vcpkg install eigen3:x64-windows
vcpkg install nlohmann-json:x64-windows

# 列出已安装
vcpkg list

# 移除
vcpkg remove opencv4

# 更新
vcpkg update
vcpkg upgrade
```

### 在 CMake 中使用 vcpkg
```cmake
# 方式1：在 CMakeLists.txt 中添加
set(CMAKE_TOOLCHAIN_FILE "D:/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake")

# 方式2：在 CMake 命令行指定
cmake -B build -DCMAKE_TOOLCHAIN_FILE="D:/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake"
```

---

## 六、完整示例：Eigen + nlohmann/json 项目

### 目录结构
```
project/
├── CMakeLists.txt
├── src/
│   └── main.cpp
└── data/
    └── input.json
```

### CMakeLists.txt
```cmake
cmake_minimum_required(VERSION 3.16)
project(MathModeling)

set(CMAKE_CXX_STANDARD 17)

# Eigen
set(EIGEN_DIR "D:/桌面/文件/讲解/C++库安装与参考/include")
target_include_directories(MathModeling PRIVATE ${EIGEN_DIR})

# nlohmann/json（直接包含）
include_directories("D:/桌面/文件/讲解/C++库安装与参考/include")

add_executable(math_model src/main.cpp)
```

### 编译
```bash
# 手动
g++ -std=c++17 -O2 -I"D:/桌面/文件/讲解/C++库安装与参考/include" src/main.cpp -o math_model

# 用 CMake
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

---

## 七、常用编译命令速查

| 场景 | 命令 |
|------|------|
| 基本编译（一个 cpp） | `g++ -std=c++17 -O2 main.cpp -o app` |
| 多文件 | `g++ -std=c++17 -O2 *.cpp -o app` |
| 含头文件路径 | `g++ -std=c++17 -O2 -I./include main.cpp -o app` |
| 链接库 | `g++ main.cpp -lcurl -lboost_filesystem -o app` |
| 调试模式 | `g++ -std=c++17 -O0 -g main.cpp -o app` |
| TBB 并行 | `g++ -std=c++17 -O2 main.cpp -ltbb -o app` |
| OpenCV | `g++ main.cpp -lopencv_core -lopencv_imgproc -lopencv_highgui -o app` |
| 数学建模（Eigen） | `g++ -std=c++17 -O2 -march=native -DEIGEN_NO_DEBUG main.cpp -o app` |
