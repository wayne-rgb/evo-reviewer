# 语言适配与扫描指南

## 扫描五类模式

### A — 资源泄漏
timer/interval/listener/fd/goroutine 被创建后未清理。
- TypeScript：`setInterval` 无 `clearInterval`；`EventEmitter.on` 无 `removeListener`
- Go：goroutine 无退出机制；`time.NewTicker` 无 `.Stop()`
- Swift：`Timer.scheduledTimer` 无 `.invalidate()`；`addObserver` token 未存储

### B — 标记锁未重置
flag/lock/isLoading 在异常路径未重置，导致状态永久卡死。

### C — 错误吞没
catch 块只 log 不传播、空 catch、`try?` 丢弃错误。

### D — 并发安全
共享状态无保护，多协程/线程/设备并发写同一资源。

### E — 安全边界
只测正常输入，未测超大/畸形/恶意输入。路径遍历、注入风险。

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

### 通用
- 设计决策类问题（如用 .result 状态表达错误而非新增 .error 状态）不是 bug
- 单例不需要 deinit/destroy — 生命周期 = 进程/App 生命周期

---

## 五类盲区 → 对应基础设施

| 盲区 | 应建基础设施 |
|------|------------|
| 只测状态不测资源 | 全局 afterEach 资源泄漏检测器 |
| Mock 只走 happy path | 故障注入 helper + 错误路径测试集 |
| 只测保护不测保护失效 | "故障后可用性"测试模式 |
| 缺少安全边界 | 接口边界测试模板 |
| 只验结果不验后续 | 故障后继续操作的断言模式 |

## 资源泄漏检测方式（按语言）

| 语言 | 检测方式 |
|------|---------|
| TypeScript/Node | monkey-patch + afterEach |
| Go | goleak / NumGoroutine 对比 |
| Swift | 弱引用 / deinit 检测 |
| Python | weakref + gc.collect |
