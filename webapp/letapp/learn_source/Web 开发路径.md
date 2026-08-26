# Web 开发路径

## 路径说明

这条路径适合想从零开始学习前端开发的同学。建议按照 HTML → CSS → JavaScript → Vue → 接口联调与部署的顺序推进，每一段都配合在线编辑器做即时练习。

---

## 建议阶段

### 1. HTML 与 CSS 基础

HTML 是网页的"骨架"，CSS 是网页的"衣服"。没有 HTML 就没有内容，没有 CSS 就只有光秃秃的文字。

#### HTML 基础

HTML（超文本标记语言）使用"标签"来标记内容：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的第一个网页</title>
</head>
<body>
    <!-- 标题 -->
    <h1>这是一级标题</h1>
    <h2>这是二级标题</h2>
    <h3>这是三级标题</h3>

    <!-- 段落 -->
    <p>这是一个段落。段落是网页中最常见的文本元素。</p>

    <!-- 链接 -->
    <a href="https://example.com">这是一个链接</a>

    <!-- 图片 -->
    <img src="image.jpg" alt="图片描述" width="300">

    <!-- 列表 -->
    <ul>
        <li>无序列表项 1</li>
        <li>无序列表项 2</li>
    </ul>
    <ol>
        <li>有序列表项 1</li>
        <li>有序列表项 2</li>
    </ol>

    <!-- 容器 -->
    <div>这是一个块级容器</div>
    <span>这是一个行内容器</span>

    <!-- 表格 -->
    <table>
        <tr>
            <th>姓名</th>
            <th>年龄</th>
        </tr>
        <tr>
            <td>小明</td>
            <td>18</td>
        </tr>
    </table>

    <!-- 表单 -->
    <form>
        <input type="text" placeholder="请输入用户名">
        <input type="password" placeholder="请输入密码">
        <button type="submit">登录</button>
    </form>
</body>
</html>
```

**语义化写法**：使用有语义的标签比全部用 `<div>` 更好，对搜索引擎和屏幕阅读器更友好：
- `<header>` — 页头
- `<nav>` — 导航
- `<main>` — 主要内容
- `<article>` — 文章
- `<section>` — 区块
- `<aside>` — 侧边栏
- `<footer>` — 页脚

#### CSS 基础

CSS（层叠样式表）用来控制网页的外观：

```css
/* 选择器 —— 选中要设置样式的元素 */

/* 标签选择器 */
p {
    color: blue;
    font-size: 16px;
}

/* 类选择器（最常用） */
.card {
    border: 1px solid #ddd;
    padding: 20px;
    border-radius: 8px;
}

/* ID 选择器（尽量少用） */
#header {
    background-color: #f5f5f5;
}

/* 组合选择器 */
.card .title {
    font-weight: bold;
}
```

**盒模型**：理解盒模型是学好 CSS 的关键。每个 HTML 元素都可以看作一个"盒子"：

```css
.box {
    /* 内容区大小 */
    width: 200px;
    height: 100px;

    /* 内边距 —— 内容到边框的距离 */
    padding: 20px;

    /* 边框 */
    border: 2px solid black;

    /* 外边距 —— 元素之间的距离 */
    margin: 10px;

    /* box-sizing: border-box 会让 padding 和 border 包含在 width 内 */
    box-sizing: border-box;
}
```

**Flexbox 布局**：现代 CSS 中最强大的布局方式之一，非常适合一维布局：

```css
.container {
    display: flex;           /* 启用 flex 布局 */
    justify-content: center; /* 水平居中 (flex-start / center / flex-end / space-between / space-around) */
    align-items: center;     /* 垂直居中 (flex-start / center / flex-end / stretch) */
    flex-wrap: wrap;         /* 允许换行 */
    gap: 16px;              /* 子元素之间的间距 */
}

.item {
    flex: 1;                 /* 等分剩余空间 */
    /* 或者固定宽度 */
    width: 200px;
}
```

**响应式设计**：让网页在不同屏幕上都显示良好：

```css
/* 媒体查询 —— 根据屏幕宽度应用不同样式 */
/* 手机（默认样式）*/
.card {
    width: 100%;
    padding: 10px;
}

/* 平板（宽度 ≥ 768px）*/
@media (min-width: 768px) {
    .card {
        width: 50%;
        padding: 20px;
    }
}

/* 桌面（宽度 ≥ 1024px）*/
@media (min-width: 1024px) {
    .card {
        width: 33.33%;
        padding: 30px;
    }
}
```

---

### 2. JavaScript 核心语法

JavaScript 让网页从"静态展示"变成"动态交互"。这一阶段你会学到编程的基本概念，为后续学习 Vue 打下基础。

#### 变量、函数、对象、数组
```javascript
// 变量
let name = "小明"
const age = 18

// 函数
function greet(name) {
    return `你好, ${name}!`
}

// 箭头函数（更简洁）
const add = (a, b) => a + b

// 对象
const user = {
    name: "小明",
    age: 18,
    hobbies: ["篮球", "编程"]
}

