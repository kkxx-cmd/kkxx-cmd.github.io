## run_cron.sh 脚本说明

run_cron.sh 是一个用于在cron环境中运行Python脚本的包装器，具有以下特点：

### 功能特性
1. **自动重试机制**：如果第一次运行失败，会在指定延迟后重试一次
2. **Telegram通知**：运行结果会通过Telegram机器人发送通知
3. **日志记录**：完整的运行输出会被保存到日志文件
4. **环境适配**：自动查找Telegram Bot Token（从环境变量或OpenClaw配置文件中）

### 使用方法
```bash
run_cron.sh <task_name> <python_script> [retry_delay_seconds]
```

### 参数说明
- `<task_name>`：任务名称，用于日志和通知中标识
- `<python_script>`：要执行的Python脚本路径
- `[retry_delay_seconds]`：重试延迟时间（秒），默认为300秒（5分钟）

### 工作流程
1. 切换到仓库根目录（/home/qgg/.openclaw/workspace/repo）
2. 尝试发现Telegram Bot Token（优先从环境变量，然后从OpenClaw配置文件中查找）
3. 执行Python脚本并捕获输出
4. 如果成功（退出码0）：
   - 通过Telegram发送成功通知
   - 退出
5. 如果失败：
   - 发送失败通知并等待指定延迟时间
   - 重试一次
   - 如果第二次也失败，发送严重错误通知并退出

### 在kkxx-cmd/kkxx-cmd.github.io中的用途
此脚本设计用于在OpenClaw环境中定期运行内容更新脚本（如kkxx_generate.py），确保即使网络临时问题也能通过重试机制成功完成更新。
