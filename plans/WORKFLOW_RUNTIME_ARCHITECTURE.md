# Core: 工作流引擎运行时原理解析 (Runtime Architecture)

您最担心的问题是：**"前端的图在后端怎么跑？变量的值从哪来？"**

答案在于三个核心概念：**执行上下文 (Context)**、**解释器 (Runner)** 和 **动态解析 (Resolver)**。

---

## 1. 数据的载体：上下文 (Context)

想象一下，工作流执行时，内存里有一个巨大的字典对象 `context`。它就像一个购物篮，随着工作流的每一步执行，里面装的东西越来越多。

**结构示例：**
```python
# 这是一个正在运行中的工作流的 Context
context = {
    # 1. 触发器带来的初始数据 (这是源头！)
    "trigger": {
        "event": "user_registered",
        "data": {
            "user_id": 101,
            "email": "zhangsan@example.com",
            "name": "张三",
            "ip": "192.168.1.1"
        }
    },
    
    # 2. 全局变量 (来自数据库)
    "global": {
        "company_name": "TalentMail Inc.",
        "support_email": "help@talentmail.com"
    },
    
    # 3. 步骤执行结果 (由引擎自动填充)
    "steps": {
        "node_generate_coupon": {  # 假设第一个节点是生成优惠券
            "coupon_code": "WELCOME2024",
            "expires_in": "7d"
        },
        # 还没执行到的节点在这里是空的
    }
}
```

---

## 2. 动力的来源：解释器 (Runner)

后端不需要为每个工作流生成代码。我们只有一个通用的 `WorkflowEngine` 类，它就是那个“演奏家”。

**伪代码逻辑：**

```python
class WorkflowEngine:
    async def run(self, workflow_json, trigger_data):
        # 1. 初始化购物篮
        context = {
            "trigger": trigger_data,
            "steps": {}
        }
        
        # 2. 找到开始节点
        current_node = self.find_start_node(workflow_json)
        
        # 3. 死循环执行，直到没有下一个节点
        while current_node:
            print(f"正在执行节点: {current_node.type}")
            
            # --- 关键点：执行前的参数准备 ---
            # 这一步解决了"变量发出去的时候值是什么"的问题
            # 引擎会把配置里的 "{{trigger.data.email}}" 翻译成 "zhangsan@example.com"
            resolved_params = self.resolve_parameters(current_node.config, context)
            
            # 4. 真正干活 (调用具体的 Service)
            try:
                result = await self.execute_node_logic(current_node.type, resolved_params)
                
                # 5. 把结果放进购物篮，供后面的节点使用
                context["steps"][current_node.id] = result
                
                # 6. 找下一站
                current_node = self.find_next_node(workflow_json, current_node)
                
            except Exception as e:
                self.log_error(e)
                break
```

---

## 3. 魔法的桥梁：变量解析器 (Resolver)

这就是您问的：**“邮件中变量值是什么？”** 的答案。

在前端配置里，您存的是一个**路径字符串**，比如 `{{trigger.data.email}}`。
在后端执行时，`resolve_parameters` 函数会做置换。

**代码演示：**

```python
# 假设这是刚才那个“发送邮件”节点的配置 (node.config)
node_config = {
    "template_code": "welcome_email",
    "target_email": "{{trigger.data.email}}",  # <--- 注意这里是字符串
    "variables": {
        "user_name": "{{trigger.data.name}}",
        "my_coupon": "{{steps.node_generate_coupon.coupon_code}}"
    }
}

def resolve_variable(value_str, context):
    # 如果是 {{...}} 格式，就去 Context 里找值
    if value_str.startswith("{{") and value_str.endswith("}}"):
        path = value_str[2:-2].strip() # 拿到 "trigger.data.email"
        
        # 这是一个辅助函数，顺着点号一层层取字典的值
        # context["trigger"]["data"]["email"] -> "zhangsan@example.com"
        return get_value_from_path(context, path)
        
    return value_str # 如果不是变量，就原样返回 (比如静态写的标题)

# 执行结果：
# {
#     "template_code": "welcome_email",
#     "target_email": "zhangsan@example.com",
#     "variables": {
#        "user_name": "张三",
#        "my_coupon": "WELCOME2024"
#     }
# }
```

---

## 4. 最终回环：邮件服务调用

一旦变量被解析成真实值，Engine 就会调用大家熟悉的 `MailService`：

```python
# 此时所有值都已经是真实的字符串了，不再是 {{...}}
await mail_service.send_template_email(
    to="zhangsan@example.com",
    template_code="welcome_email",
    template_data={
        "user_name": "张三",
        "my_coupon": "WELCOME2024"
    }
)
```

## 5. 总结

1.  **触发阶段**：事件发生，产生原始数据（种子）。
2.  **流动阶段**：数据被放入 `Context` 容器。
3.  **解析阶段**：每个节点执行前，引擎看着它的配置，把 `{{...}}` 里的占位符换成 `Context` 里的真实值。
4.  **执行阶段**：带着真实值去调用具体的 Python 函数（发邮件、数据库操作等）。

这就是为什么我们在设计时强调 **Schema** 的原因 —— 只有前端明确知道后端 `Context` 里会有什么（Trigger 会提供什么，上一步会输出什么），前端才能生成正确的下拉菜单，让您去“连线”或“选择变量”。