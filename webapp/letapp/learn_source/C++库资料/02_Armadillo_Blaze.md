# Armadillo 与 Blaze 数值计算库参考手册

---

# 第一篇：Armadillo

## 1. 概述

**Armadillo** 是一个基于 C++ 的高质量线性代数库，其语法与 MATLAB 高度相似，旨在在 C++ 环境中提供快速原型开发和生产级性能。

| 项目 | 说明 |
|------|------|
| 头文件 | `#include <armadillo>` |
| 命名空间 | `arma` |
| 底层依赖 | BLAS / LAPACK（可选 OpenBLAS、Intel MKL、Apple Accelerate 或系统 BLAS） |
| 许可证 | Apache 2.0 |
| 官网 | https://arma.sourceforge.net/ |

### 安装方式

**vcpkg（推荐）**：
```
vcpkg install armadillo
vcpkg install openblas   # 推荐搭配高性能 BLAS
```

**源码编译**：
从 https://arma.sourceforge.net/download.html 下载，解压后：

```bash
cd armadillo-14.x.x
cmake -B build -DCMAKE_INSTALL_PREFIX=/usr/local
cmake --build build
cmake --install build
```

**编译器链接**（以 g++ 为例）：
```bash
g++ main.cpp -o main -O2 -larmadillo -lopenblas
```

---

## 2. 核心类型（Key Types）

```cpp
#include <armadillo>
using namespace arma;

// ── 稠密矩阵 ──
mat    A;           // double 矩阵（默认）
fmat   B;           // float  矩阵
cx_mat C;           // complex<double> 矩阵

// ── 向量（本质上是单列/单行矩阵） ──
vec    v;           // 列向量，等价于 colvec
colvec w;           // 列向量
rowvec r;           // 行向量

// ── 稀疏矩阵 ──
sp_mat S;           // 稀疏 double 矩阵

// ── 索引向量 ──
uvec idx;           // 无符号整型向量，常用于存放 find() 返回的索引
```

---

## 3. 矩阵构造（Matrix Construction）

```cpp
// ── 特殊矩阵 ──
mat Z = zeros<mat>(4, 3);      // 全零矩阵 4×3
mat O = ones<mat>(4, 3);       // 全一矩阵 4×3
mat E = eye<mat>(4, 4);        // 单位矩阵 4×4
mat R = randu<mat>(4, 3);      // 均匀分布 [0,1] 随机矩阵
mat N = randn<mat>(4, 3);      // 标准正态分布随机矩阵

// ── 向量构造 ──
vec x = linspace<vec>(0, 1, 5);         // 在 [0,1] 间均匀取 5 个点 → 0, 0.25, 0.5, 0.75, 1.0
vec y = regspace<vec>(0, 2, 10);        // 0:2:10 → 0,2,4,6,8,10 （类似 MATLAB colon 操作符）
vec z = regspace<vec>(0, 1, 5);         // 0:1:5  → 0,1,2,3,4,5

// ── 初始化列表（C++11） ──
mat A = {
    {1, 2, 3},
    {4, 5, 6}
};

// ── 填充 ──
mat B(4, 4);
B.fill(3.14);

// ── 动态分配 ──
mat C(100, 200);          // 不初始化元素
mat D(100, 200, fill::zeros);  // 指定填充
```

---

## 4. 访问与子矩阵（Access & Submatrices）

```cpp
mat A = randu<mat>(5, 5);

// ── 单元素访问 ──
double val = A(2, 3);       // 第 2 行第 3 列
A(1, 2) = 9.0;              // 写

// ── 行列提取 ──
rowvec r = A.row(2);        // 第 2 行（返回行向量）
colvec c = A.col(3);        // 第 3 列（返回列向量）

// ── 子矩阵 ──
mat sub = A(span(1, 3), span(2, 4));       // 行 1~3，列 2~4 的子矩阵
mat sub2 = A.submat(1, 2, 3, 4);           // 等价：左上角(1,2) 到右下角(3,4)
mat sub3 = A.rows(0, 2);                   // 第 0~2 行（含两端）
mat sub4 = A.cols(1, 3);                   // 第 1~3 列（含两端）

// ── 首/尾行（列） ──
mat head = A.head_rows(3);                 // 前 3 行
mat tail = A.tail_rows(2);                 // 后 2 行
mat head_cols = A.head_cols(3);            // 前 3 列

// ── 对角线 ──
vec d = A.diag();                           // 主对角线
vec d1 = A.diag(1);                         // 上偏移 1 的对角线

// ── 大小查询 ──
int nr = A.n_rows;      // 行数
int nc = A.n_cols;      // 列数
int ne = A.n_elem;      // 总元素数
bool em = A.is_empty(); // 是否为空
```

