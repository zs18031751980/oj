# Vue 组件化开发

## 课程目标

学会把一个中型页面拆成多个职责清晰的组件，并处理好数据流和交互边界。组件化是 Vue 的核心思想——把页面拆分成一个个独立、可复用的小部件，每个部件只负责自己的那一块，组合起来就构成了完整的页面。

---

## 推荐内容

### 组件拆分原则

#### 单一职责原则
每个组件只负责一件事。如果一个组件做的事情太多，就应该把它拆成更小的组件。

**不好的例子**：一个组件包含了文章列表、搜索框、用户信息、侧边栏广告、页脚...
**好的例子**：把上面拆成 `ArticleList`、`SearchBar`、`UserProfile`、`SidebarAd`、`AppFooter` 等独立组件

```vue
<!-- 好的做法：一个组件只做一件事 -->
<template>
  <div class="article-list">
    <ArticleItem
      v-for="article in articles"
      :key="article.id"
      :article="article"
      @click="handleClick"
    />
  </div>
</template>

<script setup>
import ArticleItem from "./ArticleItem.vue"

defineProps(["articles"])
const emit = defineEmits(["click"])

function handleClick(article) {
  emit("click", article)
}
</script>
```

#### 可复用性
当你发现某个 UI 片段在多处使用时，就应该把它提取成组件。常见的可复用组件有：
- 按钮组件（`BaseButton`）
- 输入框组件（`BaseInput`）
- 卡片组件（`BaseCard`）
- 弹窗组件（`BaseModal`）
- 加载状态组件（`LoadingSpinner`）

```vue
<!-- 可复用的按钮组件 -->
<template>
  <button
    :class="[
      'base-button',
      `base-button--${type}`,
      `base-button--${size}`,
      { 'base-button--disabled': disabled }
    ]"
    :disabled="disabled"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: "primary",  // primary / secondary / danger / text
  },
  size: {
    type: String,
    default: "medium",   // small / medium / large
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

defineEmits(["click"])
</script>
```

#### 输入输出明确
每个组件都应该有清晰的"接口"：
- **输入（Props）**：父组件通过 props 向子组件传递数据
- **输出（Emits）**：子组件通过事件向父组件发送消息
- **不要修改 props**：props 是只读的，子组件不应该直接修改它

```vue
<!-- 好的组件设计：接口清晰 -->
<template>
  <div class="user-card" @click="handleClick">
    <img :src="user.avatar" :alt="user.name" />
    <h3>{{ user.name }}</h3>
    <p>{{ user.bio }}</p>
  </div>
</template>

<script setup>
const props = defineProps({
  user: {
    type: Object,
    required: true,
    // 明确说明 user 对象的结构
    // 实际使用中可以用更详细的验证
  },
})

const emit = defineEmits(["select"])

function handleClick() {
  emit("select", props.user.id)
}
</script>
```

---

### 常用通信方式

#### Props 父传子
父组件通过 props 把数据传给子组件，这是最基础的通信方式：

```vue
<!-- 父组件 -->
<template>
  <ChildComponent
    :title="pageTitle"
    :items="itemList"
    :is-visible="true"
  />
</template>

<!-- 子组件 -->
<script setup>
defineProps({
  title: String,
  items: Array,
  isVisible: Boolean,
})
</script>
```

**Props 验证**：建议总是为 props 指定类型和必要的验证，这能在开发阶段就发现问题：

```vue
<script setup>
defineProps({
  name: {
    type: String,
    required: true,       // 必须传入
  },
  age: {
    type: Number,
    default: 0,           // 默认值
  },
  tags: {
    type: Array,
    default: () => [],     // 数组和对象的默认值要用函数返回
  },
  status: {
    type: String,
    validator: (value) => {
      return ["active", "inactive", "pending"].includes(value)
    },
  },
})
</script>
```

#### Emits 子传父
子组件通过事件向父组件传递信息：

```vue
<!-- 子组件 -->
<template>
  <button @click="handleDelete">删除</button>
</template>

<script setup>
const emit = defineEmits(["delete", "update"])

function handleDelete() {
  // 可以传递数据
  emit("delete", { id: 123, reason: "用户主动删除" })
}
</script>

<!-- 父组件 -->
<template>
  <ChildComponent @delete="handleDelete" @update="handleUpdate" />
</template>

<script setup>
function handleDelete(data) {
  console.log("收到删除事件:", data)
}
function handleUpdate() {
  console.log("收到更新事件")
}
</script>
```

#### v-model 双向绑定
v-model 是 Vue 中实现"双向绑定"的语法糖，本质上是 props + events 的组合：

```vue
<!-- 父组件使用 v-model -->
<template>
  <CustomInput v-model="searchText" />
  <!-- 等价于：
  <CustomInput
    :modelValue="searchText"
    @update:modelValue="searchText = $event"
  />
  -->
</template>

<!-- 自定义输入框组件 -->
<template>
  <input
    :value="modelValue"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>

<script setup>
defineProps(["modelValue"])
defineEmits(["update:modelValue"])
</script>

<!-- 多个 v-model（Vue 3） -->
<template>
  <CustomForm
    v-model:name="userName"
    v-model:age="userAge"
  />
</template>
```

#### 插槽（Slot）
插槽让父组件可以向子组件中插入任意内容，实现更灵活的组合：

