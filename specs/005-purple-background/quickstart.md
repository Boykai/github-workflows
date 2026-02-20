# Quickstart Guide: Add Purple Background Color to App

**Feature**: 005-purple-background | **Date**: 2026-02-20  
**Estimated Time**: 5–10 minutes  
**Prerequisites**: Git access, text editor

## Overview

This guide walks through implementing the purple background (#7C3AED) for the Agent Projects app. The implementation involves adding a CSS custom property and updating CSS rules across 2 files.

**Complexity**: ⭐ Trivial (1/5)  
**Risk Level**: Minimal  
**Rollback**: Instant (single git revert)

---

## Step 1: Verify Current State

```bash
cd /home/runner/work/github-workflows/github-workflows
grep "background:" frontend/src/index.css
```

**Expected Output**: `background: var(--color-bg-secondary);`

---

## Step 2: Add Purple CSS Variable

### 2.1 Edit `frontend/src/index.css` — `:root` block

Find:
```css
  --color-bg-secondary: #f6f8fa;
  --color-border: #d0d7de;
```

Add `--color-bg-app` between them:
```css
  --color-bg-secondary: #f6f8fa;
  --color-bg-app: #7C3AED;
  --color-border: #d0d7de;
```

### 2.2 Edit `frontend/src/index.css` — `html.dark-mode-active` block

Find:
```css
  --color-bg-secondary: #161b22;
  --color-border: #30363d;
```

Add `--color-bg-app` between them:
```css
  --color-bg-secondary: #161b22;
  --color-bg-app: #7C3AED;
  --color-border: #30363d;
```

### 2.3 Update body background

Find:
```css
  background: var(--color-bg-secondary);
```

Replace with:
```css
  background: var(--color-bg-app);
```

---

## Step 3: Update Text Colors for Contrast

### 3.1 Edit `frontend/src/App.css` — Login heading

Find:
```css
.app-login h1 {
  font-size: 32px;
  color: var(--color-text);
}
```

Replace color:
```css
.app-login h1 {
  font-size: 32px;
  color: #ffffff;
}
```

### 3.2 Edit `frontend/src/App.css` — Login paragraph

Find:
```css
.app-login p {
  color: var(--color-text-secondary);
```

Replace color:
```css
.app-login p {
  color: #E9D5FF;
```

---

## Step 4: Verify

```bash
grep "color-bg-app" frontend/src/index.css
```

**Expected**: 3 matches (`:root`, `dark-mode-active`, `body`)

```bash
grep "#ffffff\|#E9D5FF" frontend/src/App.css
```

**Expected**: 2 matches (login h1, login p)
