# Eigen 库详解 — C++ 矩阵计算（对标 NumPy）

## 概述

Eigen 是 C++ 头文件库，**无需编译，直接 #include 即可使用**。数学建模、机器学习、3D几何、仿真计算的标配。

**包含路径：** `#include <Eigen/Dense>`（包含核心、几何、LU、QR、SVD 等全部功能）

**安装位置：** `include/Eigen/`（已下载）

**编译：** 只需添加 `-I"路径/Eigen/"`，无链接库

---

## 一、核心：矩阵与向量

### 1.1 基本类型

| 类型 | 说明 | 对应 NumPy |
|------|------|-----------|
| `Eigen::MatrixXd` | double 动态矩阵 (rows,cols) | `np.ndarray` |
| `Eigen::MatrixXi` | int 动态矩阵 | — |
| `Eigen::MatrixXf` | float 动态矩阵 | — |
| `Eigen::VectorXd` | double 动态列向量 (size) | `np.array(shape=(n,))` |
| `Eigen::RowVectorXd` | double 动态行向量 | — |
| `Eigen::Matrix3d` | double 3×3 固定矩阵 | — |
| `Eigen::Vector3d` | double 3 维列向量 | — |

```cpp
#include <Eigen/Dense>
using namespace Eigen;

// 动态矩阵
MatrixXd m(3, 4);          // 3×4 double 矩阵
MatrixXf f(2, 2);          // 2×2 float 矩阵
VectorXd v(5);             // 5 维列向量
RowVectorXd rv(3);         // 3 维行向量

// 固定大小（栈分配，更快）
Matrix3d m33;              // 3×3 double
Vector3d v3;               // 3 维列向量
Vector4f v4;               // 4 维 float
```

### 1.2 初始化

```cpp
// 零矩阵
MatrixXd::Zero(rows, cols);
Matrix3d::Zero();

// 全 1
MatrixXd::Ones(rows, cols);

// 单位矩阵
MatrixXd::Identity(rows, cols);

// 常量矩阵
MatrixXd::Constant(rows, cols, value);

// 随机矩阵（均匀分布 [-1,1]）
MatrixXd::Random(rows, cols);

// Linspace（需要自己构造）
// Eigen 没有直接 linspace，可以手动：
int N = 10;
VectorXd t(N);
for (int i = 0; i < N; ++i) t(i) = 0.1 * i;

// 用逗号初始化
MatrixXd m(2, 3);
m << 1, 2, 3,
     4, 5, 6;

// 从数组/vector 构造
double arr[] = {1, 2, 3, 4, 5, 6};
MatrixXd m = Map<MatrixXd>(arr, 2, 3);
// 或
std::vector<double> vec = {1,2,3,4};
VectorXd v = VectorXd::Map(vec.data(), vec.size());
```

### 1.3 访问与赋值

```cpp
m(i, j);           // 读元素 (i 行 j 列)
m(i, j) = x;       // 写元素
v(i);              // 向量元素

// 行列操作
m.row(i);           // 第 i 行（返回引用）
m.col(j);           // 第 j 列（返回引用）
m.block(i, j, rows, cols); // 子块 (i,j) 起 rows×cols

// 特殊块
m.topLeftCorner(rows, cols);
m.bottomRightCorner(rows, cols);
m.topRows(n);
m.bottomRows(n);
m.leftCols(n);
m.rightCols(n);

// 范围（类似 Python 切片）
// Eigen 3.4+ 支持 placeholders::last, seq, all
using namespace Eigen::placeholders;
m(seq(0, 4), all);          // 前 5 行，所有列
m(all, seq(0, last, 2));    // 所有行，每隔一列
```

### 1.4 大小与属性

```cpp
m.rows();           // 行数
m.cols();           // 列数
m.size();           // 总元素数
m.resize(rows, cols);  // 改变大小（原有数据丢失）
m.rows(v);          // 向量长度
```

---

## 二、运算

### 2.1 算术运算

```cpp
// 加减
MatrixXd C = A + B;
MatrixXd D = A - B;
A += B;             // 原地

// 矩阵乘法
MatrixXd C = A * B;           // 数学矩阵乘法
VectorXd y = A * x;           // 矩阵×向量
v = w * A;                    // 行向量×矩阵（w 是 RowVectorXd）

// 标量运算
MatrixXd C = 2.0 * A;
A *= 2.0;

// 哈达玛积（逐元素乘）
MatrixXd C = A.cwiseProduct(B);

// 逐元素除
MatrixXd C = A.cwiseQuotient(B);

// 逐元素加减常数
MatrixXd C = A.array() + 1.0;  // 转成数组视图
MatrixXd D = A.array().sin();  // 逐元素求 sin
```

### 2.2 数组操作（类似 NumPy 逐元素运算）

需要先 `.array()` 转成数组视图，运算完再 `.matrix()` 转回。

