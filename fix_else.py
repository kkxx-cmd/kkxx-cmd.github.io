import re

with open('update_news.py', 'r') as f:
    lines = f.readlines()

# Find the line index of the outer else: that is after the skill fetch failure.
# We'll look for the line: "        else:" that is preceded by a line containing "if news:" and then the skill success block.
# But we can also look for the line: "        report += \"⚠️ Skill获取失败，降级到纯爬虫模式\\n\""
# and then replace from there until the line before "    ok, err = git_push"

# Let's find the start and end indices.

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if line.strip() == 'report += "⚠️ Skill获取失败，降级到纯爬虫模式\\n"':
        start_idx = i
        # Now we need to find the end of the else block.
        # We'll look for the line that is at the same indentation level as the else and is not part of the else block.
        # The else block starts at the line with the else (which is at some indentation) and ends when we return to a lower indentation.
        # We'll assume the else block is indented by 8 spaces (two tabs or two spaces? Actually, we see 8 spaces in the file).
        # We'll look for the line that has less than 8 spaces of indentation and is not empty, after the start.
        # But note: the else block might have nested blocks with more indentation.
        # We'll break when we find a line that has indentation <= the indentation of the else line and is not empty and not part of a comment? 
        # Actually, we can look for the line that starts with "    ok, err = git_push" (which is at 4 spaces? Let's check).

        # Let's instead look for the line that contains "    ok, err = git_push" and set end_idx to the line before that.
        for j in range(i+1, len(lines)):
            if lines[j].strip().startswith('ok, err = git_push'):
                end_idx = j-1
                break
        if end_idx == -1:
            end_idx = len(lines)-1
        break

if start_idx == -1 or end_idx == -1:
    print("Could not find the else block to replace.")
    exit(1)

# Now we replace lines[start_idx:end_idx+1] with our new else block.
new_block = '''        report += "⚠️ Skill获取失败，降级到纯爬虫模式\\n"
        try:
            from kkxx_generate import fetch_news as fallback_fetch
            old_news = fallback_fetch()
            if old_news:
                cards = make_cards([{"title": n["title"], "url": n["link"], "source": n["source"]} for n in old_news])
            else:
                old_news = []
                cards = ""
            html = HTML_TEMPLATE.replace('{title}', "每日新闻 · " + date_cn).replace('{date_cn}', date_cn).replace('{cards}', cards)
            with open(f"blog/news-{date_str}.html", "w", encoding="utf-8") as f:
                f.write(html)
            report += f"✅ 降级模式: {len(old_news)}条\\n"
            update_list("blog/news.html", f'<a class="post" href="news-{date_str}.html"><h3>📰 每日新闻 · {date_cn}</h3><div class="meta">全球热点 · {len(old_news)}条</div></a>')
        except Exception as e:
            report += f"⚠️ 降级报错: {e}\\n"
            send_alert("每日新闻", f"降级异常: {e}")
'''

# Note: the indentation level of the original else block is 8 spaces (two tabs? Actually, we see 8 spaces in the file for the line "        report += ...")
# We'll keep the same indentation for the new block.

# Replace the lines
lines[start_idx:end_idx+1] = [new_block]

# Write the file
with open('update_news.py', 'w') as f:
    f.writelines(lines)

print("Fixed the else block.")
