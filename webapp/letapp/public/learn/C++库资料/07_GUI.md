# GUI 图形界面库详解

## 一、Qt — 最主流的跨平台 C++ GUI

### 概述
Qt 是 C++ GUI 开发的工业标准，功能远超"界面框架"范畴——包含网络、数据库、XML、OpenGL 等。

### 安装
- 从 https://www.qt.io/download 下载 Qt Online Installer
- 选择 MinGW 或 MSVC 版本

### 核心模块

| 模块 | 功能 |
|------|------|
| QtCore | 核心非 GUI（事件循环、线程、文件、容器） |
| QtGui | 基本 GUI（窗口、字体、颜色、图像） |
| QtWidgets | 桌面控件（按钮、文本框、表格、布局） |
| QtNetwork | 网络通信 |
| QtSql | 数据库 |
| QtOpenGL | OpenGL 3D 渲染 |
| QtCharts | 图表 |
| QtQuick/QML | 声明式 UI |

### Hello Qt

```cpp
#include <QApplication>
#include <QPushButton>

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    QPushButton button("Hello, Qt!");
    button.resize(200, 100);
    button.show();

    return app.exec();  // 进入事件循环
}
```

**编译（qmake）：**
```bash
# 先创建 .pro 文件
# QT += core gui widgets
# SOURCES += main.cpp
qmake
make
```

**编译（CMake）：**
```cmake
# CMakeLists.txt
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)
qt_standard_project_setup()
add_executable(app main.cpp)
target_link_libraries(app Qt6::Core Qt6::Gui Qt6::Widgets)
```

### 常用控件

```cpp
#include <QWidget>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QTextEdit>
#include <QComboBox>
#include <QCheckBox>
#include <QRadioButton>
#include <QSpinBox>
#include <QSlider>
#include <QProgressBar>
#include <QTableWidget>
#include <QListWidget>
#include <QTreeWidget>
#include <QTabWidget>

// 标签
QLabel* label = new QLabel("Text");

// 按钮
QPushButton* btn = new QPushButton("Click");
connect(btn, &QPushButton::clicked, [&](){ /* 处理点击 */ });

// 文本输入
QLineEdit* lineEdit = new QLineEdit;
QTextEdit* textEdit = new QTextEdit;

// 下拉框
QComboBox* combo = new QComboBox;
combo->addItems({"Option1", "Option2"});

// 复选框
QCheckBox* check = new QCheckBox("Enable");

// 单选按钮（需要 QButtonGroup 分组）
QRadioButton* radio1 = new QRadioButton("A");
QRadioButton* radio2 = new QRadioButton("B");

// 数字输入
QSpinBox* spin = new QSpinBox;  // 整数
spin->setRange(0, 100);
QDoubleSpinBox* dspin = new QDoubleSpinBox;  // 浮点

// 滑块
QSlider* slider = new QSlider(Qt::Horizontal);
slider->setRange(0, 100);

// 进度条
QProgressBar* progress = new QProgressBar;
progress->setRange(0, 100);
progress->setValue(50);

// 表格
QTableWidget* table = new QTableWidget(5, 3);  // 5行3列
table->setItem(0, 0, new QTableWidgetItem("data"));

// 列表
QListWidget* list = new QListWidget;
list->addItem("Item1");

// 标签页
QTabWidget* tabs = new QTabWidget;
tabs->addTab(new QWidget, "Tab1");
```

### 布局管理

```cpp
// 水平布局
QHBoxLayout* hbox = new QHBoxLayout;
hbox->addWidget(btn1);
hbox->addWidget(btn2);

// 垂直布局
QVBoxLayout* vbox = new QVBoxLayout;
vbox->addWidget(label);
vbox->addLayout(hbox);

// 网格布局
QGridLayout* grid = new QGridLayout;
grid->addWidget(label, 0, 0);   // 第0行第0列
grid->addWidget(edit, 0, 1);    // 第0行第1列
grid->addWidget(btn, 1, 0, 1, 2);  // 第1行，跨2列

// 设置主窗口布局
window->setLayout(vbox);
```

