# Sidebar Icon Vertical Alignment Design

## Goal

When the desktop sidebar is collapsed, align the top logo, every navigation icon, and the bottom expand icon on the same vertical center line.

## Scope

- Update only the collapsed desktop sidebar layout in `webapp/letapp/src/layouts/MainLayout.vue`.
- Preserve the expanded desktop sidebar and mobile drawer layouts.
- Do not change icon sizes, sidebar widths, navigation spacing, colors, or interaction behavior.

## Design

The navigation links and bottom toggle already center their icon containers within the collapsed sidebar. The top logo remains offset because its header keeps horizontal padding and the logo link uses its intrinsic width.

In the collapsed state, the top header will use zero horizontal padding and center its only child. The expanded state will retain its existing padding and `justify-between` alignment.

## Verification

- In collapsed desktop mode, measure the horizontal center of the logo, navigation icons, and expand icon against the sidebar center.
- Each center must differ from the sidebar center by no more than 1 px.
- Confirm the expanded sidebar and mobile drawer remain visually unchanged.
- Run the frontend production build.
