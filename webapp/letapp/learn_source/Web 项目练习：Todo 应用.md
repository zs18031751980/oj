# Web 项目练习：Todo 应用

## 项目目标

通过一个完整的小项目，把布局、交互、状态管理和本地存储串起来。

---

## 推荐拆分

我们把整个项目拆分成三个核心部分，建议按顺序逐步实现。

### 1. 页面结构

这一阶段只关注"长什么样"，先不要管交互逻辑。

#### HTML 结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的待办事项</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="todo-app">
        <!-- 标题区 -->
        <header class="todo-header">
            <h1>📋 我的待办事项</h1>
            <p class="todo-count">共 <span id="taskCount">0</span> 项任务</p>
        </header>

        <!-- 输入区 -->
        <div class="todo-input-area">
            <input
                type="text"
                id="todoInput"
                placeholder="请输入新的待办事项..."
            />
            <button id="addBtn">添加</button>
        </div>

        <!-- 过滤区 -->
        <div class="todo-filter">
            <button class="filter-btn active" data-filter="all">全部</button>
            <button class="filter-btn" data-filter="active">未完成</button>
            <button class="filter-btn" data-filter="completed">已完成</button>
        </div>

        <!-- 列表区 -->
        <ul class="todo-list" id="todoList">
            <!-- 待办事项会由 JavaScript 动态生成 -->
        </ul>

        <!-- 统计区 -->
        <footer class="todo-footer">
            <button id="clearCompletedBtn">清除已完成</button>
        </footer>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

#### CSS 样式

```css
/* 全局样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: "Microsoft YaHei", sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
}

/* 应用容器 */
.todo-app {
    background: white;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
    width: 100%;
    max-width: 500px;
    padding: 30px;
}

/* 标题区 */
.todo-header {
    text-align: center;
    margin-bottom: 20px;
}

.todo-header h1 {
    color: #333;
    font-size: 24px;
}

.todo-count {
    color: #999;
    font-size: 14px;
    margin-top: 5px;
}

/* 输入区 */
.todo-input-area {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.todo-input-area input {
    flex: 1;
    padding: 12px 16px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
    outline: none;
    transition: border-color 0.3s;
}

.todo-input-area input:focus {
    border-color: #667eea;
}

.todo-input-area button {
    padding: 12px 24px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.3s;
}

.todo-input-area button:hover {
    background: #5a67d8;
}

/* 过滤区 */
.todo-filter {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-bottom: 20px;
}

.filter-btn {
    padding: 6px 16px;
    border: 1px solid #e0e0e0;
    background: white;
    border-radius: 20px;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.3s;
}

.filter-btn:hover {
    border-color: #667eea;
    color: #667eea;
}

.filter-btn.active {
    background: #667eea;
    color: white;
    border-color: #667eea;
}

/* 列表区 */
.todo-list {
    list-style: none;
    margin-bottom: 20px;
}

.todo-item {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #f0f0f0;
    transition: background 0.2s;
}

.todo-item:hover {
    background: #f9f9f9;
}

.todo-item:last-child {
    border-bottom: none;
}

/* 复选框（自定义样式） */
.todo-item input[type="checkbox"] {
    width: 20px;
    height: 20px;
    margin-right: 12px;
    cursor: pointer;
    accent-color: #667eea;
}

/* 任务文本 */
.todo-item .todo-text {
    flex: 1;
    font-size: 15px;
    color: #333;
}

.todo-item.completed .todo-text {
    text-decoration: line-through;
    color: #bbb;
}

/* 删除按钮 */
.todo-item .delete-btn {
    background: none;
    border: none;
    color: #ff6b6b;
    cursor: pointer;
    font-size: 18px;
    padding: 0 4px;
    opacity: 0;
    transition: opacity 0.2s;
}

.todo-item:hover .delete-btn {
    opacity: 1;
}

/* 空状态 */
.empty-state {
    text-align: center;
    color: #bbb;
    padding: 40px 0;
    font-size: 14px;
}

/* 底部统计区 */
.todo-footer {
    text-align: center;
    padding-top: 10px;
    border-top: 1px solid #f0f0f0;
}

#clearCompletedBtn {
    background: none;
    border: 1px solid #ff6b6b;
    color: #ff6b6b;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.3s;
}

#clearCompletedBtn:hover {
    background: #ff6b6b;
    color: white;
}
```

