# 图像处理与计算机视觉 — OpenCV + stb_image

## 一、OpenCV 概述

OpenCV（Open Source Computer Vision Library）是最流行的计算机视觉库。C++ 版本速度远快于 Python 版。

### 安装
- vcpkg: `vcpkg install opencv4`（推荐，自动编译）
- 或从 https://opencv.org/releases/ 下载预编译二进制
- MinGW 需自行编译（耗时长）

### 核心模块

| 模块 | 功能 |
|------|------|
| `core` | 核心数据结构（Mat、Point、Scalar） |
| `imgproc` | 图像处理（滤波、形态学、几何变换） |
| `highgui` | 窗口显示、鼠标/键盘交互 |
| `imgcodecs` | 图片读写（imread/imwrite） |
| `videoio` | 视频读写、摄像头 |
| `objdetect` | 目标检测（人脸检测等） |
| `features2d` | 特征点（SIFT/SURF/ORB） |
| `calib3d` | 相机标定、3D 重建 |
| `ml` | 机器学习（SVM/KNN/决策树） |
| `dnn` | 深度学习推理 |

```cpp
// 常用包含
#include <opencv2/opencv.hpp>   // 全部模块
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgcodecs.hpp>
using namespace cv;
```

---

## 二、核心数据结构 cv::Mat

### 创建

```cpp
// 3×3 灰度图（8位）
Mat img(300, 400, CV_8UC1);   // 单通道

// 3×3 彩色图（8位3通道）
Mat color(300, 400, CV_8UC3, Scalar(0, 255, 0));  // 绿色

// 浮点矩阵（单通道）
Mat A(3, 3, CV_64FC1);
A = (Mat_<double>(3,3) << 1,2,3, 4,5,6, 7,8,9);

// 从外部数据创建（不复制）
double data[] = {1,2,3,4,5,6};
Mat M(2, 3, CV_64F, data);

// 特殊矩阵
Mat::zeros(rows, cols, CV_8UC3);
Mat::ones(rows, cols, CV_32F);
Mat::eye(3, 3, CV_64F);
```

### 基本属性

```cpp
img.rows;          // 行数（高度）
img.cols;          // 列数（宽度）
img.channels();    // 通道数（1=灰度, 3=BGR, 4=BGRA）
img.depth();       // 深度（CV_8U, CV_32F, CV_64F 等）
img.type();        // 类型（如 CV_8UC3）
img.total();       // 总像素数
img.elemSize();    // 每个元素字节数
img.empty();       // 是否空
```

### 像素访问

```cpp
// 方法一：at（慢，安全）
img.at<uchar>(y, x) = 255;                    // 灰度图
color.at<Vec3b>(y, x) = Vec3b(0, 255, 0);     // 彩色 BGR
double v = A.at<double>(i, j);

// 方法二：ptr（快，推荐）
for (int y = 0; y < img.rows; y++) {
    uchar* row = img.ptr<uchar>(y);
    for (int x = 0; x < img.cols; x++)
        row[x] = 255;
}

// 方法三：data（最底层）
uchar* pixel = img.data + y * img.step + x * img.channels();
```

---

## 三、图像读写

```cpp
// 读取
Mat img = imread("photo.jpg");                    // 默认彩色（IMREAD_COLOR）
Mat gray = imread("photo.jpg", IMREAD_GRAYSCALE); // 灰度
Mat unchanged = imread("photo.jpg", IMREAD_UNCHANGED); // 含 Alpha

// 写入
imwrite("output.jpg", img);                       // JPG
imwrite("output.png", img);                       // PNG
```

---

## 四、图像处理函数

### 4.1 颜色空间转换

```cpp
Mat gray, hsv;
cvtColor(img, gray, COLOR_BGR2GRAY);     // BGR → 灰度
cvtColor(img, hsv, COLOR_BGR2HSV);       // BGR → HSV
cvtColor(hsv, img, COLOR_HSV2BGR);       // HSV → BGR
```

### 4.2 几何变换

```cpp
// 缩放
Mat resized;
resize(img, resized, Size(200, 200));
resize(img, resized, Size(), 0.5, 0.5);  // 按比例缩小 50%

// 旋转
Point2f center(img.cols/2.0, img.rows/2.0);
Mat rot = getRotationMatrix2D(center, 45, 1.0); // 旋转45度
Mat rotated;
warpAffine(img, rotated, rot, img.size());

// 平移
Mat trans = (Mat_<double>(2,3) << 1, 0, 100, 0, 1, 50);
Mat translated;
warpAffine(img, translated, trans, img.size());

// 翻转
flip(img, flipped, 0);   // 垂直翻转（上下）
flip(img, flipped, 1);   // 水平翻转（左右）

// 裁剪
Mat crop = img(Rect(100, 100, 200, 200));  // (x,y,width,height)
```

### 4.3 滤波与平滑

