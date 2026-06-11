# AGENTS.md - Development Guidelines for LetApp

**请使用中文问答或中文描述**

This file contains coding standards, build commands, and development guidelines for agentic coding agents working on this Vue 3 + TypeScript + Vite project.

## Build Commands

### Essential Commands
- `npm install` - Install dependencies
- `npm run dev` - Start development server (localhost:5173)
- `npm run build` - Build for production (runs vue-tsc -b && vite build)
- `npm run preview` - Preview production build locally
- `vue-tsc -b` - TypeScript type checking (no specific npm script, run directly)

### Type Checking
Always run `vue-tsc -b` before committing to ensure type safety. The project uses strict TypeScript configuration.

## Code Style Guidelines

### TypeScript Configuration
- Strict mode enabled with comprehensive linting rules
- No unused locals/parameters allowed
- No fallthrough cases in switch
- All Vue components use `<script setup lang="ts">`

### Import Organization
```typescript
// Vue imports first
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

// Third-party libraries
import MarkdownIt from 'markdown-it'
import { Icon } from '@iconify/vue'

// Internal imports (stores, components, types)
import { useThemeStore } from './stores/theme'
import type { Content } from './types'
```

### Component Structure
```vue
<script setup lang="ts">
// 1. Imports (Vue first, then third-party, then internal)
// 2. Interface/type definitions
// 3. Props with withDefaults if needed
// 4. Store instances
// 5. Ref/reactive variables
// 6. Computed properties
// 7. Methods/functions
// 8. Lifecycle hooks (onMounted, etc.)
</script>

<template>
  <!-- Template content with semantic HTML -->
</template>

<style scoped>
@import "prismjs/themes/prism-tomorrow.min.css";

/* Use Tailwind classes primarily */
/* Custom CSS only when necessary */
/* Use :deep() for component style penetration */
</style>
```

### Naming Conventions
- **Components**: PascalCase (e.g., `MarkdownComponent.vue`)
- **Files**: kebab-case for utilities, PascalCase for components
- **Variables**: camelCase with descriptive names
- **Constants**: UPPER_SNAKE_CASE for environment/constants
- **Props**: camelCase with clear interfaces

### Vue 3 Composition API Patterns
```typescript
// Use defineProps with TypeScript interfaces
interface Props {
  content?: Content
  showNav?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showNav: true
})

// Use storeToRefs for reactive store properties
import { storeToRefs } from 'pinia'
const themeStore = useThemeStore()
const { theme } = storeToRefs(themeStore)

// Computed properties for derived state
const date = computed(() => 
  props.content?.date ? new Date(props.content.date).toLocaleDateString('zh-CN') : ''
)
```

### CSS/Style Guidelines
- **Primary**: Use Tailwind CSS classes
- **Custom CSS**: Only in `<style scoped>` blocks when necessary
- **Theme Support**: Always include dark mode variants
- **Component Styling**: Use `:deep()` for child component styling
- **Responsive**: Mobile-first with `md:` and `lg:` breakpoints

```css
/* Correct usage example */
.markdown-content :deep(h1) {
  @apply text-3xl mt-8 mb-4 font-semibold;
}

.dark .markdown-content :deep(h1) {
  @apply text-white;
}
```

### Error Handling
- Use try-catch blocks for async operations
- Provide user feedback via Naive UI message components
- Log errors for debugging but don't expose sensitive data

### File Organization
```
src/
├── components/          # Reusable Vue components
├── layouts/            # Layout components
├── pages/              # Page components
├── stores/             # Pinia stores (one file per store)
├── types/              # TypeScript type definitions
├── main.ts            # App entry point
├── router.ts          # Vue Router configuration
├── App.vue            # Root component
└── style.css          # Global styles and theme variables
```

### Store Patterns
```typescript
// Use Composition API stores
export const useThemeStore = defineStore('theme', () => {
  const state = ref(initialValue)
  const computedValue = computed(() => /* logic */)
  
  function action() {
    // mutation logic
  }
  
  return { state, computedValue, action }
})
```

### Markdown Integration
- Project uses markdown-it with extensive plugin configuration
- Support for task lists, footnotes, attributes, code highlighting
- Custom containers: warning, danger, tip
- Always use Prism for syntax highlighting
- Handle anchor navigation and TOC generation

### Theme System
- Light/dark theme support via CSS custom properties
- Naive UI theme provider integration
- System preference detection
- Theme persistence in localStorage
- Use `.dark` class on document root

### Testing (if implemented)
- No current test framework detected
- When adding tests, check package.json for test scripts
- Follow Vue Test Utils patterns if added

### Git & Commit Workflow
- Use semantic commit messages
- Run type checking before commits: `vue-tsc -b`
- Check build passes: `npm run build`

### Package Management
- Use npm (package-lock.json present)
- Dependencies are up-to-date, check versions before major updates
- Vue 3.5.24, TypeScript 5.9.3, Vite 7.1.11

## Project Specific Notes

### Chinese Language Support
- Project includes Chinese UI text and documentation
- Use proper Unicode handling for Chinese characters
- Date formatting uses 'zh-CN' locale

### Markdown Features
- Comprehensive markdown rendering with custom plugins
- TOC (Table of Contents) generation
- Scroll-based navigation highlighting
- Code block syntax highlighting
- Mermaid diagram support

### Performance Considerations
- Use `nextTick()` for DOM-dependent operations
- Lazy load route components
- Debounce scroll listeners
- Optimize large markdown parsing

### Browser Support
- Modern browsers only (ES2020+)
- Uses native CSS features (no PostCSS plugins needed)
- Vite's native ES module build target

## Development Workflow

1. **Setup**: Run `npm install`
2. **Development**: `npm run dev` for hot reload
3. **Type Check**: `vue-tsc -b` before commits
4. **Build**: `npm run build` to verify production build
5. **Preview**: `npm run preview` to test production build

This project follows Vue 3 + TypeScript + Vite best practices with emphasis on type safety, component reusability, and maintainable code architecture.