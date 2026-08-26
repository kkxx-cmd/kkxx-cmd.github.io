# 贡献指南

感谢您考虑为KKXX个人导航页做出贡献！以下是一些指导原则，帮助您顺利参与项目。

## 如何贡献

### 报告问题
- 在GitHub上使用[Issues](https://github.com/kkxx-cmd/kkxx-cmd.github.io/issues)功能报告问题
- 请提供清晰的描述、重现步骤和预期结果
- 如果是功能请求，请解释为什么这个功能会有用

### 提交代码更改
1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

### 开发流程
- 请确保您的代码符合现有的代码风格
- 添加相关的注释说明复杂逻辑
- 如果修改了Python脚本，请确保在本地测试后再提交
- 保持提交信息清晰且描述性强

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

## 编码标准
- Python代码请遵循PEP 8风格指南
- 有意义的变量和函数名称
- 适当的注释说明目的和用法
- 错误处理要完整且易于理解

## 问题和功能标签
我们使用以下标签来组织Issues：
- `bug`: 代表一个确定的错误或意外结果
- `enhancement`: 代表一个新功能或改进建议
- `documentation`: 代表需要改进或添加的文档
- `help wanted`: 表示维护者希望社区协助解决的Issue
- `good first issue`: 适合新手贡献者的Issue

## 行为准则
请注意本项目遵循[行为准则](CODE_OF_CONDUCT.md)。请在所有互动中保持友善和有建设性。

## 致谢
感谢所有已经为本项目做出贡献的人！

---
*此指南最后更新于：$(date '+%Y-%m-%d')*