---

### 2. 交互逻辑

这一阶段实现所有的核心功能，让页面"动起来"。

#### 数据管理
我们用 JavaScript 数组来存放待办事项，每个事项是一个对象：

```javascript
// 数据结构
let todos = [
    { id: 1, text: "学习 HTML", completed: false },
    { id: 2, text: "学习 CSS", completed: true },
    { id: 3, text: "学习 JavaScript", completed: false },
]

// 生成唯一 ID（简单方式）
let nextId = todos.length + 1
```

#### 核心功能实现

```javascript
// ========== DOM 引用 ==========
const todoInput = document.getElementById("todoInput")
const addBtn = document.getElementById("addBtn")
const todoList = document.getElementById("todoList")
const taskCount = document.getElementById("taskCount")
const filterBtns = document.querySelectorAll(".filter-btn")
const clearCompletedBtn = document.getElementById("clearCompletedBtn")

// ========== 数据状态 ==========
let todos = []
let currentFilter = "all" // 'all' | 'active' | 'completed'

// ========== 渲染函数 ==========
function render() {
    // 1. 根据当前筛选条件过滤数据
    let filteredTodos = todos
    if (currentFilter === "active") {
        filteredTodos = todos.filter(todo => !todo.completed)
    } else if (currentFilter === "completed") {
        filteredTodos = todos.filter(todo => todo.completed)
    }

    // 2. 清空列表
    todoList.innerHTML = ""

    // 3. 空状态处理
    if (filteredTodos.length === 0) {
        todoList.innerHTML = `
            <li class="empty-state">
                ${todos.length === 0 ? "还没有任务，添加一条吧！" : "没有符合条件的任务"}
            </li>
        `
    } else {
        // 4. 生成列表项
        filteredTodos.forEach(todo => {
            const li = document.createElement("li")
            li.className = `todo-item ${todo.completed ? "completed" : ""}`
            li.dataset.id = todo.id
            li.innerHTML = `
                <input type="checkbox" ${todo.completed ? "checked" : ""}>
                <span class="todo-text">${todo.text}</span>
                <button class="delete-btn">✕</button>
            `
            todoList.appendChild(li)
        })
    }

    // 5. 更新任务计数
    taskCount.textContent = todos.length
}

// ========== 添加任务 ==========
function addTodo() {
    const text = todoInput.value.trim()
    if (text === "") {
        alert("请输入待办事项内容！")
        return
    }

    todos.push({
        id: Date.now(), // 用时间戳作为唯一 ID
        text: text,
        completed: false,
    })

    todoInput.value = "" // 清空输入框
    todoInput.focus()     // 聚焦到输入框
    render()
    saveToLocalStorage()
}

// ========== 切换完成状态 ==========
function toggleTodo(id) {
    const todo = todos.find(t => t.id === id)
    if (todo) {
        todo.completed = !todo.completed
        render()
        saveToLocalStorage()
    }
}

// ========== 删除任务 ==========
function deleteTodo(id) {
    todos = todos.filter(t => t.id !== id)
    render()
    saveToLocalStorage()
}

// ========== 清除已完成 ==========
function clearCompleted() {
    todos = todos.filter(t => !t.completed)
    render()
    saveToLocalStorage()
}

// ========== 切换筛选条件 ==========
function setFilter(filter) {
    currentFilter = filter
    filterBtns.forEach(btn => {
        btn.classList.toggle("active", btn.dataset.filter === filter)
    })
    render()
}

// ========== 本地存储 ==========
function saveToLocalStorage() {
    localStorage.setItem("todos", JSON.stringify(todos))
}

function loadFromLocalStorage() {
    const saved = localStorage.getItem("todos")
    if (saved) {
        try {
            todos = JSON.parse(saved)
        } catch (e) {
            todos = []
        }
    }
}

// ========== 事件绑定 ==========
// 添加按钮点击
addBtn.addEventListener("click", addTodo)

// 回车键添加
todoInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        addTodo()
    }
})

// 列表事件委托（处理点击复选框和删除按钮）
todoList.addEventListener("click", (e) => {
    const li = e.target.closest(".todo-item")
    if (!li) return

    const id = Number(li.dataset.id)

    if (e.target.type === "checkbox") {
        toggleTodo(id)
    }

    if (e.target.classList.contains("delete-btn")) {
        deleteTodo(id)
    }
})

// 筛选按钮
filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        setFilter(btn.dataset.filter)
    })
})

// 清除已完成
clearCompletedBtn.addEventListener("click", clearCompleted)

// ========== 初始化 ==========
loadFromLocalStorage()
render()
```

