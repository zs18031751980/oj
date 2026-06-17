# JavaScript 入门指南

## 适合谁

适合第一次系统学习前端编程的同学，尤其适合刚从 HTML / CSS 过渡到交互逻辑的人。如果你已经能写出一个漂亮的静态页面，但想让页面"动起来"——比如点击按钮弹出提示、表单验证输入内容、数据变化时自动更新页面——那么 JavaScript 就是你需要的工具。

---

## 你会学到什么

### 基础语法

#### 变量和常量
JavaScript 有三种声明变量的方式，新手建议优先使用 `let` 和 `const`：

```javascript
// let — 可变变量，值可以改变
let age = 18;
age = 20; // 没问题

// const — 常量，值一旦赋值就不能改变
const name = "小明";
name = "小红"; // 会报错！常量不可重新赋值

// var — 旧的声明方式（不推荐使用），有作用域问题
var oldWay = "尽量避免这样写";
```

**命名规则**：变量名建议使用"小驼峰命名法"，例如 `userName`、`totalPrice`、`isLoggedIn`，见名知意。

#### 数据类型
```javascript
// 基本数据类型
let str = "你好";        // 字符串（String）
let num = 42;             // 数字（Number），包括整数和小数
let isTrue = true;        // 布尔值（Boolean），true 或 false
let notDefined = undefined; // 未定义
let empty = null;         // 空值

// 引用数据类型
let arr = [1, 2, 3];      // 数组（Array），用于存放一组数据
let obj = {                // 对象（Object），用于存放键值对
    name: "小明",
    age: 18,
    sayHi: function() {
        console.log("你好！");
    }
};

// 使用 typeof 检查数据类型
console.log(typeof "hello"); // "string"
console.log(typeof 42);      // "number"
console.log(typeof true);    // "boolean"
```

#### 条件与循环
**条件判断**：
```javascript
let score = 85;

if (score >= 90) {
    console.log("优秀");
} else if (score >= 60) {
    console.log("及格");
} else {
    console.log("不及格");
}

// 三元运算符 —— 简洁的条件判断
let status = score >= 60 ? "通过" : "未通过";
```

**循环**：
```javascript
// for 循环 —— 知道循环次数时使用
for (let i = 0; i < 5; i++) {
    console.log("第" + (i + 1) + "次循环");
}

// while 循环 —— 不知道具体次数，只知道条件时使用
let count = 0;
while (count < 5) {
    console.log(count);
    count++;
}

// 遍历数组
let fruits = ["苹果", "香蕉", "橘子"];
for (let fruit of fruits) {
    console.log(fruit);
}

// forEach 方法（更常用）
fruits.forEach(function(fruit, index) {
    console.log(index + ": " + fruit);
});
```

#### 函数与作用域
函数是 JavaScript 中最重要的概念之一，它让你能把一段代码"打包"起来，随时调用。

```javascript
// 传统函数声明
function greet(name) {
    return "你好, " + name + "!";
}
console.log(greet("小明")); // "你好, 小明!"

// 箭头函数（ES6 新写法，更简洁）
const greet2 = (name) => {
    return "你好, " + name + "!";
};

// 如果只有一行 return，可以更加简洁
const greet3 = (name) => "你好, " + name + "!";
```

**作用域**理解：
- **全局作用域**：在代码最外层声明的变量，任何地方都能访问
- **函数作用域**：在函数内部声明的变量，只能在函数内部访问
- **块作用域**：`let` 和 `const` 在 `{}` 内声明，只能在这个块内访问

```javascript
let global = "我是全局变量";

function test() {
    let local = "我是局部变量";
    console.log(global); // 可以访问
    console.log(local);  // 可以访问
}

console.log(global); // 可以访问
console.log(local);  // 报错！local 在此处不可见
```

---

### 常见数据结构

#### 数组
数组用于存储一组有序的数据，是前端开发中使用频率最高的数据结构之一。

```javascript
let arr = [1, 2, 3, 4, 5];

// 常用方法
arr.push(6);           // 末尾添加元素 → [1,2,3,4,5,6]
arr.pop();             // 移除末尾元素 → [1,2,3,4,5]
arr.unshift(0);        // 开头添加元素 → [0,1,2,3,4,5]
arr.shift();           // 移除开头元素 → [1,2,3,4,5]
arr.indexOf(3);        // 查找元素位置 → 2
arr.includes(3);       // 是否包含 → true
arr.slice(1, 3);       // 截取（不修改原数组）→ [2,3]
arr.splice(1, 2);      // 删除（修改原数组）→ 从索引1开始删2个

// 数组变换（这些方法不会修改原数组）
let doubled = arr.map(x => x * 2);      // [2,4,6,8,10] 每个元素翻倍
let evens = arr.filter(x => x % 2 === 0); // [2,4] 只保留偶数
let sum = arr.reduce((a, b) => a + b, 0); // 15 求和
```

#### 对象
对象以"键值对"的形式存储数据，适合表示现实中的实体：

```javascript
let user = {
    name: "小明",
    age: 18,
    hobbies: ["篮球", "编程"],
    address: {
        city: "北京",
        district: "海淀"
    }
};

// 访问属性
console.log(user.name);        // "小明"
console.log(user["name"]);     // "小明"（另一种方式）
console.log(user.address.city); // "北京"

// 修改和添加属性
user.age = 19;
user.email = "xiaoming@example.com";

// 删除属性
delete user.email;

// 遍历对象
for (let key in user) {
    console.log(key + ": " + user[key]);
}

// 获取所有键或值
console.log(Object.keys(user));   // ["name", "age", "hobbies", "address"]
console.log(Object.values(user)); // ["小明", 18, [...], {...}]
```