```cpp
Mat dst;

// 均值滤波
blur(img, dst, Size(5, 5));

// 高斯滤波
GaussianBlur(img, dst, Size(5, 5), 1.5);

// 中值滤波（去椒盐噪声好）
medianBlur(img, dst, 5);

// 双边滤波（保边去噪）
bilateralFilter(img, dst, 9, 75, 75);
```

### 4.4 边缘检测

```cpp
Mat edges;

// Canny 边缘检测
Canny(img, edges, 50, 150);

// Sobel 梯度
Mat grad_x, grad_y;
Sobel(img, grad_x, CV_64F, 1, 0);  // x 方向梯度
Sobel(img, grad_y, CV_64F, 0, 1);  // y 方向梯度

// Laplacian
Laplacian(img, laplacian, CV_64F);
```

### 4.5 阈值处理

```cpp
Mat binary;

// 固定阈值
threshold(gray, binary, 128, 255, THRESH_BINARY);
threshold(gray, binary, 128, 255, THRESH_BINARY_INV);  // 反色

// 自适应阈值
adaptiveThreshold(gray, binary, 255, ADAPTIVE_THRESH_GAUSSIAN_C, THRESH_BINARY, 11, 2);

// Otsu 自动阈值
threshold(gray, binary, 0, 255, THRESH_BINARY | THRESH_OTSU);
```

### 4.6 形态学操作

```cpp
Mat kernel = getStructuringElement(MORPH_RECT, Size(3,3));
Mat dst;

erode(img, dst, kernel);       // 腐蚀
dilate(img, dst, kernel);      // 膨胀
morphologyEx(img, dst, MORPH_OPEN, kernel);   // 开运算（先腐蚀后膨胀）
morphologyEx(img, dst, MORPH_CLOSE, kernel);  // 闭运算（先膨胀后腐蚀）
morphologyEx(img, dst, MORPH_GRADIENT, kernel); // 形态学梯度
morphologyEx(img, dst, MORPH_TOPHAT, kernel);   // 顶帽
```

### 4.7 绘图

```cpp
// 画线
line(img, Point(50,50), Point(200,200), Scalar(0,0,255), 2); // BGR 红色

// 画矩形
rectangle(img, Rect(100,100,150,100), Scalar(0,255,0), 2);     // 空心
rectangle(img, Rect(100,100,150,100), Scalar(0,255,0), FILLED); // 实心

// 画圆
circle(img, Point(300,300), 50, Scalar(255,0,0), 2);

// 画椭圆
ellipse(img, Point(300,300), Size(100,50), 0, 0, 360, Scalar(255,255,0), 2);

// 写文字
putText(img, "Hello", Point(50,50), FONT_HERSHEY_SIMPLEX, 1.0, Scalar(255,255,255), 2);
```

### 4.8 直方图

```cpp
// 计算直方图（灰度）
int histSize = 256;
float range[] = {0, 256};
const float* histRange = {range};
Mat hist;
calcHist(&gray, 1, 0, Mat(), hist, 1, &histSize, &histRange);

// 直方图均衡化
Mat equalized;
equalizeHist(gray, equalized);
```

---

## 五、视频与摄像头

```cpp
// 打开摄像头
VideoCapture cap(0);                     // 0 = 默认摄像头
// 或打开视频文件
VideoCapture cap("video.mp4");

if (!cap.isOpened()) return -1;

Mat frame;
while (cap.read(frame)) {                // 逐帧读取
    // 处理 frame
    imshow("Video", frame);
    if (waitKey(30) >= 0) break;         // 按任意键退出
}

// 写入视频
VideoWriter writer("output.avi",
    VideoWriter::fourcc('M','J','P','G'),
    30, Size(640, 480));
writer.write(frame);
```

---

## 六、人脸检测（Haar Cascade）

```cpp
CascadeClassifier face_cascade;
face_cascade.load("haarcascade_frontalface_default.xml");

Mat gray;
cvtColor(img, gray, COLOR_BGR2GRAY);
equalizeHist(gray, gray);

vector<Rect> faces;
face_cascade.detectMultiScale(gray, faces, 1.1, 3, 0, Size(30, 30));

for (const Rect& face : faces)
    rectangle(img, face, Scalar(0, 255, 0), 2);
```

---

## 七、stb_image（轻量备选）

当只需要图片读写而不需要图像处理时，stb_image 比 OpenCV 轻量得多（单头文件 vs OpenCV 数百 MB）。

参见《05_JSON_序列化.md》的 stb_image 部分。

---

## 八、编译

```bash
# OpenCV（需要安装后指定路径）
g++ main.cpp -I"D:/path/to/opencv/include" \
    -L"D:/path/to/opencv/lib" \
    -lopencv_core -lopencv_imgproc -lopencv_highgui \
    -lopencv_imgcodecs -lopencv_videoio \
    -o app
```
