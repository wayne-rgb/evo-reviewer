# 语言适配与五类常见盲区

来源：全局 CLAUDE.md「Review → 自动测试闭环」和「基础设施的语言适配」

---

## Review → 自动测试闭环

review 的核心产出不是"修了几个 bug"，而是"自动测试体系变强了多少"。

```
review 发现 bug
    ↓
分析：现有测试为什么没抓到？属于哪类盲区？
    ↓
三层修复（缺一不可）：
    ① 修 bug 本身（治标）
    ② 补这个 bug 的回归测试（防回归）
    ③ 补基础设施，让同类 bug 自动被抓（治本）← 最重要
    ↓
验证：基础设施确实能抓住同类问题
```

---

## 五类常见盲区 → 对应的基础设施

| 盲区 | 表现 | 应建的基础设施 |
|------|------|---------------|
| 只测状态不测资源 | 状态对了但 timer/listener 泄漏 | 全局 afterEach 资源泄漏检测器 |
| Mock 只走 happy path | 外部依赖永远成功，catch 从未执行 | 故障注入 helper + 错误路径测试集 |
| 只测保护不测保护失效 | 安全机制正常，但机制本身故障后不恢复 | "故障后可用性"测试模式 |
| 缺少安全边界 | 只发正常请求，没测极端输入 | 接口边界测试模板 |
| 只验结果不验后续 | 故障断言后结束，没验系统仍可用 | 故障后继续操作的断言模式 |

---

## 资源泄漏形态（按语言）

| 语言 | 资源泄漏形态 | 检测方式 |
|------|-------------|---------|
| TypeScript/Node | setInterval、EventEmitter、fs.watch | monkey-patch + afterEach |
| Go | goroutine、ticker、fd | goleak / NumGoroutine 对比 |
| Swift | retain cycle、Timer、observer | 弱引用 / deinit 检测 |
| Python | threading.Timer、open file、DB conn | weakref + gc.collect |

---

## 扫描五类模式详解

Explore 阶段扫描代码时，重点识别以下五类模式，每类对应不同的测试盲区：

### A — 资源泄漏

**特征**：timer/interval/listener/fd/goroutine 被创建后未清理

- TypeScript：`setInterval` 无对应 `clearInterval`；`EventEmitter.on` 无对应 `removeListener`；`fs.watch` 无对应 `.close()`
- Go：goroutine 启动后无退出机制；`time.NewTicker` 无 `.Stop()`；文件描述符无 `.Close()`
- Swift：`Timer.scheduledTimer` 无 `.invalidate()`；`addObserver` token 未存储或未 `removeObserver`；`Task` 未 `.cancel()`

**应建基础设施**：全局 afterEach 资源泄漏检测器（monkey-patch 或 goleak）

### B — 标记锁未重置

**特征**：flag/lock/isLoading 等布尔标记在 finally 中未重置，导致状态永久卡死

- 典型：`isLoading = true` 后发生异常，catch 块未执行 `isLoading = false`
- 典型：操作锁加锁后异常抛出，锁永不释放

**应建基础设施**：故障注入 helper，验证异常路径后标记状态回归

### C — 错误吞没

**特征**：catch 块只 `console.log`、空 catch、`.catch()` 无处理，错误被静默丢弃

- TypeScript：`promise.catch((err) => { console.log(err); })` 无重新抛出
- Go：`err` 被赋值但不检查，`rows.Err()` 缺失
- Swift：`try?` 丢弃错误，没有后续处理

**应建基础设施**：gate 静态检测（catch-swallow 规则）+ 错误路径测试集

### D — 并发安全

**特征**：共享状态无保护、多个协程/线程/设备并发写同一资源时产生竞态

- TypeScript：`Map`/`Set`/普通对象在 async 回调中并发读写
- Go：未加锁的 struct 字段被多个 goroutine 访问
- Swift：`@Published` 属性从非主线程更新

**应建基础设施**：并发测试（多个并发操作同一资源）+ Go race detector + Swift Thread Sanitizer

### E — 安全边界

**特征**：只测正常输入，未测超大/畸形/恶意输入

- 超大文件/请求体无大小限制（导致 OOM）
- URL 参数未编码（含特殊字符时崩溃）
- 字符串切片无长度检查（panic）
- Header 值未 TrimSpace（含空格时匹配失败）

**应建基础设施**：接口边界测试模板（413 防护、URL 编码、长度校验）