#### 字符串处理
```javascript
let str = "  Hello, JavaScript!  ";

// 常用方法
str.length;              // 长度 → 21
str.toLowerCase();       // 转小写 → "  hello, javascript!  "
str.toUpperCase();       // 转大写 → "  HELLO, JAVASCRIPT!  "
str.trim();              // 去除两端空格 → "Hello, JavaScript!"
str.split(",");          // 分割成数组 → ["  Hello", " JavaScript!  "]
str.includes("Java");    // 是否包含 → true
str.startsWith("Hello"); // 是否以...开头 → false（前面有空格）
str.replace("JavaScript", "JS"); // 替换 → "  Hello, JS!  "

// 模板字符串（ES6，推荐使用）
let name = "小明";
let age = 18;
let message = `我叫${name}，今年${age}岁`; // "我叫小明，今年18岁"
```

---

### 浏览器交互

JavaScript 最初就是为了让网页有交互而诞生的。以下是三个最核心的浏览器交互能力：

#### DOM 查询
DOM（文档对象模型）可以理解为浏览器把 HTML 页面转换成了一个"对象树"，JavaScript 可以通过操作这棵树来改变页面的内容。

```javascript
// 获取页面元素 —— 四种方式
document.getElementById("myId");          // 通过 id 获取（最快）
document.getElementsByClassName("myClass"); // 通过 class 获取（返回集合）
document.getElementsByTagName("div");      // 通过标签名获取（返回集合）
document.querySelector(".myClass");        // 通过 CSS 选择器获取（第一个匹配）
document.querySelectorAll("div.item");     // 获取所有匹配的元素（返回 NodeList）

// 修改元素内容
let title = document.querySelector("h1");
title.textContent = "新的标题";       // 修改文本内容
title.innerHTML = "新的标题 <span>带标签</span>"; // 修改 HTML 内容

// 修改样式
title.style.color = "red";
title.style.fontSize = "24px";
title.classList.add("active");        // 添加类名
title.classList.remove("inactive");   // 移除类名
title.classList.toggle("active");     // 切换类名（有则删，无则加）

// 修改属性
let link = document.querySelector("a");
link.href = "https://example.com";
link.setAttribute("target", "_blank");
```

#### 事件绑定
事件就是用户在页面上的操作（点击、输入、鼠标移动等），JavaScript 可以"监听"这些事件并做出响应。

```javascript
// 点击事件 —— 最常用
let button = document.querySelector("#myButton");
button.addEventListener("click", function(event) {
    alert("按钮被点击了！");
    console.log("事件对象:", event);
});

// 常用事件类型
// click       — 点击
// dblclick    — 双击
// mouseover   — 鼠标移入
// mouseout    — 鼠标移出
// keydown     — 键盘按下
// keyup       — 键盘抬起
// submit      — 表单提交
// change      — 值改变（输入框、下拉菜单等）
// input       — 输入时触发（实时）
// scroll      — 滚动
// load        — 页面加载完毕

// 事件委托 —— 把事件绑定到父元素上，通过事件冒泡来处理子元素
let list = document.querySelector("ul");
list.addEventListener("click", function(event) {
    if (event.target.tagName === "LI") {
        console.log("你点击了:", event.target.textContent);
    }
});
```

#### 表单输入处理
```javascript
// 获取输入框的值
let input = document.querySelector("#username");
input.addEventListener("input", function() {
    console.log("当前输入:", this.value);
});

// 表单验证
let form = document.querySelector("#myForm");
form.addEventListener("submit", function(event) {
    event.preventDefault(); // 阻止表单默认提交行为

    let username = document.querySelector("#username").value;
    let password = document.querySelector("#password").value;

    // 简单的验证
    if (username.trim() === "") {
        alert("用户名不能为空");
        return;
    }
    if (password.length < 6) {
        alert("密码长度不能少于6位");
        return;
    }

    // 验证通过，提交数据
    console.log("提交数据:", { username, password });
});

// 复选框和单选框
let checkbox = document.querySelector("#agree");
checkbox.addEventListener("change", function() {
    console.log("是否同意:", this.checked); // true 或 false
});

// 下拉菜单
let select = document.querySelector("#city");
select.addEventListener("change", function() {
    console.log("选择的城市:", this.value);
});
```

---

## 练习建议

1. 在编辑器里写一个 `greet(name)` 函数，调用后返回 "你好，[name]！"，然后打印到控制台
2. 练习遍历数组并输出结果：创建一个包含 5 个水果名称的数组，用 forEach 依次输出 "我喜欢吃[水果名]"
3. 尝试模拟一个待办事项列表的增删逻辑：创建一个数组存放待办事项，实现添加、删除、标记完成三个功能
4. 进阶练习：做一个简单的计算器页面，包含两个输入框和加减乘除四个按钮，点击按钮显示计算结果
5. 综合练习：做一个"猜数字"游戏，程序随机生成 1-100 之间的数字，用户输入猜测，程序提示"大了"或"小了"，直到猜中为止
