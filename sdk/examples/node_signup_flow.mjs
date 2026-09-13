#!/usr/bin/env node
/**
 * 完整 E2E：创建临时邮箱 → 等验证码。
 *
 * 环境变量:
 *   TALENTMAIL_BASE_URL  例如 https://mail.example.com/api
 *   TALENTMAIL_API_KEY   tm_xxx
 */
import { TalentMailClient } from '../node/talentmail-client.mjs';

const baseUrl = process.env.TALENTMAIL_BASE_URL || 'https://mail.example.com/api';
const apiKey = process.env.TALENTMAIL_API_KEY;
if (!apiKey) {
  console.error('请设置 TALENTMAIL_API_KEY');
  process.exit(1);
}

const client = new TalentMailClient({ baseUrl, apiKey });

try {
  const mailbox = await client.createTempMailbox({
    prefix: 'signup-demo',
    purpose: 'Node SDK demo',
    idempotencyKey: 'demo-node-signup-001',
  });
  console.log(`创建成功: ${mailbox.email} (id=${mailbox.id})`);

  // 在这里把 mailbox.email 填到第三方注册表单
  console.log('请用该邮箱完成第三方注册，等待验证码...');

  const code = await client.waitForCode(mailbox.id, {
    timeoutMs: 90000,
    intervalMs: 3000,
    withinMinutes: 5,
  });
  console.log(`验证码: ${code}`);
} catch (err) {
  console.error('失败:', err.message);
  process.exit(2);
}