```vue
<!-- Card 组件 —— 提供骨架，内容由外部填充 -->
<template>
  <div class="card">
    <div class="card-header">
      <slot name="header">默认标题</slot>
    </div>
    <div class="card-body">
      <slot />  <!-- 默认插槽 -->
    </div>
    <div class="card-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<!-- 使用 Card 组件 -->
<template>
  <Card>
    <template #header>
      <h2>用户信息</h2>
    </template>

    <!-- 默认插槽的内容 -->
    <p>姓名：小明</p>
    <p>年龄：18岁</p>

    <template #footer>
      <button>编辑</button>
      <button>删除</button>
    </template>
  </Card>
</template>
```

#### 状态管理（Pinia）
当多个组件需要共享同一个状态时，使用状态管理库（推荐 Pinia）会比 props 层层传递更清晰：

```javascript
// stores/counter.js
import { defineStore } from "pinia"
import { ref, computed } from "vue"

export const useCounterStore = defineStore("counter", () => {
  // state —— 状态
  const count = ref(0)
  const name = ref("计数器")

  // getters —— 计算属性
  const doubleCount = computed(() => count.value * 2)

  // actions —— 方法
  function increment() {
    count.value++
  }
  function decrement() {
    count.value--
  }
  function reset() {
    count.value = 0
  }

  return { count, name, doubleCount, increment, decrement, reset }
})
```

```vue
<!-- 在任何组件中使用 -->
<template>
  <div>
    <p>{{ counterStore.count }} × 2 = {{ counterStore.doubleCount }}</p>
    <button @click="counterStore.increment">+1</button>
    <button @click="counterStore.decrement">-1</button>
    <button @click="counterStore.reset()">重置</button>
  </div>
</template>

<script setup>
import { useCounterStore } from "@/stores/counter"

const counterStore = useCounterStore()
</script>
```

---

### 工程化思维

#### 目录结构
一个好的项目目录结构能让你在项目变大时依然保持清晰的思路：

```
src/
├── assets/                # 静态资源（图片、字体等）
│   ├── images/
│   └── styles/
├── components/            # 通用组件（可复用）
│   ├── common/           # 基础组件（按钮、输入框等）
│   │   ├── BaseButton.vue
│   │   ├── BaseInput.vue
│   │   └── BaseModal.vue
│   └── business/         # 业务组件
│       ├── UserCard.vue
│       └── ArticleItem.vue
├── composables/           # 组合式函数（可复用的逻辑）
│   ├── usePagination.js
│   └── useDebounce.js
├── layouts/               # 布局组件
│   ├── DefaultLayout.vue
│   └── AuthLayout.vue
├── pages/                 # 页面组件（路由级别）
│   ├── Home.vue
│   ├── About.vue
│   └── User/
│       ├── UserProfile.vue
│       └── UserSettings.vue
├── router/                # 路由配置
│   └── index.js
├── stores/                # 状态管理
│   └── counter.js
└── utils/                 # 工具函数
    ├── format.js
    └── request.js
```

#### 命名规范
一致的命名规范能让团队协作更顺畅：

**组件命名**：
- 文件名使用 PascalCase：`UserCard.vue`、`BaseButton.vue`
- 多单词命名避免与 HTML 原生标签冲突：`UserCard`（好）、`Card`（可能冲突）
- 通用组件加前缀：`BaseButton`、`AppHeader`、`TheModal`

**变量命名**：
- JavaScript 使用 camelCase：`userName`、`articleList`
- CSS 类名使用 kebab-case：`.user-card`、`.article-item`
- Props 使用 camelCase，但在模板中使用 kebab-case：`:user-name="..."`

**事件命名**：
- 使用 kebab-case：`@update-user`、`@delete-item`
- 表示动作的动词在前：`@submit-form`、`@close-modal`

#### 公共组件沉淀
当你在开发过程中发现某个组件在多个地方用到，就应该把它提取到 `components/common/` 目录下：

**适合沉淀为公共组件的场景**：
- 基础 UI 元素（按钮、输入框、下拉菜单、弹窗、提示框）
- 布局组件（栅格系统、容器、分割面板）
- 常用功能组件（分页器、加载动画、日期选择器、文件上传）
- 反馈组件（加载中、空状态、错误提示、确认对话框）

**公共组件的要求**：
- 和业务无关，不包含任何业务数据或业务逻辑
- 接口设计通用，支持通过 props 来定制外观和行为
- 有完整的文档和示例（至少要有注释说明每个 prop 的作用）
- 充分测试各种边界情况

---

## 练习建议

1. **从简单的组件开始**：先实现一个 `BaseButton` 组件，支持不同的样式类型（主要、次要、危险）和尺寸（大、中、小）
2. **尝试组件拆分**：把一个卡片列表页面拆成 `Container`（容器组件）、`List`（列表组件）和 `Card`（单卡片组件）三层
3. **实践通信方式**：创建一个待办事项应用，使用 props 传递数据，events 响应用户操作，v-model 实现输入绑定
4. **学习阅读开源项目**：在 GitHub 上搜索 Vue 项目，看别人的组件是如何拆分和组织的
5. **进阶练习**：尝试实现一个树形组件（Tree）或选项卡组件（Tabs），这两个组件能很好地练习递归组件和插槽的使用