---

## 5. 算术运算（Arithmetic）

```cpp
mat A = randu<mat>(3, 3);
mat B = randu<mat>(3, 3);

mat C = A + B;           // 矩阵加法
mat D = A - B;           // 矩阵减法
mat E = A * B;           // 矩阵乘法
mat F = A % B;           // 逐元素乘法（Hadamard 积）
mat G = A / B;           // 逐元素除法

mat At = A.t();          // 转置
mat Ai = inv(A);         // 逆矩阵

// ── 标量运算 ──
mat S = 2.0 * A;
mat S2 = A / 3.0;
```

---

## 6. 归约与统计（Reductions & Statistics）

```cpp
mat A = randu<mat>(4, 5);

double s = accu(A);                 // 所有元素之和
double m = mean(mean(A));           // 全部元素的均值（嵌套调用）
double v = var(vec(A));             // 方差（注意先将矩阵展为向量）
double sd = stddev(vec(A));         // 标准差

vec col_sum = sum(A, 0);            // 按列求和，返回行向量
vec row_sum = sum(A, 1);            // 按行求和，返回列向量
vec col_mean = mean(A, 0);          // 按列求均值
vec row_mean = mean(A, 1);          // 按行求均值

double mn = min(A);                 // 全局最小值
double mx = max(A);                 // 全局最大值

uvec idx_row, idx_col;
double mn_val = min(A, idx_row, idx_col); // 同时返回最小值及其位置

// ── 向量运算 ──
vec u = {1, 2, 3};
vec v = {4, 5, 6};

double dp = dot(u, v);              // 点积 → 1*4 + 2*5 + 3*6 = 32
vec    cp = cross(u, v);            // 叉积（仅 3 维）
double n2 = norm(u, 2);             // 2-范数（Euclidean 范数）
double n1 = norm(u, 1);             // 1-范数
double ni = norm(u, "inf");         // 无穷范数
```

---

## 7. 逐元素函数（Element-wise Functions）

```cpp
mat A = randu<mat>(3, 3);

mat B = abs(A);          // 绝对值
mat C = sqrt(A);         // 平方根
mat D = log(A);          // 自然对数
mat E = log10(A);        // 以 10 为底对数
mat F = exp(A);          // 指数
mat G = pow(A, 2);       // 平方

mat H = sin(A);          // 正弦
mat I = cos(A);          // 余弦
mat J = tan(A);          // 正切
mat K = asin(A);         // 反正弦
mat L = acos(A);         // 反余弦
mat M = atan(A);         // 反正切

mat N = floor(A);        // 向下取整
mat O = ceil(A);         // 向上取整
mat P = round(A);        // 四舍五入
mat Q = trunc(A);        // 截断取整
```

---

## 8. 线性代数（Linear Algebra）

```cpp
// ── 求解线性方程组 Ax = b ──
mat A = randu<mat>(4, 4);
vec b = randu<vec>(4);
vec x = solve(A, b);                // 等价于 MATLAB 的 A\b

// ── 矩阵分解 ──
mat A = randu<mat>(5, 5);

// LU 分解：P * A = L * U
mat L, U;
lu(L, U, A);

// QR 分解：A = Q * R
mat Q, R;
qr(Q, R, A);

// Cholesky 分解：A = L * L^T （A 必须对称正定）
mat L_chol = chol(A * A.t());

// SVD 分解：A = U * S * V^T
mat U_svd, V_svd;
vec S_svd;
svd(U_svd, S_svd, V_svd, A);

// ── 特征值 ──
vec eigval;
mat eigvec;
eig_sym(eigval, eigvec, A * A.t());      // 对称矩阵特征值分解
// eig_gen(eigval, eigvec, A);            // 一般矩阵特征值分解

// ── 其他 ──
double d = det(A);                        // 行列式
double rc = rcond(A);                     // 条件数的倒数
int    r = rank(A);                       // 矩阵的秩
mat    N = null(A);                       // 零空间基
mat    Pi = pinv(A);                      // Moore-Penrose 伪逆
```