```cpp
// 逐元素数学函数
A.array().sin();
A.array().cos();
A.array().tan();
A.array().asin();
A.array().acos();
A.array().atan();
A.array().sinh();
A.array().cosh();
A.array().tanh();
A.array().exp();
A.array().log();
A.array().log10();
A.array().sqrt();
A.array().pow(x);
A.array().abs();
A.array().floor();
A.array().ceil();
A.array().round();

// 条件
A.array() > 0;                           // 返回 bool 数组
(A.array() > 0).select(B, C);            // 类似 np.where(A>0, B, C)
(A.array() > 0).count();                 // 统计 true 个数
(A.array() > 0).all();                   // 是否全部 true
(A.array() > 0).any();                   // 是否有 true

// 裁剪
A.array().min(1.0);                      // 类似 np.minimum(A, 1)
A.array().max(0.0);                      // 类似 np.maximum(A, 0)

// 组合
A.array().cwiseMin(B);                   // 逐元素 min
A.array().cwiseMax(B);                   // 逐元素 max
```

### 2.3 规约运算

```cpp
m.sum();                  // 所有元素和
m.prod();                 // 所有元素积
m.mean();                 // 平均值
m.minCoeff();             // 最小值
m.maxCoeff();             // 最大值
m.trace();                // 迹（对角线之和）

// 带位置的最小值
int i, j;
double minVal = m.minCoeff(&i, &j);   // i,j 接收位置

// 按行/列
m.colwise().sum();        // 每列和（返回行向量）
m.rowwise().sum();        // 每行和（返回列向量）
m.colwise().mean();       // 每列均值
m.rowwise().maxCoeff();   // 每行最大值
```

### 2.4 转置、逆、行列式

```cpp
m.transpose();            // 转置
m.transposeInPlace();     // 原地转置
m.adjoint();              // 共轭转置（实矩阵 = transpose）
m.conjugate();            // 共轭

m.inverse();              // 逆矩阵
m.determinant();          // 行列式

// 伪逆（SVD 分解）
BDCSVD<MatrixXd> svd(m, ComputeThinU | ComputeThinV);
MatrixXd pinv = svd.pseudoinverse();
```

### 2.5 范数与归一化

```cpp
v.norm();                 // L2 范数（欧几里得范数）
v.squaredNorm();          // L2 范数平方
v.lpNorm<1>();            // L1 范数
v.lpNorm<Eigen::Infinity>(); // 无穷范数
v.normalized();           // 归一化向量（返回新向量）
v.normalize();            // 原地归一化

m.norm();                 // Frobenius 范数
m.lpNorm<1>();            // L1 范数（所有元素绝对值之和）
m.lpNorm<Eigen::Infinity>(); // 无穷范数（最大绝对值）
```

---

## 三、线性代数求解

### 3.1 线性方程组 Ax = b

```cpp
// 方法一：PartialPivLU（通用，中等大小）
VectorXd x = A.partialPivLu().solve(b);

// 方法二：FullPivLU（更稳定，更慢）
VectorXd x = A.fullPivLu().solve(b);

// 方法三：HouseholderQR（最小二乘，超定系统）
VectorXd x = A.householderQr().solve(b);

// 方法四：LLT（对称正定矩阵，最快）
VectorXd x = A.llt().solve(b);

// 方法五：LDLT（对称不定矩阵）
VectorXd x = A.ldlt().solve(b);

// 方法六：BDCSVD（最稳定，最慢）
VectorXd x = A.bdcSvd(ComputeThinU | ComputeThinV).solve(b);
```

### 3.2 SVD 分解

```cpp
// JacobiSVD（更精确）
JacobiSVD<MatrixXd> svd(A, ComputeThinU | ComputeThinV);
MatrixXd U = svd.matrixU();
MatrixXd V = svd.matrixV();
VectorXd S = svd.singularValues();

// BDCSVD（更快，大矩阵）
BDCSVD<MatrixXd> svd(A, ComputeThinU | ComputeThinV);
```

### 3.3 特征值分解

```cpp
// 实对称矩阵
SelfAdjointEigenSolver<MatrixXd> eigensolver(A);
VectorXd eigenvalues = eigensolver.eigenvalues();
MatrixXd eigenvectors = eigensolver.eigenvectors();

// 一般方阵
EigenSolver<MatrixXd> eigensolver(A);
// eigenvalues 是复数型
```

### 3.4 QR 分解

```cpp
HouseholderQR<MatrixXd> qr(A);
MatrixXd Q = qr.householderQ();
MatrixXd R = qr.matrixQR().triangularView<Eigen::Upper>();

// 列主元 QR
ColPivHouseholderQR<MatrixXd> qr(A);
```

### 3.5 Cholesky 分解

```cpp
// LLT（对称正定）
LLT<MatrixXd> llt(A);
MatrixXd L = llt.matrixL();

// LDLT（对称不定）
LDLT<MatrixXd> ldlt(A);
```

