# Sidebar Icon Vertical Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Center every icon in the collapsed desktop sidebar on the same vertical line.

**Architecture:** Keep the existing navigation and toggle layouts, which already center their icons. Change only the top desktop sidebar header so its collapsed-state child is centered without horizontal padding, while preserving the expanded-state classes.

**Tech Stack:** Vue 3 SFC, TypeScript, Tailwind CSS, Vite, browser DOM geometry checks.

## Global Constraints

- Modify only the collapsed desktop sidebar layout in `webapp/letapp/src/layouts/MainLayout.vue`.
- Preserve expanded desktop and mobile drawer layouts.
- Do not change icon sizes, sidebar widths, navigation spacing, colors, or behavior.
- The horizontal center error for each collapsed sidebar icon must be no more than 1 px.

---

### Task 1: Center The Collapsed Sidebar Logo

**Files:**
- Modify: `webapp/letapp/src/layouts/MainLayout.vue:10-13`
- Test: browser geometry assertion against the rendered `.app-sidebar`

**Interfaces:**
- Consumes: `sidebarExpanded: Ref<boolean>` and the existing `desktopSidebarWidth` computation.
- Produces: collapsed header classes `justify-center px-0`; expanded classes remain `justify-between px-5`.

- [ ] **Step 1: Start the frontend and open the desktop home page**

Run:

```powershell
cd D:\probject\oj\webapp\letapp
npm.cmd run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

Open `http://127.0.0.1:5174/`, set a desktop viewport at least 1024 px wide, and click the button with `aria-label="收起侧边栏"`.

- [ ] **Step 2: Run the failing geometry assertion**

Evaluate in the rendered page:

```javascript
const sidebar = document.querySelector('.app-sidebar');
const logo = sidebar?.querySelector(':scope > div:first-child a > span');
const navIcons = [...document.querySelectorAll('.app-sidebar .sidebar-link .iconify')];
const toggleIcon = document.querySelector('.app-sidebar .sidebar-toggle .iconify');
const sidebarCenter = sidebar.getBoundingClientRect().left + sidebar.getBoundingClientRect().width / 2;
const targets = [logo, ...navIcons, toggleIcon];
const deltas = targets.map((element) => {
  const rect = element.getBoundingClientRect();
  return Math.abs(rect.left + rect.width / 2 - sidebarCenter);
});
if (deltas.some((delta) => delta > 1)) {
  throw new Error(`Sidebar icon centers are misaligned: ${deltas.join(', ')}`);
}
```

Expected before the fix: FAIL because the first delta, for the logo, is about 12 px while the other deltas are at most 1 px.

- [ ] **Step 3: Implement the minimal collapsed-state class change**

In `webapp/letapp/src/layouts/MainLayout.vue`, replace the top header wrapper with:

```vue
<div
  class="flex h-20 items-center gap-3"
  :class="
    sidebarExpanded
      ? 'justify-between px-5'
      : 'justify-center px-0'
  "
>
```

Do not change the anchor, logo, navigation links, toggle button, sidebar width constants, or mobile drawer.

- [ ] **Step 4: Re-run the geometry assertion**

Repeat Step 2 after Vite hot reload.

Expected after the fix: PASS; every delta is at most 1 px.

- [ ] **Step 5: Verify unaffected states**

Click the button with `aria-label="展开侧边栏"` and confirm:

- the logo and `Let Coding` text remain left aligned with the existing 20 px header padding;
- all navigation labels remain visible;
- the mobile drawer markup and behavior are unchanged in the source diff.

- [ ] **Step 6: Run the production build**

Run:

```powershell
cd D:\probject\oj\webapp\letapp
npm.cmd run build
```

Expected: exit code 0 from `vue-tsc -b` and `vite build`.

- [ ] **Step 7: Commit only the alignment change and plan**

```powershell
cd D:\probject\oj
git add docs/superpowers/plans/2026-08-11-sidebar-icon-vertical-alignment.md webapp/letapp/src/layouts/MainLayout.vue
git commit -m "fix: align collapsed sidebar icons"
```

Before committing, verify `webapp/letapp/public/learn/c-language/chapters/04-selection-structure.md` is not staged.