---

## 9. MATLAB 风格命令

```cpp
// ── 拼接 ──
mat A = randu<mat>(3, 2);
mat B = randu<mat>(3, 2);
mat H = join_rows(A, B);     // 水平拼接（左右），要求行数相同
mat V = join_cols(A, B);     // 垂直拼接（上下），要求列数相同

// ── 复制与重塑 ──
mat R = repmat(A, 2, 3);     // 将 A 按行复制 2 次、按列复制 3 次
mat S = reshape(A, 6, 1);    // 重塑为 6×1（按列填充）

// ── 排序 ──
mat Sorted = sort(A);        // 每列独立升序排列
mat Sorted2 = sort(A, 1);    // 每行独立升序排列

// ── 去重 ──
vec v = {1, 2, 1, 3, 2, 4};
vec u = unique(v);            // 返回 {1,2,3,4}

// ── 查找 ──
mat A = randu<mat>(3, 3);
uvec idx = find(A > 0.5);    // 返回满足条件的元素的线性索引（列优先）
uvec idx2 = find(A > 0.5, 2);// 最多找 2 个

// ── 直方图 ──
vec data = randn<vec>(1000);
vec counts, centers;
hist(counts, centers, data, 10);  // 10 个等距 bin

// ── 卷积与 FFT ──
vec a = {1, 2, 3};
vec b = {4, 5, 6};
vec c = conv(a, b);           // 卷积

vec signal = randu<vec>(1024);
cx_vec fft_result = fft(signal);         // FFT
cx_vec ifft_result = ifft(fft_result);   // IFFT
```

---

## 10. 文件 I/O

```cpp
mat A = randu<mat>(5, 5);

// ── MATLAB .mat 格式 ──
A.save("data.mat");              // 保存为 .mat 文件
A.load("data.mat");              // 从 .mat 文件加载

// ── CSV 格式 ──
A.save("data.csv", csv_ascii);           // 保存为 CSV
mat B;
B.load("data.csv");                      // 从 CSV 加载

// ── 文本格式（Armadillo 自有格式） ──
A.save("data.txt", raw_ascii);

// ── 二进制格式（速度快，文件小） ──
A.save("data.bin", arma_binary);

// ── 在 HDF5 中保存/加载（需要 HDF5 支持） ──
A.save("data.h5", hdf5_binary);

// ── 打印到控制台 ──
A.print("矩阵 A：");
arma::cout << "A = \n" << A << arma::endl;
```

---

## 11. 综合示例：多项式拟合

```cpp
#include <armadillo>
using namespace arma;

int main() {
    // ── 数据点 ──
    vec x = linspace<vec>(0, 4, 5);          // x = [0, 1, 2, 3, 4]
    vec y = {1.1, 3.9, 9.0, 16.1, 25.0};    // 观测值

    // ── 构造 Vandermonde 矩阵： [x^2, x, 1] ──
    mat A = join_rows(x % x, x, ones<vec>(5));

    // ── 最小二乘求解 ──
    vec coeff = solve(A, y);

    coeff.print("多项式系数 (c2, c1, c0)：");

    // ── 预测 ──
    vec x_pred = linspace<vec>(0, 4, 100);
    mat A_pred = join_rows(x_pred % x_pred, x_pred, ones<vec>(100));
    vec y_pred = A_pred * coeff;

    y_pred.save("prediction.csv", csv_ascii);

    return 0;
}
```

---

## 12. 编译示例

```bash
# 使用 g++
g++ -std=c++17 -O2 main.cpp -o main -larmadillo -lopenblas

# 使用 cmake（CMakeLists.txt）
find_package(Armadillo REQUIRED)
target_link_libraries(my_program PRIVATE Armadillo::Armadillo)
```

---

# 第二篇：Blaze

## 1. 概述

