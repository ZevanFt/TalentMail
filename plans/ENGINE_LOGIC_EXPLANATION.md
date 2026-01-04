# 引擎核心逻辑深度解析：条件与变量 (Engine Logic Deep Dive)

## 问题一：工作流中的条件（If/Else）是引擎写好的吗？

**答案：是的，但是是通用的。**

引擎不会预先写好“如果用户是VIP”这种具体业务代码。引擎里写好的是**数学和逻辑操作符**。

### 1. 引擎内部已经写好的代码 (The Operators)
引擎里有一个 `ConditionEvaluator` 类，它就像一个阅卷老师，只会打钩或打叉。它认识以下操作：

```python
# 这是写死在引擎里的基础能力
OPERATORS = {
    "equals": lambda a, b: a == b,
    "not_equals": lambda a, b: a != b,
    "contains": lambda a, b: b in a,
    "greater_than": lambda a, b: float(a) > float(b),
    "is_empty": lambda a, _: not a,
    # ... 共约 15 种基础判断
}
```

### 2. 您在前端配置的数据 (The Configuration)
当您在界面上拖拽一个“判断节点”时，生成的 JSON 是这样的：

```json
{
  "type": "condition_node",
  "config": {
    "left": "{{trigger.user.vip_level}}",  // 动态变量
    "operator": "greater_than",            // 选择的操作符
    "right": "1"                           // 对比的值
  }
}
```

### 3. 运行时的结合 (The Execution)
当引擎跑到这一步时，它做三件事：
1.  **取左边**：把 `{{trigger.user.vip_level}}` 变成数字 `2` (假设)。
2.  **取右边**：把 `"1"` 变成数字 `1`。
3.  **调函数**：`OPERATORS["greater_than"](2, 1)` -> 结果为 `True`。

**结论**：您不需要在后端写业务代码，只需要在前端**选操作符**。

---

## 问题二：自定义变量不好读取？自动回复怎么搞？

这是一个非常棒的问题。所谓的“自定义变量”，在工作流里其实就是**上游节点的输出结果**。

### 场景演示：自动回复 (Auto-Reply)

假设流程是：`收到邮件` -> `自动提取订单号(自定义变量)` -> `自动回复`

#### 第一步：触发 (Context 初始化)
```python
context = {
    "trigger": {
        "from": "user@gmail.com",
        "subject": "关于订单 ORDER-999 的投诉",
        "body": "我的货坏了..."
    }
}
```

#### 第二步：中间节点生成“自定义变量”
假设您加了一个“正则提取”节点（这是一个功能节点）。
*   配置：从 `{{trigger.subject}}` 提取 `ORDER-\d+`
*   **执行后，Context 变大了**：
```python
context = {
    "trigger": { ... },
    "steps": {
        "node_regex_1": {
            "match_result": "ORDER-999",  # <--- 这就是在这个流程中诞生的“自定义变量”！
            "found": True
        }
    }
}
```

#### 第三步：自动回复 (引用变量)
现在到了发邮件节点。
*   **收件人**：填 `{{trigger.from}}` (引擎能读到)
*   **邮件内容**：
    > "亲，我们收到了关于 **{{steps.node_regex_1.match_result}}** 的反馈。"

**后端怎么读这个难读的变量？**
其实对后端来说，读取 `trigger.from` 和读取 `steps.node_regex_1.match_result` **没有任何区别**！都是在字典里根据路径查值。

*   `context["trigger"]["from"]` -> 拿到发件人
*   `context["steps"]["node_regex_1"]["match_result"]` -> 拿到刚才生成的订单号

### 总结：什么是“自定义变量”？

在我们的系统里，**不存在**像写代码那样随意声明的 `var x = 1`。
所有的变量都必须有**出处**：
1.  **系统给的** (触发器数据)
2.  **节点产出的** (比如“计算节点”、“HTTP请求节点”的结果)

只要节点跑完了，它的结果就存在 `Context` 里，后面的节点（自动回复）就可以通过路径去引用它。

---

## 下一步建议

既然您担心这些逻辑，我建议我们的开发顺序是：

1.  **先不碰复杂的数据库**。
2.  在 `Code` 模式下，写一个纯 Python 的 `test_engine_logic.py`。
3.  在这个文件里，我不连数据库，直接手动造一个假 `Context` 数据，然后模拟跑一下 `Condition` 和 `VariableResolver`。
4.  **把运行结果打印出来给您看**。

这样您就能亲眼看到：
*   它是怎么把 `{{...}}` 变成真实值的。
*   它是怎么判断 `True/False` 的。

您觉得先做一个这样的**纯逻辑验证脚本**，是不是更稳妥？