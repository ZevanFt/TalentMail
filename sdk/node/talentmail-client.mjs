/**
 * TalentMail Open API 轻量客户端 (Node.js 18+)
 *
 * 用法:
 *   import { TalentMailClient } from './talentmail-client.mjs';
 *   const client = new TalentMailClient({ baseUrl: 'https://mail.example.com/api', apiKey: 'tm_xxx' });
 *   const mailbox = await client.createTempMailbox({ prefix: 'e2e' });
 *   const code = await client.waitForCode(mailbox.id, { timeoutMs: 60000 });
 */

export class TalentMailError extends Error {
  constructor(statusCode, detail) {
    super(`[${statusCode}] ${detail}`);
    this.name = 'TalentMailError';
    this.statusCode = statusCode;
    this.detail = detail;
  }
}

export class TalentMailClient {
  constructor({ baseUrl, apiKey, timeoutMs = 15000 }) {
    if (!baseUrl || !apiKey) {
      throw new Error('baseUrl and apiKey are required');
    }
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
    this.timeoutMs = timeoutMs;
  }

  async #request(method, path, { body, query, idempotencyKey } = {}) {
    const url = new URL(this.baseUrl + path);
    if (query) {
      for (const [k, v] of Object.entries(query)) {
        if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
      }
    }
    const headers = {
      Authorization: `Bearer ${this.apiKey}`,
      Accept: 'application/json',
    };
    if (body) headers['Content-Type'] = 'application/json';
    if (idempotencyKey) headers['Idempotency-Key'] = idempotencyKey;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const resp = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });
      if (!resp.ok) {
        let detail = await resp.text();
        try {
          detail = JSON.parse(detail).detail ?? detail;
        } catch {
          /* keep text */
        }
        throw new TalentMailError(resp.status, String(detail));
      }
      if (resp.status === 204) return null;
      const text = await resp.text();
      return text ? JSON.parse(text) : null;
    } finally {
      clearTimeout(timer);
    }
  }

  createTempMailbox({ prefix, purpose, autoVerifyCodes = true, idempotencyKey } = {}) {
    return this.#request('POST', '/automation/temp-mailboxes', {
      body: {
        auto_verify_codes: autoVerifyCodes,
        ...(prefix ? { prefix } : {}),
        ...(purpose ? { purpose } : {}),
      },
      idempotencyKey,
    });
  }

  listTempMailboxes({ includePurged = false } = {}) {
    return this.#request('GET', '/automation/temp-mailboxes', {
      query: { include_purged: includePurged },
    });
  }

  getEmails(mailboxId, { includeBody = false, page = 1, limit = 20 } = {}) {
    return this.#request('GET', `/automation/temp-mailboxes/${mailboxId}/emails`, {
      query: { include_body: includeBody, page, limit },
    });
  }

  getLatestCode(mailboxId, {
    withinMinutes = 5,
    senderContains,
    subjectContains,
    unreadOnly = false,
  } = {}) {
    return this.#request('GET', `/automation/temp-mailboxes/${mailboxId}/codes/latest`, {
      query: {
        within_minutes: withinMinutes,
        unread_only: unreadOnly,
        ...(senderContains ? { sender_contains: senderContains } : {}),
        ...(subjectContains ? { subject_contains: subjectContains } : {}),
      },
    });
  }

  async waitForCode(mailboxId, { timeoutMs = 60000, intervalMs = 3000, withinMinutes = 5, ...filters } = {}) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const result = await this.getLatestCode(mailboxId, { withinMinutes, ...filters });
      if (result?.code) return result.code;
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    throw new TimeoutError(`在 ${timeoutMs}ms 内未获取到验证码 (mailbox_id=${mailboxId})`);
  }

  extendMailbox(mailboxId, { hours = 24 } = {}) {
    return this.#request('POST', `/automation/temp-mailboxes/${mailboxId}/extend`, {
      body: { hours },
    });
  }

  restoreMailbox(mailboxId) {
    return this.#request('POST', `/automation/temp-mailboxes/${mailboxId}/restore`);
  }
}

class TimeoutError extends Error {
  constructor(message) {
    super(message);
    this.name = 'TimeoutError';
  }
}