**Blaze** 是一个高性能 C++ 数学库，采用**头文件唯一（header-only）** 设计，无需链接额外库即可使用。它通过**表达式模板（Expression Templates）** 技术实现了极致的运行效率，在矩阵向量运算方面常超越优化后的 BLAS。

| 项目 | 说明 |
|------|------|
| 头文件 | `#include <blaze/Blaze.h>` |
| 命名空间 | `blaze` |
| 许可证 | BSD 3-Clause |
| 官网 | https://bitbucket.org/blaze-lib/blaze/ |
| 下载 | https://bitbucket.org/blaze-lib/blaze/downloads/ |

### 安装方式

Blaze 是 header-only 库，下载解压后将 `blaze/` 文件夹复制到项目 include 路径即可：

```bash
# 方法一：直接复制到系统 include 路径
cp -r blaze /usr/local/include/

# 方法二：在 CMake 中使用
# cmake/CMakeLists.txt:
find_package(blaze REQUIRED)
target_link_libraries(my_program PRIVATE blaze::blaze)
```

### 编译选项

```bash
# 基础编译（无需链接任何库）
g++ -std=c++17 -O2 -DNDEBUG main.cpp -o main

# 启用 BLAS/LAPACK 加速（链接 OpenBLAS）
g++ -std=c++17 -O2 -DNDEBUG -march=native main.cpp -o main -lopenblas

# MSVC（Windows）
cl /std:c++17 /O2 /DNDEBUG main.cpp
```

---

## 2. 核心类型（Key Types）

```cpp
#include <blaze/Blaze.h>
using namespace blaze;

// ── 动态矩阵（堆分配） ──
DynamicMatrix<double> A(4, 3);                  // double 矩阵 4×3
DynamicMatrix<float>  B(4, 3);                  // float  矩阵 4×3
DynamicMatrix<complex<double>> C(4, 3);         // 复数矩阵 4×3

// ── 静态矩阵（栈分配，编译期固定大小） ──
StaticMatrix<double, 3, 3> D;                   // 3×3 固定大小矩阵，零开销
StaticMatrix<float, 4, 4>  E;                   // 4×4 固定大小矩阵

// ── 动态向量 ──
DynamicVector<double> v(100);                   // double 向量，长度 100
DynamicVector<float>  w(100);                   // float  向量

// ── 静态向量 ──
StaticVector<double, 3> u;                      // 3 元素固定向量

// ── 稀疏矩阵 ──
CompressedMatrix<double> S(1000, 1000);          // 稀疏 double 矩阵
```

---

## 3. 构造与初始化（Construction & Initialization）

```cpp
// ── 动态矩阵 ──
DynamicMatrix<double> A(3, 4);           // 3×4，元素未初始化
DynamicMatrix<double> B(3, 4, 0.0);      // 3×4，全部初始化为 0.0

// ── 初始化列表 ──
DynamicMatrix<double> C = {
    {1, 2, 3},
    {4, 5, 6}
};

// ── 静态矩阵初始化列表 ──
StaticMatrix<double, 2, 2> D = {
    {1, 2},
    {3, 4}
};

// ── 向量初始化列表 ──
DynamicVector<double> v = {1, 2, 3, 4, 5};

// ── 工厂函数 ──
auto Z = zero<double>(4, 3);             // 全零矩阵
auto O = ones<double>(4, 3);             // 全一矩阵
auto I = identity<double>(4);            // 单位矩阵

// ── 自定义初始化（generate） ──
DynamicMatrix<double> M(4, 4);
generate(M, [](size_t i, size_t j) { return double(i + j); });

// ── 填充 ──
DynamicMatrix<double> N(4, 4);
fill(N, 3.14);

// ── 线性间隔（需要单独头文件） ──
#include <blaze/math/typetraits/IsVector.h>
auto x = linspace(0.0, 1.0, 10);         // 在 [0,1] 均匀取 10 个点
```

---

## 4. 访问与子矩阵（Access & Submatrices）

