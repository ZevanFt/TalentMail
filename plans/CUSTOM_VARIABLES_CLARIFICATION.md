# 终极解答：自定义变量存在哪？怎么读？(Custom Variables Solutions)

您问得非常精准：**“如果数据库里没有这个字段，Trigger 也没送过来，我想自定义一个变量，它到底在哪？怎么读？”**

这有三种实现方案，我会为您分析每一种，看看哪种符合您的直觉。

## 方案 A：临时变量节点 (Set Variable Node) —— 最灵活，最常见

这是目前主流工作流（如 n8n, Zapier）的做法。

*   **怎么定义？**
    用户拖入一个叫“设置变量 (Set Variable)”的节点。
    在配置里写：`变量名: my_custom_status`, `值: "VIP_PENDING"`。
*   **它在哪？**
    它不存数据库表结构里，它**临时存活在这次工作流运行的内存 Context 里**。
*   **怎么读？**
    后续节点用 `{{steps.set_variable_node_1.my_custom_status}}` 读取。
*   **对应数据库吗？**
    **不对应**。它只是这次运行过程中的一个临时记号。跑完就没了。

## 方案 B：扩展用户属性 (User Metadata) —— 持久化存储

如果您定义的变量是想**长期保存**的（比如“给用户打个分”，下次发邮件还要用），那就不能只存在内存里了。

*   **怎么定义？**
    我们在 `users` 表里加一个 `metadata (JSON)` 字段。
*   **怎么写？**
    拖入一个“更新用户属性 (Update User)”节点。
    配置：`Key: "customer_score"`, `Value: 100`。
    **引擎会真的去执行 SQL**：`UPDATE users SET metadata = metadata || '{"customer_score": 100}' ...`
*   **怎么读？**
    下一次触发时，Trigger 会把用户最新的 `metadata` 全读出来。
    您用 `{{trigger.user.metadata.customer_score}}` 就能读到上次存的值。

## 方案 C：手动查询数据库 (Query Database) —— 这种最硬核

如果这个变量在别的表里（比如在 `orders` 表里），Trigger 没带过来。

*   **怎么定义？**
    也就是“我想查个值”。
*   **怎么做？**
    拖入一个“查询记录 (Query Record)”节点。
    SQL/配置：`SELECT status FROM orders WHERE user_id = {{trigger.user.id}}`
*   **怎么读？**
    后续节点用 `{{steps.query_node_1.result.status}}` 读取。

---

## 针对您的问题的直接回答

> **“这个自定义的话就没法读取把？！”**

如果您不做上述 A/B/C 的任何操作，直接在邮件里写 `{{my_ghost_var}}`，那是真的**读不到**（因为不存在）。

**变量必须“被生产”出来，才能“被消费”。**

*   如果是**临时逻辑**（比如判断分支用的旗标），用 **方案 A**。
*   如果是**业务数据**（比如用户积分、等级），必须用 **方案 B** 或 **方案 C**，让它和数据库发生关系。

## 我们的系统怎么做？

我建议**同时支持 A 和 B**：

1.  **短期记忆**：提供 `Set Variable` 节点，方便做复杂的逻辑计算。
2.  **长期记忆**：提供 `Update User/Contact` 节点，把数据写回 `JSON` 字段，这样以后永远能读到。

这样是不是就清晰了？**变量要么在内存里传鼓（A），要么写进硬盘留底（B）。**