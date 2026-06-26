---
title: 第一篇 Obsidian 同步笔记
date: 2026-06-27 12:00:00 +0800
categories: [笔记]
tags: [obsidian, jekyll, 教程]
---

## 欢迎 👋

这是从 Obsidian 同步到博客的第一篇文章。

## Obsidian 语法 → Jekyll 兼容

### Wikilinks 转换

Obsidian 的 `[[双链]]` 语法会被转换器自动处理为 Markdown 链接。

### Callout 转换

> [!note] 这是一个 Obsidian 风格的 callout
> 会被转换为普通引用块显示。

### 代码块

```python
print("代码高亮完美支持！")
```

### 数学公式 (KaTeX)

行内公式 $E = mc^2$ 和块级公式：

$$ \int_a^b f(x) dx $$

## 发布流程

1. 在 Obsidian 中写作
2. 使用 GitHub Publisher 插件一键推送到仓库
3. GitHub Actions 自动构建部署
4. 网站更新完成 🎉