```cpp
DynamicMatrix<double> A = {
    {1, 2, 3, 4},
    {5, 6, 7, 8},
    {9, 10, 11, 12}
};

// ── 单元素访问 ──
double val = A(1, 2);                    // 第 1 行第 2 列 → 7
A(0, 0) = 99.0;                          // 写

// ── 行 / 列 ──
auto r = row(A, 1);                      // 第 1 行 → [5, 6, 7, 8]
auto c = column(A, 2);                   // 第 2 列 → [3, 7, 11]

// ── 子矩阵 ──
auto sub = submatrix(A, 1, 1, 2, 2);     // 从 (1,1) 开始取 2×2 子块

// ── 指定行 / 列集合 ──
auto rows_sel = rows(A, {0, 2});          // 选择第 0 行和第 2 行
auto cols_sel = columns(A, {1, 3});       // 选择第 1 列和第 3 列

// ── 对角线 ──
auto d_main = band(A, 0);                 // 主对角线
auto d_super = band(A, 1);                // 上对角线
auto d_sub = band(A, -1);                 // 下对角线

// ── 大小查询 ──
size_t nr = A.rows();
size_t nc = A.columns();
size_t ne = A.capacity();

// ── 切片范围 ──
auto slice = submatrix(A, 0, 0, 2, 3);    // 前 2 行前 3 列
```

---

## 5. 运算（Operations）

```cpp
DynamicMatrix<double> A = {{1, 2}, {3, 4}};
DynamicMatrix<double> B = {{5, 6}, {7, 8}};

DynamicMatrix<double> C = A + B;          // 矩阵加法
DynamicMatrix<double> D = A - B;          // 矩阵减法
DynamicMatrix<double> E = A * B;          // 矩阵乘法
DynamicMatrix<double> F = A % B;          // 逐元素乘法
DynamicMatrix<double> G = A / B;          // 逐元素除法

// ── 转置与共轭转置 ──
auto At = trans(A);                       // 转置
auto Ac = ctrans(A);                      // 共轭转置

// ── 逆矩阵 ──
auto Ai = inv(A);                         // 需要 LAPACK 支持

// ── 标量运算 ──
DynamicMatrix<double> H = 2.0 * A;
DynamicMatrix<double> I = A / 3.0;

// ── 向量运算 ──
DynamicVector<double> u = {1, 2, 3};
DynamicVector<double> v = {4, 5, 6};

double dp = u * v;                                  // 点积（向量内积）
auto   cv = cross(u, v);                            // 叉积（3 维）
double l2 = l2Norm(u);                              // 2-范数
double l1 = l1Norm(u);                              // 1-范数
double li = lInfNorm(u);                            // 无穷范数
```

---

## 6. 逐元素变换（Element-wise Mapping）

```cpp
DynamicMatrix<double> A = rand<double>(3, 3);

// ── map：返回新矩阵，不修改原矩阵 ──
auto B = map(A, [](double x) { return sin(x); });   // 逐元素求 sin
auto C = map(A, [](double x) { return x * x; });    // 逐元素平方

// ── forEach：原地修改 ──
forEach(A, [](double& x) { x = sqrt(x); });        // 原地开方

// ── 常用数学函数 ──
auto D = abs(A);                                     // 绝对值
auto E = sqrt(A);                                    // 平方根
auto F = exp(A);                                     // 指数
auto G = log(A);                                     // 自然对数

// ── 三角函数 ──
auto H = sin(A);
auto I = cos(A);
auto J = tan(A);
```

---

## 7. 归约与统计（Reductions & Statistics）

```cpp
DynamicMatrix<double> A = rand<double>(4, 5);

double s = sum(A);                     // 全部元素之和
double m = mean(A);                    // 全部元素均值
double mn = min(A);                    // 全局最小值
double mx = max(A);                    // 全局最大值

// ── 按行 / 按列归约 ──
auto col_sum = sum<rowwise>(A);        // 按列求和（返回行向量）
auto row_sum = sum<columnwise>(A);     // 按行求和（返回列向量）
auto col_mean = mean<rowwise>(A);      // 按列求均值
auto row_mean = mean<columnwise>(A);   // 按行求均值

// ── 范数 ──
double n1 = l1Norm(A);                 // 1-范数
double n2 = l2Norm(A);                 // 2-范数（Frobenius 范数）
double ni = lInfNorm(A);               // 无穷范数
double nf = frobeniusNorm(A);          // Frobenius 范数

// ── 自定义归约 ──
double custom = reduce(A, [](double a, double b) { return a + b; }, 0.0);
```

