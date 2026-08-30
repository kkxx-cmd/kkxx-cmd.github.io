import re

with open('update_news.py', 'r') as f:
    lines = f.readlines()

# Find the line index of the try block in the fallback mode.
# We know that the fallback mode is after the skill fetch fails.
# We'll look for the line: "        try:"
# and then replace until the line that is at the same indentation as the try and contains "update_list"
# but note: there might be multiple try blocks.

# We'll do a simple approach: find the line that contains "        try:" and then the next line that contains "from kkxx_generate"
# and then we'll replace until the line that contains "update_list" at the same indentation level.

# Let's first find the index of the line that contains "        try:" in the fallback section.
# We know that the fallback section is after the skill fetch fails and we have a comment: "⚠️ 降级报错: unexpected '{' in field name"

# We'll search for the line: "        try:"
# and then we'll assume that the fallback block ends at the line that has the same indentation as the try and contains "update_list"

# We'll do:

in_fallback = False
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if line.strip() == "⚠️ 降级报错: unexpected '{' in field name":
        in_fallback = True
    if in_fallback and line.strip().startswith("try:"):
        start_idx = i
        # Now we look for the end of the block: the line that is at the same indentation as the try and contains "update_list"
        # But note: the try block might be nested? We'll assume it's not.
        # We'll look for the line that has the same indentation as the try line and is after the try block.
        # We'll break when we find a line that has less indentation than the try line and is not empty.
        try_indent = len(line) - len(line.lstrip())
        for j in range(i+1, len(lines)):
            if lines[j].strip() == "":
                continue
            indent = len(lines[j]) - len(lines[j].lstrip())
            if indent < try_indent:
                # We've gone out of the try block.
                end_idx = j-1
                break
        if end_idx == -1:
            end_idx = len(lines)-1
        break

if start_idx == -1 or end_idx == -1:
    print("Could not find the fallback try block.")
    exit(1)

# Now we replace lines[start_idx:end_idx+1] with our new block.
new_block = '''        try:
            from kkxx_generate import fetch_news as fallback_fetch
            old_news = fallback_fetch()
            if old_news:
                cards = make_cards([{"title": n["title"], "url": n["link"], "source": n["source"]} for n in old_news])
            else:
                old_news = []
                cards = ""
        except Exception as e:
            print(f"Fallback error: {e}")
            old_news = []
            cards = ""

        html = HTML_TEMPLATE.replace('{title}', "每日新闻 · " + date_cn).replace('{date_cn}', date_cn).replace('{cards}', cards)
        with open(f"blog/news-{date_str}.html", "w", encoding="utf-8") as f:
            f.write(html)
        report += f"✅ 降级模式: {len(old_news)}条\\n"
        update_list("blog/news.html", f'<a class="post" href="news-{date_str}.html"><h3>📰 每日新闻 · {date_cn}</h3><div class="meta">全球热点 · {len(old_news)}条</div></a>')
'''

# Note: we must keep the indentation level of the original try block.
# The new_block string already has the same indentation (8 spaces) for the first line.

# Replace the lines
lines[start_idx:end_idx+1] = [new_block]

# Write the file
with open('update_news.py', 'w') as f:
    f.writelines(lines)

print("Fixed the fallback block.")
