# 🧪 MoonVPN - Scratchpad / Task Queue

> Updated: 2025-04-21  
> Purpose: Provide a centralized list of copy-ready prompts to validate and align the project structure, database, async setup, and core flows with the official documentation.

---

## 🔄 Global Validation & Fix Prompts

### ✅ Prompt A – Validate & Migrate Database Schema
```markdown
🔧 Task A: Validate & Migrate Database Schema

📄 References:
- docs/database-structure.md
- docs/project-relationships.md

1. Run migrations:
```bash
moonvpn restart
moonvpn migrate
```
2. Compare `db/models/*.py` with database-structure.md:
   - Tables and columns: user, panel, inbound, client_account, plan, order, transaction, bank_card, receipt_log, etc.
   - All types, FK, PK match.
3. If mismatch exists:
   - Update model.
   - Create migration:
```bash
moonvpn migrate-create "fix schema"
moonvpn migrate
```
4. Confirm schema in DB.
✅ Reply with: DB schema fully compliant ✅
```

---

### ✅ Prompt B – Validate Project File Structure
```markdown
🔧 Task B: Validate Project Structure

📄 Reference: docs/project-structure.md

1. Run:
```bash
tree . -L 2
```
2. Compare output with allowed folders/files:
   - bot/, core/, db/, scripts/, tests/, docs/, .env, docker-compose.yml, Dockerfile
   - Reject or move unknown paths.
✅ Reply with: Project structure is clean ✅
```

---

### ✅ Prompt C – Validate ORM Relationships
```markdown
🔧 Task C: Validate SQLAlchemy Relationships

📄 References:
- docs/database-structure.md
- docs/project-relationships.md

1. In each model file in `db/models`, verify `ForeignKey()` and `relationship()` match documented design.
2. For each missing relationship:
   - Fix in model.
   - Create migration:
```bash
moonvpn migrate-create "fix relationships"
moonvpn migrate
```
✅ Reply with: ORM relationships correct ✅
```

---

### ✅ Prompt D – Validate Async XuiClient Wrapper
```markdown
🔧 Task D: Validate XuiClient Async Wrapper

📄 Reference:
- core/integrations/xui_client.py

1. Check `xui_client.py`:
   - Uses `AsyncApi` from py3xui.async_api.
   - Defines `async def` methods with `await`: login, get_inbounds, create_client, get_config, delete_client, etc.
2. Test with:
```bash
moonvpn exec-bot python - <<'PYCODE'
import asyncio
from core.integrations.xui_client import XuiClient
async def test():
  x = XuiClient(...)
  await x.login()
  print(await x.get_inbounds())
asyncio.run(test())
PYCODE
```
✅ Reply with: XuiClient wrapper is fully async ✅
```

---

### ✅ Prompt E – Fix `/buy` Flow & Display Inbounds
```markdown
🔧 Task E: Fix Inbound Display in /buy

📄 Reference:
- bot/commands/buy.py
- bot/buttons/inbound_buttons.py

1. After user chooses location (panel):
   - Query `inbound` table → list active inbounds.
   - Render buttons: `protocol@port`
2. If no inbound: show message "فعلاً اینباندی موجود نیست."
3. Ensure `panel_service.sync_inbounds()` is called at startup.
✅ Reply with: Inbounds display fixed ✅
```

---

### ✅ Prompt F – Validate Wallet Payment Flow
```markdown
🔧 Task F: Validate Wallet Payment

📄 Reference:
- PaymentService, OrderService

1. Buy with wallet:
   - Deduct balance from user
   - Add transaction (type: purchase)
   - Set order.status = paid → create client
2. Test:
   - Recharge wallet → buy → confirm config sent
✅ Reply with: Wallet flow is functional ✅
```

---

### ✅ Prompt G – Validate Reply Keyboards
```markdown
🔧 Task G: Validate Reply Keyboard

📄 Reference:
- bot/keyboards/user_keyboard.py

1. Keyboard must include buttons: `/start`, `/plans`, `/wallet`, `/myaccounts`, `/settings`
2. Attached to start command.
3. Test: each button sends related command.
✅ Reply with: Reply keyboard working ✅
```

---

### ✅ Prompt H – Validate Receipt & Card Flow
```markdown
🔧 Task H: Validate Card-to-Card Flow

📄 Reference:
- bot/receipts/, db/models/receipt_log.py

1. Choose card from active list (by rotation).
2. Show card to user, receive receipt (text/photo).
3. Save to `receipt_log`, assign `tracking_code`
4. Send receipt to `telegram_channel_id` of the card
5. Admin approves → updates DB → notifies user
✅ Reply with: Receipt + tracking flow complete ✅
```