### 信号与槽（事件处理）

```cpp
// 语法1：新式（推荐）
connect(btn, &QPushButton::clicked, this, &MainWindow::onClick);

// 语法2：Lambda
connect(btn, &QPushButton::clicked, [=]() {
    label->setText("Clicked!");
});

// 语法3：老式（字符串连接）
connect(btn, SIGNAL(clicked()), this, SLOT(onClick()));

// 自定义信号
class MyWidget : public QWidget {
    Q_OBJECT
signals:
    void valueChanged(int newValue);
public slots:
    void onValueChanged(int v) {
        // 处理
    }
};
```

### 对话框

```cpp
// 文件选择
QString file = QFileDialog::getOpenFileName(this, "选择文件", "C:/", "Images (*.png *.jpg)");

// 颜色选择
QColor color = QColorDialog::getColor(Qt::blue, this);

// 消息对话框
QMessageBox::information(this, "标题", "信息");
QMessageBox::warning(this, "标题", "警告");
QMessageBox::question(this, "标题", "确认？", QMessageBox::Yes | QMessageBox::No);

// 输入对话框
QString text = QInputDialog::getText(this, "标题", "输入文字:");
int value = QInputDialog::getInt(this, "标题", "输入数字:", 0, 0, 100);
```

### 绘图（QPainter）

```cpp
void paintEvent(QPaintEvent*) override {
    QPainter painter(this);
    painter.setPen(QPen(Qt::red, 2));
    painter.setBrush(QBrush(Qt::blue));

    painter.drawLine(10, 10, 100, 100);
    painter.drawRect(50, 50, 100, 80);
    painter.drawEllipse(50, 50, 100, 80);
    painter.drawText(10, 10, "Hello");
}
```

### 定时器

```cpp
QTimer* timer = new QTimer(this);
connect(timer, &QTimer::timeout, [&]() {
    // 每秒执行
});
timer->start(1000);  // 1000ms

// 单次定时
QTimer::singleShot(5000, [&]() {
    // 5秒后执行一次
});
```

### 多线程

```cpp
#include <QThread>

class Worker : public QObject {
    Q_OBJECT
public slots:
    void doWork() {
        // 耗时操作
        emit finished();
    }
signals:
    void finished();
};

QThread* thread = new QThread;
Worker* worker = new Worker;
worker->moveToThread(thread);
connect(thread, &QThread::started, worker, &Worker::doWork);
connect(worker, &Worker::finished, thread, &QThread::quit);
thread->start();
```

---

## 二、ImGui — 即时模式 GUI

### 概述
Dear ImGui 是用于工具、调试面板、仿真界面的轻量 GUI 库。特点是：
- **即时模式**：每帧重新绘制，不需要事件循环和回调
- **极轻量**：仅需一个头文件和 OpenGL/DirectX 后端
- **适合**：开发工具、数据可视化面板、游戏内调试窗口

### 包含
```cpp
#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"
```

### 基础用法

```cpp
// 在渲染循环中
while (!glfwWindowShouldClose(window)) {
    // 开始新帧
    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();

    // ---- 创建 UI ----
    ImGui::Begin("控制面板");           // 窗口开始

    ImGui::Text("Hello, ImGui!");       // 文本
    ImGui::Button("点击");              // 按钮

    static float value = 0.5f;
    ImGui::SliderFloat("参数", &value, 0.0f, 1.0f);  // 滑块

    static int count = 0;
    if (ImGui::Button("+1"))
        count++;
    ImGui::SameLine();                  // 同一行
    ImGui::Text("计数: %d", count);

    ImGui::Checkbox("启用", &enabled);  // 复选框

    static int selected = 0;
    ImGui::RadioButton("A", &selected, 0);
    ImGui::RadioButton("B", &selected, 1);

    const char* items[] = {"选项1", "选项2", "选项3"};
    static int current = 0;
    ImGui::Combo("选择", &current, items, 3);  // 下拉框

    ImGui::InputText("输入", buf, sizeof(buf));  // 文本输入

    ImGui::End();                            // 窗口结束

    // ---- 渲染 ----
    ImGui::Render();
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
}
```