// 数组
const fruits = ["苹果", "香蕉", "橘子"]
```

#### 条件判断、循环
```javascript
// if 条件
if (score >= 90) {
    console.log("优秀")
} else if (score >= 60) {
    console.log("及格")
} else {
    console.log("不及格")
}

// for 循环
for (let i = 0; i < 5; i++) {
    console.log(i)
}

// 数组遍历
fruits.forEach(fruit => console.log(fruit))
```

#### DOM 操作（操作网页元素）
```javascript
// 获取元素
const button = document.querySelector("#myButton")
const title = document.querySelector("h1")

// 修改内容
title.textContent = "新的标题"

// 修改样式
title.style.color = "red"

// 事件监听
button.addEventListener("click", () => {
    alert("按钮被点击了！")
})

// 创建和添加元素
const newDiv = document.createElement("div")
newDiv.textContent = "我是新元素"
document.body.appendChild(newDiv)
```

#### 异步基础
```javascript
// Promise 和 async/await
async function fetchData() {
    try {
        const response = await fetch("https://api.example.com/data")
        const data = await response.json()
        console.log(data)
    } catch (error) {
        console.error("请求失败:", error)
    }
}

fetchData()
```

---

### 3. Vue 组件开发

Vue 是一个渐进式前端框架，它让你能用"组件"的方式开发网页。学完 HTML/CSS/JavaScript 后，Vue 会把你的开发效率提升一个台阶。

#### 组件拆分
把一个大页面拆成多个小组件，每个组件只负责一个功能：

```vue
<template>
  <div class="app">
    <AppHeader />
    <MainContent>
      <ArticleList :articles="articles" />
      <SideBar />
    </MainContent>
    <AppFooter />
  </div>
</template>
```

#### Props / Emits
- **Props**：父组件向子组件传递数据
- **Emits**：子组件向父组件发送事件

```vue
<!-- 子组件 -->
<script setup>
defineProps(["title", "content"])
defineEmits(["click", "delete"])
</script>
```

#### 状态管理和页面组合
使用 Pinia 管理多个组件共享的状态：

```javascript
// stores/user.js
export const useUserStore = defineStore("user", () => {
    const user = ref(null)
    const isLoggedIn = computed(() => !!user.value)
    async function login(username, password) { /* ... */ }
    function logout() { user.value = null }
    return { user, isLoggedIn, login, logout }
})
```

---

### 4. 接口联调与部署

#### 使用 fetch 或 axios
前端需要从后端获取数据，通常使用 HTTP 请求：

```javascript
// 使用 fetch（浏览器内置）
async function getUsers() {
    const response = await fetch("/api/users")
    const users = await response.json()
    return users
}

// 使用 axios（需要安装，功能更强大）
import axios from "axios"

async function getUsers() {
    const { data } = await axios.get("/api/users")
    return data
}
```

#### 处理加载状态和报错
```vue
<template>
    <div>
        <!-- 加载中 -->
        <Loading v-if="loading" />

        <!-- 加载成功 -->
        <template v-else-if="data">
            <ArticleList :articles="data" />
        </template>

        <!-- 加载失败 -->
        <ErrorTip v-else :message="errorMessage" />
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue"

const loading = ref(true)
const data = ref(null)
const errorMessage = ref("")

onMounted(async () => {
    try {
        const response = await fetch("/api/articles")
        data.value = await response.json()
    } catch (error) {
        errorMessage.value = "数据加载失败，请稍后重试"
    } finally {
        loading.value = false
    }
})
</script>
```

#### 把项目部署到线上环境
部署就是把你的代码放到服务器上，让别人也能访问：

**常见部署方式**：
1. **静态托管**（适合前端项目）：
   - Vercel：免费，连接 GitHub 仓库即可自动部署
   - Netlify：类似 Vercel，操作简单
   - GitHub Pages：免费，适合静态站点
   - 阿里云 OSS / 腾讯云 COS：对象存储托管静态文件

2. **服务器部署**（适合有后端的项目）：
   - 购买云服务器（阿里云、腾讯云、华为云）
   - 使用 Nginx 作为反向代理
   - 使用 Docker 容器化部署

**部署流程示例（Vercel）**：
```bash
# 1. 把代码推送到 GitHub
git add .
git commit -m "准备部署"
git push

# 2. 在 Vercel 上导入你的 GitHub 仓库
# 3. Vercel 会自动检测项目类型，一键部署
# 4. 每次推送代码到 GitHub，Vercel 会自动重新部署
```

---

## 配套建议

1. **学完每个阶段后，都去 `/playground` 写一个小例子验证理解**，再进入下一阶段
2. **不要追求"学完再练"**：学到什么就练什么，哪怕只是一个按钮、一个标题
3. **善用浏览器开发者工具**：按 F12 打开，你会看到 Elements（元素）、Console（控制台）、Network（网络）等面板，它们是你调试网页的利器
4. **多看、多模仿、多创造**：先在 GitHub 上找开源项目看代码，再模仿着写，最后尝试自己创造
5. **遇到报错先自己查**：把错误信息复制到搜索引擎或 Stack Overflow 上，大部分问题都已经有答案了
6. **建立自己的代码片段库**：把常用的代码片段保存下来，以后直接复制使用，提高效率
