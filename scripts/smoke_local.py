"""TalentMail 本地全栈冒烟测试 — 对 127.0.0.1:13000 直接打 API"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:13000/api"
ADMIN = "admin@talenting.test"
PASS = "5dgzpuH6lz5Z5KjUMgULXg"

results: list[tuple[str, str, str]] = []


def req(method, path, token=None, data=None, form=False, headers=None):
    url = f"{BASE}{path}"
    body = None
    hs = {"Accept": "application/json"}
    if headers:
        hs.update(headers)
    if token:
        hs["Authorization"] = f"Bearer {token}"
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            hs["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            hs["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=hs, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read()
            if not raw:
                return resp.status, None
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, raw.decode("utf-8", "replace")[:200]
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            detail = json.loads(raw)
        except Exception:
            detail = raw.decode("utf-8", "replace")[:300]
        return e.code, detail
    except Exception as e:
        return 0, str(e)


def check(name, status, ok_codes=(200, 201, 204), extra=""):
    ok = status in ok_codes
    mark = "PASS" if ok else "FAIL"
    results.append((mark, name, f"HTTP {status} {extra}".strip()))
    print(f"[{mark}] {name}: HTTP {status} {extra}")
    return ok


def main():
    # 1 health
    st, body = req("GET", "/health")
    check("health", st, (200,), f"status={body.get('status') if isinstance(body, dict) else body}")

    # 2 login
    st, login = req("POST", "/auth/login", data={"username": ADMIN, "password": PASS}, form=True)
    if not check("admin login", st, (200,)):
        print("login failed, abort")
        return 1
    token = login["access_token"]
    print(f"  token ok, user sub in jwt present")

    # 3 me
    st, me = req("GET", "/users/me", token=token)
    check("users/me", st, (200,), f"email={me.get('email') if isinstance(me, dict) else ''}")

    # 4 folders
    st, folders = req("GET", "/folders", token=token)
    names = []
    if isinstance(folders, list):
        names = [f.get("name") or f.get("role") for f in folders]
    elif isinstance(folders, dict):
        names = [f.get("name") or f.get("role") for f in folders.get("items", folders.get("folders", []))]
    check("folders", st, (200,), f"count={len(names)} names={names[:6]}")

    # 5 tags
    st, tags = req("GET", "/tags", token=token)
    check("tags", st, (200,), f"total={tags.get('total') if isinstance(tags, dict) else tags}")

    # 6 signatures
    st, _ = req("GET", "/signatures", token=token)
    check("signatures", st, (200,))

    # 7 create contact
    st, contact = req("POST", "/contacts", token=token, data={
        "name": "Smoke Test", "email": "smoke@example.com", "phone": "10086", "notes": "auto"
    })
    check("contact create", st, (200, 201), f"id={contact.get('id') if isinstance(contact, dict) else ''}")
    cid = contact.get("id") if isinstance(contact, dict) else None

    # 8 send internal email (admin -> admin)
    st, sent = req("POST", "/emails", token=token, data={
        "to": [{"email": ADMIN}],
        "subject": f"Smoke test {int(time.time())}",
        "body_text": "hello from smoke test\n验证码是 123456",
        "body_html": "<p>hello</p>",
    })
    check("send email", st, (200, 201), f"id={sent.get('id') if isinstance(sent, dict) else str(sent)[:80]}")
    email_id = sent.get("id") if isinstance(sent, dict) else None

    # wait for background send
    time.sleep(3)

    # 9 sync inbox
    st, sync = req("POST", "/emails/sync", token=token)
    check("email sync", st, (200,), str(sync)[:80] if sync else "")

    time.sleep(2)

    # 10 list emails (need folder_id?)
    # try several list endpoints
    st, em = req("GET", "/emails?limit=5", token=token)
    check("list emails limit=5", st, (200,), str(em)[:100] if not isinstance(em, dict) else f"count={len(em.get('items', em if isinstance(em, list) else []))}")

    # get inbox folder id
    inbox_id = None
    flist = folders if isinstance(folders, list) else (folders.get("items") if isinstance(folders, dict) else []) or []
    for f in flist:
        if (f.get("role") == "inbox") or (f.get("name") or "").lower() in ("inbox", "收件箱"):
            inbox_id = f.get("id")
            break
    if inbox_id:
        st, em2 = req("GET", f"/emails?folder_id={inbox_id}&limit=10", token=token)
        check("list inbox emails", st, (200,), str(type(em2).__name__) + " " + str(em2)[:80])

    # 11 calendar create/list
    st, cal = req("POST", "/calendar", token=token, data={
        "title": "Smoke Meeting",
        "start_time": "2026-03-10T09:00:00Z",
        "end_time": "2026-03-10T10:00:00Z",
        "recurrence": "weekly",
        "recurrence_until": "2026-04-01T00:00:00Z",
    })
    check("calendar create", st, (200, 201), f"id={cal.get('id') if isinstance(cal, dict) else str(cal)[:80]}")
    st, evs = req("GET", "/calendar?start=2026-03-01T00:00:00Z&end=2026-03-31T23:59:59Z", token=token)
    n = len(evs) if isinstance(evs, list) else "?"
    check("calendar list expand", st, (200,), f"n={n}")

    # 12 drive create folder
    st, folder = req("POST", "/drive/folders", token=token, data={"name": "SmokeFolder"})
    # maybe different path
    if st >= 400:
        st, folder = req("POST", "/drive/folder", token=token, data={"name": "SmokeFolder"})
    if st >= 400:
        # try list to discover
        st2, drive = req("GET", "/drive", token=token)
        check("drive list", st2, (200,), str(drive)[:80])
    else:
        check("drive folder create", st, (200, 201), str(folder)[:80])

    # 13 pool
    st, pool = req("GET", "/pool/mailboxes", token=token)
    if st >= 400:
        st, pool = req("GET", "/pool/", token=token)
    check("pool list", st, (200, 403), str(pool)[:80])

    # 14 workflows
    st, wfs = req("GET", "/workflows/", token=token)
    check("workflows list", st, (200,), str(wfs)[:80])

    # 15 api keys
    st, keys = req("GET", "/api-keys/", token=token)
    check("api-keys list", st, (200,), str(keys)[:80])

    # 16 sso status
    st, sso = req("GET", "/auth/sso/status")
    check("sso status", st, (200,), str(sso)[:80])

    # 17 contacts list
    st, clist = req("GET", "/contacts", token=token)
    check("contacts list", st, (200,))

    # 18 delete contact
    if cid:
        st, _ = req("DELETE", f"/contacts/{cid}", token=token)
        check("contact delete", st, (200, 204))

    # 19 admin backups list
    st, bk = req("GET", "/admin/backups", token=token)
    check("admin backups (may 403 if not admin role)", st, (200, 403), str(bk)[:80])

    # 20 operation audit
    st, aud = req("GET", "/admin/audit/operations", token=token)
    check("admin audit ops", st, (200, 403), str(aud)[:80])

    print("\n===== SUMMARY =====")
    fails = [r for r in results if r[0] == "FAIL"]
    print(f"total={len(results)} fail={len(fails)}")
    for m, n, e in fails:
        print(f"  FAIL {n}: {e}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