---

## 8. 线性代数（Linear Algebra）

```cpp
DynamicMatrix<double> A = {{3, 1}, {1, 2}};
DynamicVector<double> b = {5, 4};

// ── 求解线性方程组 Ax = b ──
DynamicVector<double> x = solve(A, b);          // 需要 LAPACK

// ── QR 分解 ──
auto qr_decomp = qr(A);
auto Q = qr_decomp[0];                           // 正交矩阵 Q
auto R = qr_decomp[1];                           // 上三角矩阵 R

// ── LU 分解 ──
auto lu_decomp = lu(A);
auto L = lu_decomp[0];                           // 下三角 L
auto U = lu_decomp[1];                           // 上三角 U
auto P = lu_decomp[2];                           // 置换矩阵 P

// ── SVD 分解 ──
auto svd_decomp = svd(A);
auto U_svd = svd_decomp[0];                      // 左奇异向量
auto S_svd = svd_decomp[1];                      // 奇异值（向量形式）
auto V_svd = svd_decomp[2];                      // 右奇异向量

// ── 特征值 ──
auto eig = eigenvalues(A);                       // 返回复数向量
```

---

## 9. 性能优化技巧

### 9.1 使用静态矩阵（StaticMatrix）避免堆分配

对于 3×3、4×4、6×6 等编译期已知大小的矩阵，使用 `StaticMatrix` 代替 `DynamicMatrix`，数据完全在栈上分配，无动态内存开销：

```cpp
// ── 推荐：栈分配，零开销 ──
StaticMatrix<double, 3, 3> A = {
    {1, 2, 3},
    {4, 5, 6},
    {7, 8, 9}
};

// ── 不推荐（小矩阵没必要堆分配） ──
DynamicMatrix<double> B(3, 3);
```

### 9.2 使用表达式模板避免临时变量

Blaze 的表达式模板可自动**延迟求值**并**融合循环**，避免创建不必要的临时矩阵：

```cpp
// ── 下面这行不会创建临时矩阵 ──
DynamicMatrix<double> R = A * B + C * D + E * F;  // 编译期为单个融合循环

// ── 等价但更慢的手写方式 ──
auto T1 = A * B;                                   // 临时变量
auto T2 = C * D;                                   // 临时变量
DynamicMatrix<double> R = T1 + T2 + E * F;
```

### 9.3 编译优化选项

```bash
# 必须开启的选项
-O2 或 -O3
-DNDEBUG                      # 关闭运行时检查，大幅提速
-march=native                 # 启用 CPU 特定指令集（AVX、AVX2、FMA 等）

# 可选：启用 BLAS 加速（针对大矩阵）
-lopenblas
```

### 9.4 线程并行

Blaze 默认使用 OpenMP 并行化大矩阵运算。编译时需开启 OpenMP：

```bash
g++ -fopenmp -O2 -DNDEBUG main.cpp -o main
```

可通过环境变量控制线程数：

```bash
export OMP_NUM_THREADS=4     # Linux / macOS
set OMP_NUM_THREADS=4        # Windows
```

### 9.5 数据类型选择

- 优先使用 `double`（8 字节）获得最高精度
- 在 GPU 或内存受限场景下使用 `float`（4 字节）
- 对整数类型运算，可用 `DynamicMatrix<int>`，但线性代数分解通常不支持整数类型

---

## 10. 稀疏矩阵（Sparse Matrix）

```cpp
// ── 构造 ──
CompressedMatrix<double> S(5, 5);           // 5×5 稀疏矩阵

// ── 插入非零元素 ──
S(0, 0) = 1.0;
S(1, 2) = 2.0;
S(3, 4) = 3.0;
S.finalize();                                // 插入完成后调用，优化存储结构

// ── 稀疏矩阵运算 ──
DynamicVector<double> v = {1, 2, 3, 4, 5};
DynamicVector<double> y = S * v;             // 稀疏矩阵乘向量（高效）

// ── 查看非零元素信息 ──
size_t nnz = S.nonZeros();                   // 非零元素个数
size_t rows = S.rows();
size_t cols = S.columns();
```

---

## 11. 综合示例：线性回归

