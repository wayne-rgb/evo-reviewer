# 业务流追踪指南

## 业务流推导方法

### 每次 /review 执行时
1. `test-governance/config.yaml` 的 `cross_module.business_flows` — bootstrap 已预计算的业务流清单
2. `git diff --name-only HEAD~5` — 近期改动，用于筛选受影响的业务流子集

### Bootstrap 时推导业务流（首次或 config.yaml 无 cross_module 段时）
1. `test-governance/p0-cases.tsv` — 已定义的 P0 场景，按功能域聚合为业务流
2. 项目 CLAUDE.md 的通信拓扑图 — 模块间连接关系
3. `test-governance/config.yaml` — 模块列表和语言信息

### 从 P0 场景到业务流（bootstrap 阶段）
p0-cases.tsv 每行是一个 P0 场景，格式：`case_id\tkeyword\tsearch_scope`。
将相关 P0 场景聚合为业务流：
- 同一功能域的多个 P0 场景 → 1 条业务流
- 例：PAIRING_KEY_NIL_CLEARS_LOCAL + MAC_SET_KEY_IOS_SHOWS_CONFIGURED → "API Key 跨端同步流"

### 从通信拓扑到交界点
读取项目 CLAUDE.md 中的通信拓扑（搜索 ASCII 图、"通信"/"拓扑"/"架构"关键词），提取模块间的通信协议：
- WebSocket 连接 → 消息格式契约
- HTTP API → 请求/响应格式契约
- 共享类型文件 → 枚举/状态机契约

### 从近期 commit 筛选受影响流（每次 review）
1. `git diff --name-only HEAD~5` 获取改动文件列表
2. 归属到模块（按 config.yaml 的 src_dir）
3. 改动涉及的模块 ∩ 业务流涉及的模块 → 受影响的业务流
4. 如果改动了 `cross_module.shared_types` 中的文件 → 所有消费该类型的业务流也加入

---

## 交界检查清单（F1-F4）

### F1 — 消息格式对齐
在发送端找到消息构造代码，在接收端找到消息解析代码，逐字段比对：
- 字段名拼写（camelCase vs snake_case 转换是否正确）
- 字段类型（string vs number、optional vs required）
- 新增字段是否两端都已处理
- 枚举值是否完全一致（不是子集）

**语言特定提取方式**：
- TypeScript：搜 `type:` 或 `action:` 字面量、interface 定义
- Swift：搜 `CodingKeys`、`Codable` struct、`case` 枚举
- Go：搜 `json:"xxx"` struct tag
- Rust：搜 `#[serde(rename)]`、`Serialize`/`Deserialize` derive

### F2 — 状态机一致
找到所有维护状态机的端（通常是后端定义、前端消费），比对：
- 状态枚举值集合是否一致
- 允许的转换路径是否一致
- 终态判断逻辑是否一致

### F3 — 失败处理
在交界的每一跳检查：
- 发送失败：是否有重试/通知/降级？
- 超时：是否有超时机制？超时后的状态是什么？
- 部分成功：广播给 3 个客户端，1 个失败，其余 2 个是否不受影响？

### F4 — 时序假设
检查隐含的时序依赖：
- A 模块假设 B 已初始化完成 → B 延迟启动时会怎样？
- A 发送消息后立即读取 B 的状态 → 如果 B 异步处理，状态可能还是旧的
- 重连后是否获取最新状态，还是沿用断连前的缓存？

---

## 单模块退化

如果项目只有 1 个模块（config.yaml 的 modules 只有 1 个），无跨模块交界：
- 退化为代码模式扫描（A-E 同步检查作为主要产出）
- 重点关注对外接口的输入校验和错误处理
- 仍需满足"用户可感知影响"的过滤条件

---

## 同步检查（A-E，沿业务流路径顺带扫描）

追踪业务流时，流经每个模块的代码路径上顺带检查以下模式。**过滤条件**：必须能描述出用户可感知的影响，纯理论风险不报。

### A — 资源泄漏
timer/interval/listener/fd/goroutine 被创建后未清理。

### B — 标记锁未重置
flag/lock/isLoading 在异常路径未重置。

### C — 错误吞没
catch 块只 log 不传播、空 catch、try? 丢弃错误。

### D — 并发安全
共享状态无保护，多协程/线程/设备并发写同一资源。

### E — 安全边界
只测正常输入，未测超大/畸形/恶意输入。

---

## 语言运行时排除规则（必读）

以下模式**不是 bug**，禁止报告：

### Node.js / TypeScript
- 两个同步检查间的"竞态" — Node.js 单线程事件循环，同步代码不会被打断
- setTimeout 链式调度的"并发回调" — 完成后才注册下一个，不是 setInterval
- `if (this.x) return` 后的 TOCTOU — 除非两个检查间有 `await` 让出控制权
- cleanup() 调用 clearTimeout 后的"timer 泄漏" — clearTimeout 会取消未执行的回调

### Swift
- @MainActor 类内 `Task {}` 访问 self 属性 — Task 继承 @MainActor 隔离，串行执行
- @MainActor 类内 @Published 属性赋值 — 已在主线程，不存在"后台线程更新 UI"问题
- 单例的 NWPathMonitor/Timer 不调用 stop — App 退出时 OS 清理，单例生命周期 = App 生命周期
- `Task { @MainActor in }` 内部闭包共享局部变量 — @MainActor 保证串行

### Go
- sync.Mutex 已保护的代码段 — 不要报告"竞态"
- defer unlock — 不要报告"锁未释放"
- context.WithCancel 后的 defer cancel — 这是标准模式

### Rust
- 所有权系统保证的内存安全 — 不报告 use-after-free
- Drop trait 自动清理 — 不报告未显式 close（除非外部资源如网络连接）

### 通用
- 设计决策类问题（如用 .result 状态表达错误而非新增 .error 状态）不是 bug
- 单例不需要 deinit/destroy — 生命周期 = 进程/App 生命周期
