# CLAUDE.md

**请使用中文问答或中文描述**

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**代码综合平台 (Code Comprehensive Platform)** - A Vue 3-based web application providing a code development and learning environment.

### Core Features
- **Code Editor Integration**: Supports multiple programming languages
- **Advanced Markdown Support**: Real-time preview with extended syntax (task lists, diagrams, custom containers)
- **Theme Switching**: Light/dark mode with system preference detection
- **Responsive Design**: Mobile-first approach with adaptive layouts
- **Modular Architecture**: Vue 3 Composition API with clear separation of concerns
- **Type Safety**: Full TypeScript implementation with strict mode

### Environment Requirements
- **Node.js**: Version 18.0 or higher required
- **Package Manager**: npm (package-lock.json present)
- **Recommended IDE**: VS Code with extensions:
  - Vue Language Features (Volar)
  - TypeScript Vue Plugin (Volar)
  - Tailwind CSS IntelliSense
  - Vue VSCode Snippets

## Build & Development Commands

### Essential Commands
- `npm install` - Install project dependencies
- `npm run dev` - Start Vite dev server at http://localhost:5173 with HMR
- `npm run build` - Type check with vue-tsc and build for production
- `npm run preview` - Preview production build locally
- `vue-tsc -b` - Run TypeScript type checking (always run before committing)

### Important Notes
- **Always run `vue-tsc -b` before committing** - project uses strict TypeScript mode
- The build command runs type checking first, so build failures often indicate type errors
- Dev server defaults to port 5173 but can be changed with `--port` flag

## Project Architecture

This is a **Vue 3 + TypeScript + Vite** web application for a "代码综合平台" (Code Comprehensive Platform) - a code editor and learning environment with heavy emphasis on Markdown rendering.

### Tech Stack
- **Framework**: Vue 3.5+ (Composition API with `<script setup>`)
- **Language**: TypeScript 5.9+ (strict mode enabled)
- **Build Tool**: Vite 7.1+
- **State Management**: Pinia 3.0+ (Composition API stores)
- **Routing**: Vue Router 4.6+ (nested routes with lazy loading)
- **Styling**: Tailwind CSS 4.1+ (utility-first)
- **UI Components**: Naive UI 2.43+ (theme provider integration)
- **Markdown**: markdown-it 14.1+ with extensive plugin ecosystem

### Directory Structure
```
src/
├── components/      # Reusable Vue components
├── layouts/         # Layout wrappers (MainLayout with nav)
├── pages/           # Page components (route targets)
├── stores/          # Pinia stores (Composition API pattern)
├── types/           # TypeScript type definitions (.d.ts)
├── main.ts         # App entry point (Pinia + Router setup)
├── router.ts       # Vue Router config (nested routes)
├── App.vue         # Root component (theme provider)
└── style.css       # Global CSS variables and base styles
```

### Application Bootstrap Flow
1. `main.ts` → Creates Vue app, registers Pinia and Router
2. `App.vue` → Wraps with Naive UI providers (theme, dialog, message)
3. `router.ts` → Renders MainLayout for all routes
4. `MainLayout.vue` → Sticky header with navigation + theme toggle + `<router-view/>`
5. Pages render inside the layout

### State Management Pattern (Pinia)
All stores use Composition API pattern:
```typescript
export const useXxxStore = defineStore('xxx', () => {
  const state = ref(initialValue)
  const computed = computed(() => /* ... */)
  function action() { /* ... */ }
  return { state, computed, action }
})
```

**Theme Store** (`stores/theme.ts`):
- Manages light/dark theme preference
- Syncs with localStorage and system preference
- Updates `.dark` class on document root
- Provides Naive UI theme object for components

### Standard Development Workflow

When adding new features, follow this 5-layer architecture:

1. **Services Layer** (`src/services/`) - Currently empty, will contain API calls
2. **State Layer** (`src/stores/`) - Pinia stores with Composition API
3. **Component Layer** (`src/pages/` or `src/components/`) - UI components
4. **Route Configuration** (`router.ts`) - Add lazy-loaded routes
5. **Type Definitions** (`src/types/`) - TypeScript interfaces

See DEVELOPMENT_GUIDE.md for detailed examples of each layer.

### Component Structure Convention
Follow this order in `<script setup>`:
1. Vue imports (ref, computed, onMounted, etc.)
2. Third-party imports (MarkdownIt, Icon, etc.)
3. Internal imports (stores, components, types)
4. Interface/type definitions
5. Props with withDefaults
6. Store instances (use storeToRefs for reactivity)
7. Reactive data (ref/reactive)
8. Computed properties
9. Methods/functions
10. Lifecycle hooks

Use Tailwind classes in templates, scoped CSS only when necessary.

### Markdown System Architecture

The **MarkdownComponent.vue** is a complex, feature-rich component:

**Features**:
- Real-time Markdown to HTML conversion
- Table of Contents (TOC) generation with hierarchical structure
- Syntax highlighting via Prism.js
- Mermaid diagram rendering
- Custom container blocks (warning, danger, tip)
- Task list support with checkboxes
- Responsive layout with sidebar TOC

**Plugins Used**:
- `markdown-it-anchor` - Heading IDs and anchors
- `markdown-it-footnote` - Footnote references
- `markdown-it-task-lists` - GitHub-style checkboxes
- `markdown-it-attrs` - Element attributes `{.class #id}`
- `markdown-it-expand-tabs` - Tab expansion
- `markdown-it-sup` / `markdown-it-sub` - Superscript/subscript
- `markdown-it-mark` - Text marking `==text==`
- `markdown-it-container` - Custom blocks `:::warning`
- `@jsonlee_12138/markdown-it-mermaid` - Diagram support