```cpp
#include <blaze/Blaze.h>
#include <iostream>
using namespace blaze;

int main() {
    // ── 数据点 ──
    DynamicVector<double> x = {0, 1, 2, 3, 4};
    DynamicVector<double> y = {1.1, 3.9, 9.0, 16.1, 25.0};

    // ── 构造设计矩阵： [x^2, x, 1] ──
    size_t n = x.size();
    DynamicMatrix<double> A(n, 3);
    for (size_t i = 0; i < n; ++i) {
        A(i, 0) = x[i] * x[i];
        A(i, 1) = x[i];
        A(i, 2) = 1.0;
    }

    // ── 最小二乘求解 (A^T A) * coeff = A^T * y ──
    auto AtA = trans(A) * A;
    auto Atb = trans(A) * y;
    DynamicVector<double> coeff = solve(AtA, Atb);

    std::cout << "系数 (c2, c1, c0) = " << coeff << "\n";

    // ── 预测 ──
    DynamicVector<double> x_pred = linspace(0.0, 4.0, 100);
    DynamicVector<double> y_pred(100);
    for (size_t i = 0; i < 100; ++i) {
        y_pred[i] = coeff[0] * x_pred[i] * x_pred[i]
                  + coeff[1] * x_pred[i]
                  + coeff[2];
    }

    return 0;
}
```

---

## 12. 与 Eigen / Armadillo 的对比

| 特性 | Armadillo | Blaze | Eigen |
|------|-----------|-------|-------|
| 语法风格 | MATLAB 风格 | 现代 C++ | 现代 C++ |
| 安装方式 | 需编译链接 | Header-only | Header-only |
| 表达式模板 | ✓ | ✓（核心设计） | ✓ |
| 小矩阵优化 | 一般 | 优秀（StaticMatrix） | 优秀 |
| BLAS 加速 | 必须 | 可选 | 可选 |
| 稀疏矩阵 | ✓（sp_mat） | ✓（CompressedMatrix） | ✓（SparseMatrix） |
| 学习曲线 | 低（MATLAB 用户友好） | 中 | 中 |
| 文档丰富度 | 非常丰富 | 较丰富 | 非常丰富 |

### 如何选择？

- **从 MATLAB 迁移 → 选 Armadillo**：语法几乎一一对应，迁移成本最低。
- **追求极致性能 → 选 Blaze**：表达式模板技术最成熟，且 header-only 部署简单。
- **需要兼顾两者 → 可在同一项目中使用两者**（注意命名空间隔离），Armadillo 做快速原型和 I/O，Blaze 做核心计算。

---

## 附录：常用编译命令速查

### Armadillo

```bash
# Linux / macOS（使用 OpenBLAS）
g++ -std=c++17 -O2 -march=native main.cpp -o main -larmadillo -lopenblas -lpthread

# Windows（MSVC + vcpkg）
cl /std:c++17 /O2 /EHsc main.cpp /link armadillo.lib openblas.lib
```

### Blaze

```bash
# Linux / macOS（纯 header-only，无额外链接）
g++ -std=c++17 -O2 -DNDEBUG -march=native main.cpp -o main

# 启用 OpenMP 并行
g++ -std=c++17 -O2 -DNDEBUG -march=native -fopenmp main.cpp -o main

# Windows（MSVC） 
cl /std:c++17 /O2 /DNDEBUG main.cpp
```

### 检查 Blaze 版本

```cpp
#include <blaze/Blaze.h>
#include <iostream>
int main() {
    std::cout << "Blaze 版本: " << BLAZE_MAJOR_VERSION << "."
              << BLAZE_MINOR_VERSION << "\n";
    return 0;
}
```

### 检查 Armadillo 版本

```cpp
#include <armadillo>
#include <iostream>
int main() {
    std::cout << "Armadillo 版本: " << arma_version::major << "."
              << arma_version::minor << "\n";
    return 0;
}
```

---

> **参考资料**
> - Armadillo 官方文档：https://arma.sourceforge.net/docs.html
> - Blaze 官方文档：https://bitbucket.org/blaze-lib/blaze/wiki/Home
> - Blaze 在线文档（HTML）：https://blaze-lib.org/blaze-doc/
