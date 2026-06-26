#!/usr/bin/env python3
"""
Obsidian 笔记 → Jekyll 文章 转换器

功能：
  - 从 Obsidian 导出的 Markdown 转为 Chirpy 兼容的文章格式
  - 处理 [[wikilinks]] → 标准 Markdown 链接
  - 处理 ![[image]] → Markdown 图片
  - 自动生成/更新 Jekyll front matter
  - 自动重命名为 YYYY-MM-DD-slug.md 格式

用法：
  python3 tools/obsidian-to-post.py <源文件> [--category 分类] [--tags 标签1,标签2]
"""

import os
import re
import sys
import argparse
from datetime import datetime, timezone, timedelta


def parse_args():
    parser = argparse.ArgumentParser(description="Obsidian → Jekyll 文章转换器")
    parser.add_argument("source", help="Obsidian Markdown 源文件路径")
    parser.add_argument("--category", default="笔记", help="文章分类 (默认: 笔记)")
    parser.add_argument("--tags", default="", help="文章标签，逗号分隔 (默认: 空)")
    parser.add_argument("--date", default="", help="文章日期 YYYY-MM-DD hh:mm (默认: 文件修改时间)")
    parser.add_argument("--output-dir", default="_posts", help="输出目录 (默认: _posts)")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际写入文件")
    return parser.parse_args()


def convert_wikilinks(content):
    """将 [[链接]] 和 [[链接|别名]] 转为 Markdown 链接"""
    # [[title]] → [title](title)
    # [[title|alias]] → [alias](title)
    # [[title#section]] → [title](title#section)
    def replace_wikilink(m):
        full = m.group(1)
        if '|' in full:
            target, alias = full.split('|', 1)
        else:
            target = full
            alias = full

        # 去掉 #section 部分用于显示
        display = alias.split('#')[-1] if '#' in alias else alias
        return f'[{display}]({target})'

    return re.sub(r'\[\[([^\]]+)\]\]', replace_wikilink, content)


def convert_obsidian_images(content):
    """将 Obsidian ![[image.png]] 转为 Markdown 图片"""
    def replace_img(m):
        target = m.group(1)
        return f'![{target}](/{target})'

    return re.sub(r'!\[\[([^\]]+)\]\]', replace_img, content)


def convert_callouts(content):
    """将 Obsidian callout 转为普通引用块"""
    # > [!note] ... → > **Note:** ...
    # > [!warning] ... → > **Warning:** ...
    # > [!tip] ... → > **Tip:** ...
    callout_map = {
        'note': '📝 笔记',
        'warning': '⚠️ 警告',
        'tip': '💡 提示',
        'info': 'ℹ️ 信息',
        'danger': '🚨 危险',
        'example': '📖 示例',
        'quote': '💬 引用',
    }

    def replace_callout(m):
        callout_type = m.group(1).lower()
        body = m.group(2)
        label = callout_map.get(callout_type, callout_type.capitalize())
        return f'> **{label}：**\n{body}'

    return re.sub(
        r'> \[!(\w+)\][+-]?\s*\n((?:>\s?.*\n?)*)',
        replace_callout,
        content
    )


def strip_obsidian_comments(content):
    """去除 Obsidian 注释 %% ... %%"""
    return re.sub(r'%%.*?%%', '', content, flags=re.DOTALL)


def extract_title_from_content(content):
    """尝试从内容提取标题"""
    # 第一个 # 标题
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return None


def generate_front_matter(title, args, dt):
    """生成 Chirpy 兼容的 front matter"""
    bj_tz = timezone(timedelta(hours=8))
    date_str = dt.astimezone(bj_tz).strftime('%Y-%m-%d %H:%M:%S %z')

    tags_list = [t.strip() for t in args.tags.split(',') if t.strip()] if args.tags else []
    category_list = [c.strip() for c in args.category.split(',') if c.strip()]

    fm = [
        "---",
        f"title: {title}",
        f"date: {date_str}",
        f"categories: {category_list}",
        f"tags: {tags_list}",
        "---",
        ""
    ]
    return '\n'.join(fm)


def slugify(title):
    """生成 URL 友好的 slug"""
    # 中文标题用拼音首字母，英文直接保留
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


def get_file_date(filepath):
    """获取文件的修改时间"""
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime)


def main():
    args = parse_args()

    # 读取源文件
    if not os.path.exists(args.source):
        print(f"❌ 文件不存在: {args.source}")
        sys.exit(1)

    with open(args.source, 'r', encoding='utf-8') as f:
        raw = f.read()

    # 检测是否已有 Jekyll front matter
    has_front_matter = raw.startswith('---\n') or raw.startswith('---\r\n')

    if has_front_matter:
        # 已有 front matter，只处理内容
        parts = re.split(r'^---\s*$', raw, maxsplit=2, flags=re.MULTILINE)
        if len(parts) >= 3:
            fm = parts[1].strip()
            body = parts[2].strip()
        else:
            fm = ''
            body = raw
    else:
        # 提取标题
        title = extract_title_from_content(raw)
        if title:
            # 移除已有的 # 标题行
            body = re.sub(r'^#\s+.+\n', '', raw, count=1).strip()
        else:
            # 用文件名作为标题
            title = os.path.splitext(os.path.basename(args.source))[0]
            body = raw.strip()

        # 设置/解析日期
        if args.date:
            dt = datetime.strptime(args.date, '%Y-%m-%d %H:%M')
        else:
            dt = get_file_date(args.source)

        fm = generate_front_matter(title, args, dt)

    # 转换 Obsidian 语法
    body = convert_wikilinks(body)
    body = convert_obsidian_images(body)
    body = convert_callouts(body)
    body = strip_obsidian_comments(body)

    # 生成输出文件名
    title_for_slug = extract_title_from_content(raw) or os.path.splitext(os.path.basename(args.source))[0]
    slug = slugify(title_for_slug)

    if args.date:
        dt = datetime.strptime(args.date, '%Y-%m-%d %H:%M')
    else:
        dt = get_file_date(args.source)

    date_prefix = dt.strftime('%Y-%m-%d')
    output_filename = f'{date_prefix}-{slug}.md'
    output_path = os.path.join(args.output_dir, output_filename)

    # 组装最终内容
    final = fm + '\n' + body

    if args.dry_run:
        print(f"📄 预览: {output_path}")
        print("---")
        print(final[:500])
        print("...")
    else:
        os.makedirs(args.output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final)
        print(f"✅ 已生成: {output_path}")
        print(f"   标题: {title_for_slug}")
        print(f"   分类: {args.category}")
        print(f"   标签: {args.tags or '(无)'}")


if __name__ == '__main__':
    main()
