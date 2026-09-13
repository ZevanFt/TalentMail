# TalentMail 开放平台开发者指南

> 面向要接入自动化接口的开发者。API 细节见 [API Reference](./api-reference.md)。

## 1. 五分钟接入

1. 登录 Web UI → **设置 → API Keys**
2. 创建 Key，勾选需要的 scope（最小权限）
3. 安全保存明文 Key（只显示一次）
4. 用 SDK 或 curl 调用

推荐 scopes：

| 场景 | Scopes |
|------|--------|
| 只收验证码 | `temp_mailbox:create` + `temp_code:read` |
| 读完整邮件 | 再加 `temp_email:read` + `temp_mailbox:read` |
| 长任务续期 | 再加 `temp_mailbox:extend` / `temp_mailbox:restore` |

## 2. SDK

仓库内提供轻量客户端，零业务依赖：

| 语言 | 路径 |
|------|------|
| Python | `sdk/python/talentmail_client.py` |
| Node.js 18+ | `sdk/node/talentmail-client.mjs` |
| Bash/curl | `sdk/examples/ci_wait_code.sh` |

### Python 最小示例

```python
from talentmail_client import TalentMailClient

client = TalentMailClient(
    base_url="https://mail.example.com/api",
    api_key="tm_xxx",
)
mailbox = client.create_temp_mailbox(prefix="e2e", purpose="signup")
code = client.wait_for_code(mailbox["id"], timeout=60)
print(mailbox["email"], code)
```

### Node 最小示例

```js
import { TalentMailClient } from './talentmail-client.mjs';

const client = new TalentMailClient({
  baseUrl: 'https://mail.example.com/api',
  apiKey: process.env.TALENTMAIL_API_KEY,
});
const mailbox = await client.createTempMailbox({ prefix: 'e2e' });
const code = await client.waitForCode(mailbox.id, { timeoutMs: 60000 });
console.log(mailbox.email, code);
```

## 3. 典型流水线

```
create mailbox
    → 把 email 填进第三方注册
    → 轮询 codes/latest
    → 提交验证码
    → (可选) 删/不管，等自动过期
```

注意：

- 轮询建议 **3s 间隔**，不要打满限流
- 创建时带 `Idempotency-Key`，CI 重跑不会重复建邮箱
- 邮箱默认 24h 过期，10 天内可 `restore`

## 4. 限流策略（场景分层）

两层限流叠加，**先撞到哪层算哪层**：

| 层 | 规则 |
|----|------|
| API Key 全局 | 按 Key 配置，默认 120 req/min |
| 场景限流 | 创建 10/min · 列表/读信 60/min · 验证码 30/min · 续期/恢复 20/min |

被限流返回 `429`，退避后重试。生产 CI 建议：

```python
# 伪代码
for attempt in range(5):
    try:
        return call_api()
    except TalentMailError as e:
        if e.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        raise
```

## 5. 错误处理约定

| 状态码 | 含义 | 处理 |
|--------|------|------|
| 401 | Key 无效/过期/撤销 | 换 Key |
| 403 | Scope 不足或套餐限制 | 检查 Key scope / 联系管理员 |
| 404 | 邮箱不存在或不属于你 | 不要重试 |
| 429 | 限流 | 指数退避 |
| 400 | 参数/状态错误 | 打日志，修调用 |

## 6. 安全建议

- Key 只放环境变量 / Secret Manager，不要进仓库
- Key 按环境拆分（dev / staging / prod）
- 定期在 UI 里看 **Audit Logs**，发现异常 IP 及时吊销
- 用最小 scope，不要全选

## 7. 本地自测

```bash
export TALENTMAIL_BASE_URL=http://localhost:8000/api
export TALENTMAIL_API_KEY=tm_xxx

# Bash
./sdk/examples/ci_wait_code.sh demo-prefix 60

# Python
python sdk/examples/python_signup_flow.py

# Node
node sdk/examples/node_signup_flow.mjs
```

## 8. 相关文档

- [完整 API Reference](./api-reference.md)
- [OpenAPI Schema](/docs)（服务启动后 `/docs`）
- [Automation 功能说明](./automation.md)