### 布局

```cpp
ImGui::Begin("布局");

ImGui::Columns(2, "mycolumns");        // 分两列
ImGui::Text("Column 1");
ImGui::NextColumn();
ImGui::Text("Column 2");
ImGui::Columns(1);

// 树形节点
if (ImGui::TreeNode("高级选项")) {
    ImGui::SliderFloat("速度", &speed, 0, 10);
    ImGui::TreePop();
}

// 分组
ImGui::BeginGroup();
ImGui::Text("组1");
ImGui::Button("OK");
ImGui::EndGroup();

ImGui::SameLine();
ImGui::BeginGroup();
ImGui::Text("组2");
ImGui::Button("Cancel");
ImGui::EndGroup();

ImGui::End();
```

### 绘图（Canvas）

```cpp
ImGui::Begin("画布");
ImDrawList* draw = ImGui::GetWindowDrawList();
ImVec2 p = ImGui::GetCursorScreenPos();

draw->AddLine(ImVec2(p.x, p.y), ImVec2(p.x+100, p.y+100), IM_COL32(255,0,0,255), 2);
draw->AddRect(ImVec2(p.x, p.y+50), ImVec2(p.x+100, p.y+150), IM_COL32(0,255,0,255));
draw->AddCircle(ImVec2(p.x+50, p.y+25), 25, IM_COL32(0,0,255,255));
draw->AddText(ImVec2(p.x, p.y+160), IM_COL32(255,255,255,255), "文字");

ImGui::End();
```

### 表格

```cpp
if (ImGui::BeginTable("数据表", 3, ImGuiTableFlags_Borders)) {
    ImGui::TableSetupColumn("名称");
    ImGui::TableSetupColumn("数值");
    ImGui::TableSetupColumn("状态");
    ImGui::TableHeadersRow();

    for (int i = 0; i < 5; i++) {
        ImGui::TableNextRow();
        ImGui::TableSetColumnIndex(0);
        ImGui::Text("Item %d", i);
        ImGui::TableSetColumnIndex(1);
        ImGui::Text("%.2f", values[i]);
        ImGui::TableSetColumnIndex(2);
        ImGui::Text("OK");
    }
    ImGui::EndTable();
}
```

### 与 Matplotlib 对比（数据可视化）

ImGui 可以通过 ImPlot 扩展实现快速绘图：

```cpp
#include "implot.h"

ImGui::Begin("图表");
static double x[100], y1[100], y2[100];
// ... 填充数据 ...
ImPlot::BeginSubplots("2x1", 2, 1, ImVec2(-1, 400));
ImPlot::SetNextPlotLimits(0, 100, -1, 1);
ImPlot::PlotLine("sin(x)", x, y1, 100);
ImPlot::NextCol();
ImPlot::PlotLine("cos(x)", x, y2, 100);
ImPlot::EndSubplots();
ImGui::End();
```

---

## 三、wxWidgets — 传统桌面 GUI

### 概述
与 Qt 类似但更轻量，直接调用各平台原生控件。

### Hello wxWidgets

```cpp
#include <wx/wx.h>

class MyApp : public wxApp {
    bool OnInit() override {
        wxFrame* frame = new wxFrame(nullptr, wxID_ANY, "Hello wx");
        frame->Show(true);
        return true;
    }
};

wxIMPLEMENT_APP(MyApp);
```

---

## 四、GUI 库选择指南

| 库 | 学习曲线 | 功能 | 大小 | 适用场景 |
|------|---------|------|------|---------|
| Qt | 陡 | 极全 | 大（~1GB） | 商业桌面软件、跨平台应用 |
| ImGui | 平 | 基础控件+绘图 | 极小（~300KB） | 调试面板、仿真工具、内部工具 |
| wxWidgets | 中 | 完整 | 中（~100MB） | 需要原生控件外观的应用 |

**推荐：**
- 数学建模/算法调试 → **ImGui**（最小最快）
- 完整的桌面应用 → **Qt**
- 需要原生外观 → **wxWidgets**