---

### 3. 数据持久化

如果不做数据持久化，每次刷新页面数据都会丢失。我们使用浏览器自带的 `localStorage` 来保存数据。

#### localStorage 简介
- `localStorage` 是浏览器提供的一种存储方式，数据会一直保存，除非用户手动清除
- 只能存储字符串，所以需要把对象转换成 JSON 字符串
- 每个域名下有 5MB 的存储空间（对于待办事项来说完全够用了）

```javascript
// 保存数据：把数组转成 JSON 字符串存起来
function saveToLocalStorage() {
    localStorage.setItem("todos", JSON.stringify(todos))
}

// 读取数据：把 JSON 字符串转回数组
function loadFromLocalStorage() {
    const saved = localStorage.getItem("todos")
    if (saved) {
        todos = JSON.parse(saved)
    } else {
        // 如果没有保存的数据，初始化一些示例任务
        todos = [
            { id: 1, text: "学习 HTML 基础", completed: true },
            { id: 2, text: "学习 CSS 样式", completed: true },
            { id: 3, text: "学习 JavaScript", completed: false },
            { id: 4, text: "学习 Vue 框架", completed: false },
            { id: 5, text: "完成 Todo 应用", completed: false },
        ]
    }
}

// 在每次数据变化时调用 saveToLocalStorage()
// 在页面加载时调用 loadFromLocalStorage()
```

#### 进阶：添加数据导出功能
```javascript
// 导出数据为 JSON 文件
function exportData() {
    const dataStr = JSON.stringify(todos, null, 2)
    const blob = new Blob([dataStr], { type: "application/json" })
    const url = URL.createObjectURL(blob)

    const a = document.createElement("a")
    a.href = url
    a.download = "我的待办事项.json"
    a.click()

    URL.revokeObjectURL(url)
}

// 导入数据
function importData(file) {
    const reader = new FileReader()
    reader.onload = (e) => {
        try {
            const importedTodos = JSON.parse(e.target.result)
            if (Array.isArray(importedTodos)) {
                todos = importedTodos
                render()
                saveToLocalStorage()
                alert("导入成功！")
            } else {
                alert("文件格式不正确！")
            }
        } catch (error) {
            alert("文件格式不正确！")
        }
    }
    reader.readAsText(file)
}
```

---

## 练习建议

1. **先在编辑器里把任务数组相关逻辑写通**，再迁移到页面组件中。先用 JavaScript 把核心逻辑写好并测试通过，再考虑 UI 展示
2. **逐步增加功能**：
   - 基础版：添加、完成/取消完成、删除
   - 进阶版：筛选（全部/未完成/已完成）、清除已完成
   - 高级版：数据持久化（localStorage）、编辑已有任务、拖拽排序
   - 挑战版：添加截止日期、分类标签、搜索功能
3. **尝试用 Vue 重写**：学完 Vue 后，把这个项目用 Vue 组件化的方式重写一遍，体会"数据驱动视图"的开发方式
4. **优化用户体验**：添加过渡动画、响应式设计、黑暗模式、键盘快捷键支持
5. **Git 版本管理**：在项目开始时就初始化 Git 仓库，每完成一个功能就提交一次，养成好习惯
6. **部署上线**：把最终版本部署到 Vercel 或 GitHub Pages 上，分享给你的朋友使用