---

## 四、几何（3D 坐标、旋转）

```cpp
#include <Eigen/Geometry>

// 旋转矩阵（3×3）
Matrix3d R = AngleAxisd(M_PI/4, Vector3d::UnitZ()).toRotationMatrix();

// 四元数
Quaterniond q(AngleAxisd(M_PI/3, Vector3d::UnitX()));
q.normalize();

// 欧拉角
Vector3d euler = R.eulerAngles(2, 1, 0);  // ZYX

// 变换矩阵（4×4 齐次坐标）
Translation3d t(1, 2, 3);
Affine3d T = t * AngleAxisd(M_PI/4, Vector3d::UnitZ());
Vector3d p_transformed = T * Vector3d(0, 0, 0);

// 向量叉积 / 点积
double dot = a.dot(b);
Vector3d cross = a.cross(b);
```

---

## 五、数值求解器

### 5.1 最小二乘

```cpp
// 超定系统 Ax = b 的最小二乘解
VectorXd x = A.bdcSvd(ComputeThinU | ComputeThinV).solve(b);

// 加权最小二乘
// 等价于 (W^(1/2) * A) * x = (W^(1/2) * b)
```

### 5.2 非线性求解（无内建，需配合其他库）

---

## 六、性能优化

### 6.1 编译选项

```bash
# 启用优化（必须）
g++ -O2 -DNDEBUG -march=native main.cpp
```

### 6.2 固定大小 vs 动态

```cpp
// 固定大小：栈分配，更快
Matrix4d m;        // 16 个 double = 128 字节
MatrixXd m(4,4);   // 堆分配，略慢
```

### 6.3 对齐问题

```cpp
// 如果类成员包含固定大小 Eigen 类型，需要：
class MyClass {
    EIGEN_MAKE_ALIGNED_OPERATOR_NEW
    Vector4d v;
    Matrix2d m;
};
```

---

## 七、与 NumPy 对应表

| NumPy | Eigen |
|-------|-------|
| `np.array([[1,2],[3,4]])` | `MatrixXd m(2,2); m << 1,2,3,4;` |
| `np.zeros((3,4))` | `MatrixXd::Zero(3,4)` |
| `np.ones((3,4))` | `MatrixXd::Ones(3,4)` |
| `np.eye(3)` | `MatrixXd::Identity(3,3)` |
| `np.random.rand(3,4)` | `MatrixXd::Random(3,4)` |
| `A @ B` | `A * B` |
| `A * B`（逐元素） | `A.cwiseProduct(B)` |
| `A.T` | `A.transpose()` |
| `np.linalg.inv(A)` | `A.inverse()` |
| `np.linalg.det(A)` | `A.determinant()` |
| `np.linalg.solve(A,b)` | `A.llt().solve(b)` |
| `np.linalg.svd(A)` | `JacobiSVD<MatrixXd>(A, ...)` |
| `np.linalg.eig(A)` | `EigenSolver<MatrixXd>(A)` |
| `np.linalg.qr(A)` | `HouseholderQR<MatrixXd>(A)` |
| `A.sum()` | `A.sum()` |
| `A.mean(axis=0)` | `A.colwise().mean()` |
| `np.sin(A)` | `A.array().sin()` |
| `np.where(A>0, B, C)` | `(A.array()>0).select(B, C)` |
| `np.clip(A, 0, 1)` | `A.array().max(0).min(1)` |
| `np.linalg.norm(v)` | `v.norm()` |

---

## 八、完整示例：拟合抛物线

```cpp
#include <iostream>
#include <Eigen/Dense>
using namespace Eigen;
using namespace std;

int main() {
    // 数据点 (x, y)
    VectorXd x(5), y(5);
    x << 0, 1, 2, 3, 4;
    y << 1.1, 3.9, 9.0, 16.1, 25.0;

    // 构造 Vandermonde 矩阵: [x^2, x, 1]
    MatrixXd A(5, 3);
    A.col(2) = VectorXd::Ones(5);
    A.col(1) = x;
    A.col(0) = x.array().square();

    // 最小二乘解 A * coeff = y
    VectorXd coeff = A.bdcSvd(ComputeThinU | ComputeThinV).solve(y);
    cout << "系数: " << coeff.transpose() << endl;
    // 输出应接近 [1, 2, 1]（即 y = x^2 + 2x + 1）

    // 预测
    double x_test = 5.0;
    VectorXd test(3);
    test << x_test*x_test, x_test, 1.0;
    double y_pred = test.dot(coeff);
    cout << "预测 f(5) = " << y_pred << endl;

    return 0;
}
```

编译命令：
```bash
g++ -std=c++17 -O2 -I"D:\桌面\文件\讲解\C++库安装与参考\include" fit.cpp -o fit
```