**Supported Syntax Examples**:
- Task lists: `- [ ]` 未完成, `- [x]` 已完成
- Text marking: `==高亮文本==`
- Subscript: `H~2~O`, Superscript: `X^2^`
- Custom attributes: `# 标题 {.class #id}`
- Custom containers: `:::warning 警告内容 :::`

See README.md for comprehensive markdown syntax examples.

**Performance Notes**:
- Uses `nextTick()` for DOM-dependent operations (TOC generation)
- Code highlighting deferred with `setTimeout`
- Debounced scroll listeners for navigation highlighting

### Router Configuration

- Main route (`/`) renders MainLayout with nested children routes
- All pages lazy-loaded: `component: () => import('./pages/Page.vue')`
- Page titles set via `meta.title` in navigation guard
- Authentication guards commented out (future feature)

### Theme System

- Light/dark mode with system preference detection via `matchMedia` API
- Persists in localStorage
- `.dark` class on document root, Naive UI theme provider
- Use `dark:` prefix in Tailwind classes

### Styling Approach

1. Tailwind utility classes (primary)
2. Scoped CSS with `:deep()` for child elements
3. Global styles in `style.css` (minimal)

Mobile-first responsive design with `md:` and `lg:` breakpoints.

## Code Standards

### TypeScript
- Strict mode with no unused locals/parameters
- Use `import type` for type-only imports
- Extends `@vue/tsconfig/tsconfig.dom.json`

### Naming Conventions
- Components: PascalCase (`MarkdownComponent.vue`)
- Variables: camelCase (`userName`)
- Constants: UPPER_SNAKE_CASE (`API_BASE_URL`)
- Types/Interfaces: PascalCase (`User`, `ApiResponse`)

### Store Pattern (Pinia Composition API)
```typescript
export const useXxxStore = defineStore('xxx', () => {
  const state = ref(value)
  const computed = computed(() => /* ... */)
  function action() { /* ... */ }
  return { state, computed, action }
})

// Access in components
import { storeToRefs } from 'pinia'
const store = useXxxStore()
const { state } = storeToRefs(store)  // Reactive refs
```

## Important Files & Patterns

### Key Configuration Files
- `vite.config.ts` - Vite config (Vue + Tailwind plugins)
- `tsconfig.json` - Root TS config (references app and node configs)
- `tsconfig.app.json` - Strict app TS config
- `package.json` - Dependencies and scripts

### Critical Paths
- **Entry Point**: `src/main.ts`
- **Root Component**: `src/App.vue` (theme provider setup)
- **Router Config**: `src/router.ts`
- **Main Layout**: `src/layouts/MainLayout.vue` (navigation + header)
- **Theme Store**: `src/stores/theme.ts` (dark mode logic)
- **Markdown Component**: `src/components/MarkdownComponent.vue` (complex rendering)

### Development Guidelines Documents
- **DEVELOPMENT_GUIDE.md** - Comprehensive beginner's guide (Chinese)
- **AGENTS.md** - Code standards for AI agents (English)
- **README.md** - Project overview (Chinese)

## Language & Localization

**Chinese Language Project**:
- UI text and documentation in Chinese (Simplified)
- Date formatting uses `'zh-CN'` locale
- Proper Unicode handling for Chinese characters
- Comments and variable names may be in English or Chinese

## Performance Considerations

- Lazy load routes: `() => import('./pages/Page.vue')`
- Use `computed()` for cached derived state
- `nextTick()` for DOM-dependent operations
- Debounce scroll/input listeners
- Avoid unnecessary reactive data
- Code splitting at route level

## Common Patterns

### Async Store Operations
```typescript
async function fetchData() {
  try {
    isLoading.value = true
    error.value = null
    const response = await apiCall()
    data.value = response.data
  } catch (err) {
    error.value = 'Error message'
  } finally {
    isLoading.value = false
  }
}
```

### Theme Toggle
```typescript
const themeStore = useThemeStore()
themeStore.toggleTheme()  // Switches and persists
```

## Development Workflow

1. `npm install` - Setup dependencies
2. `npm run dev` - Start development server
3. `vue-tsc -b` - Type check (before commits)
4. `npm run build` - Verify production build
5. `npm run preview` - Test built app

**Pre-Commit**: Type check + build verification + test dark mode support

## Future Architecture Notes

- **Services Layer**: Directory exists but empty - will contain API integration
- **Authentication**: Router guards commented out, store structure anticipates auth
- **Permissions System**: Identity levels mentioned in MarkdownComponent (Member, Department, Minister, President, Founder)
- **Multi-User Platform**: Suggests content management with role-based access

## Browser Support

- **Chrome**: Latest version
- **Firefox**: Latest version
- **Safari**: Latest version
- **Edge**: Latest version
- **Not Supported**: IE11
- **Target**: Modern browsers with ES2020+ support
- **Build**: Native ES modules (Vite)
- **CSS Features**: Grid, Flexbox, Custom Properties

## Common Issues & Solutions

**Q: How to add a new page?**
Create component in `src/pages/`, add route in `router.ts` with lazy loading.

**Q: How to add state management?**
Create Pinia store in `src/stores/` using Composition API pattern.

**Q: Type checking fails?**
Run `vue-tsc -b` for errors. Check `tsconfig.app.json` strict mode rules.

**Q: How to customize Markdown styles?**
Use `:deep()` selector in scoped styles with Tailwind `@apply`.

**Q: Port conflict?**
Run `npm run dev -- --port 3000` or modify `vite.config.ts`.

**Q: Dark mode in custom CSS?**
Use `.dark` selector or Tailwind's `dark:` prefix.
