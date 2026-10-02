---
name: accessibility
description: Accessibility guidelines for TUI, CLI, and web interfaces
invocation: auto
---

# Accessibility Guidelines

## Color Contrast (WCAG AA)

| Content             | Min Ratio |
| ------------------- | --------- |
| Normal text (<18pt) | **4.5:1** |
| Large text (18pt+)  | **3:1**   |
| UI components       | **3:1**   |

**Don't rely on color alone** — add icons, text labels, or patterns: `● Running` not just yellow.

## Theme Variables

```css
.widget {
  background: $surface;
  color: $text;
} /* Auto-contrasting */
.status-running {
  background: $surface;
  color: $warning;
  text-style: bold;
}
```

`$text` (primary) | `$text-muted` (secondary) | `$text-disabled` (inactive)

## Focus & Keyboard

```python
class MyWidget(Static, can_focus=True):
    def on_focus(self) -> None: self.add_class("focused")
```

| Key           | Action             |
| ------------- | ------------------ |
| Tab/Shift+Tab | Navigate focusable |
| Enter/Space   | Activate           |
| Escape        | Close/cancel       |
| Arrows        | Navigate within    |
| q             | Quit (CLI)         |

**Mouse events need keyboard equivalents**: `on_click` → focus + Enter

## Screen Readers

- Text labels, not symbols alone: `"● Running"` not `"●"`
- Content order = visual reading order
- `display: none` hides from readers; off-screen doesn't

## Checklist

- [ ] Text: 4.5:1 (3:1 large)
- [ ] UI: 3:1
- [ ] Status not color-only
- [ ] All interactive keyboard accessible
- [ ] Focus visible
- [ ] Tab order = visual
