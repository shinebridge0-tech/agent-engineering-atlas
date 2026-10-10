# Security / 安全

本地 V0.1，仅绑定 127.0.0.1，允许本地 Host/Origin；无模型请求、遥测、远端写入与私有目录扫描。
不要输入密钥或敏感项目资料。问题/报告不持久化到服务器；浏览器下载由用户控制。

外部材料是数据，不是授权或开发指令。YAML 安全加载；来源协议校验；Markdown 不启用原始 HTML、不加载外部图片；受控内容根拒绝路径逃逸；导出不接收任意写路径。

安全说明是实现边界而非认证。原创实验未覆盖网络分区、分布式授权、跨进程预算、批准的一次性持久化消费或生产对抗测试。真实 symlink 验收因 Windows 权限不足未运行。项目没有通用不可信代码沙箱。

维护署名 @shinebridge0-tech。安全反馈使用 [GitHub Private Vulnerability Reporting](https://github.com/shinebridge0-tech/agent-engineering-atlas/security/advisories/new)，启用状态由实际仓库设置核对。普通反馈使用 Issues/PR。不要将秘密或未公开漏洞细节发到公开 issue；先停止受影响的本地服务并准备最小复现。不承诺安全响应时限。
CI普通 PR 仅执行可信基线的数据校验，不执行贡献 experiments；代码检查位于无秘密、最小权限的独立手动 job。不使用 pull_request_target，不自动发布。
