# KKXX 个人导航页

这是一个个人数字花园导航站点，集成了合肥本地资讯、全球每日新闻、A股量化分析等功能。

## 功能特点

- 📰 **合肥城事**：每日更新合肥本地新闻和资讯
- 🌍 **全球新闻**：汇集国内外重要新闻头条
- 📊 **A股分析**：提供股票市场数据和量化分析
- 🌱 **数字花园**：记录个人成长和学习笔记
- 🤖 **AI助手集成**：与OpenClaw AI助手协作内容生成和更新

## 项目结构

```
kkxx-cmd.github.io/
├── index.html          # 主页
├── garden.html         # 数字花园专区
├── blog.html           # 博客专区  
├── stock.html          # 股票专区
├── news.html           # 新闻专区
├── downloads/          # 下载资源
├── data/               # 数据文件
├── blog/               # 博客文章
├── garden/             # 数字花园每日更新
├── news/               # 新闻存档
├── stock/              # 股票数据存档
├── kkxx_generate.py    # 内容生成主脚本
├── update_*.py         # 各专区更新脚本
├── backfill_*.py       # 数据回填脚本
├── run_cron.sh         # Cron包装脚本
└── *.md                # 说明文档
```

## 内容更新机制

站点内容通过Python脚本自动更新：

1. **kkxx_generate.py** - 主生成脚本
   - 获取合肥新闻、股票数据等
   - 生成每日HTML页面
   - 提交更新到Git仓库
   - 通过Telegram发送更新通知

2. **更新脚本**
   - `update_garden.py` - 数字花园内容更新
   - `update_news.py` - 新闻内容更新
   - `update_stock.py` - 股票数据更新
   - `backfill_*.py` - 历史数据回填

## 自动更新设置

内容更新可以通过以下方式自动化：

### 使用系统Cron
```bash
# 每天早上6点更新内容
0 6 * * * /path/to/run_cron.sh "KKXX内容更新" "/path/to/kkxx_generate.py" 300
```

### 使用GitHub Actions（推荐）
在 `.github/workflows/content-update.yml` 中：
```yaml
name: 每日内容更新
on:
  schedule:
    - cron: '0 6 * * *'  # 每天早上6点
  workflow_dispatch:  # 允许手动触发

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: 安装依赖
      run: |
        python3 -m pip install akshare beautifulsoup4 lxml pandas
    - name: 运行更新脚本
      run: python3 kkxx_generate.py
    - name: 提交更改
      run: |
        git config user.name "github-actions[bot]"
        git config user.email "github-actions[bot]@users.noreply.github.com"
        git add .
        git commit -m "自动内容更新: $(date)" || echo "无更改需要提交"
        git push
```

## 数据来源

- 合肥新闻：通过网络爬虫获取本地新闻源
- 股票数据：使用AKShare库获取A股实时行情
- 全球新闻：整合多个新闻API或RSS源

## 本地开发

```bash
# 克隆仓库
git clone https://github.com/kkxx-cmd/kkxx-cmd.github.io.git
cd kkxx-cmd.github.io

# 安装依赖（推荐使用虚拟环境）
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # 如果存在requirements.txt

# 运行内容更新
python3 kkxx_generate.py
```

## 维护和贡献

此站点由KKXX个人维护，欢迎提出改进建议或报告问题。

### 常见维护任务

1. **更新内容脚本**：修改`kkxx_generate.py`或相应的update_*.py文件
2. **添加新数据源**：在适当的更新脚本中添加新的数据获取逻辑
3. **更新模板**：修改HTML模板以改变页面展示效果
4. **处理错误**：检查日志文件和Telegram通知以了解运行状态

## 许可证

此项目用于个人使用，欢迎 fork 和自定义使用。
