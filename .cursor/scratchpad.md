*This scratchpad file serves as a phase-specific task tracker and implementation planner. The Mode System on Line 1 is critical and must never be deleted. It defines two core modes: Implementation Type for new feature development and Bug Fix Type for issue resolution. Each mode requires specific documentation formats, confidence tracking, and completion criteria. Use "plan" trigger for planning phase (🎯) and "agent" trigger for execution phase (⚡) after reaching 95% confidence. Follow strict phase management with clear documentation transfer process.*

`MODE SYSTEM TYPES (DO NOT DELETE!):
1. Implementation Type (New Features):
   - Trigger: User requests new implementation
   - Format: MODE: Implementation, FOCUS: New functionality
   - Requirements: Detailed planning, architecture review, documentation
   - Process: Plan mode (🎯) → 95% confidence → Agent mode (⚡)

2. Bug Fix Type (Issue Resolution):
   - Trigger: User reports bug/issue
   - Format: MODE: Bug Fix, FOCUS: Issue resolution
   - Requirements: Problem diagnosis, root cause analysis, solution verification
   - Process: Plan mode (🎯) → Chain of thought analysis → Agent mode (⚡)

Cross-reference with @memories.md and @lessons-learned.md for context and best practices.`

# Mode: Refactoring 🎯
Focus: Systematic Project-wide Refactoring for Consistency
Confidence: 98% # payment_service refactored. client_service/panel_service refactored.

**High-Level Goal:** بازبینی و اصلاح کل پروژه لایه به لایه برای اطمینان از یکپارچگی در مدیریت session، خطاها، و پیروی از الگوی معماری تعریف شده در @project-requirements.md و @project_explanation_fa.md.

**Refactoring Plan:**

**Phase R1: Handler Layer Review (`bot/handlers/`)** - Completed ✅
*Goal: Ensure all handlers correctly instantiate services, pass sessions, and manage transactions/errors.*

1.  **[Handler-Common]** بررسی هندلرهای عمومی (Completed ✅)
2.  **[Handler-Admin]** بررسی هندلرهای ادمین (Completed ✅)
3.  **[Handler-User]** بررسی هندلرهای کاربر (Skipped - No handlers found) 
4.  **[Handler-Seller]** بررسی هندلرهای فروشنده (Skipped - No handlers found)

**Phase R2: Service Layer Review (`bot/services/`)** - Completed ✅
*Goal: Ensure all services handle sessions correctly and interact properly with repositories.*

*   **[Task-R2.1] Review `location_service.py`** (Completed ✅)
    *   Findings: Code generally conforms to standards. Repos instantiated in __init__. No major refactoring needed.
    *   Actual Result: `location_service.py` conforms to architectural standards. ✅
*   **[Task-R2.2] Review `user_service.py`** (Completed ✅)
    *   Findings: Service correctly assumes caller handles transactions after BaseRepo refactor. No changes needed in UserService itself.
    *   Actual Result: `user_service.py` conforms to architectural standards. ✅
*   **[Task-R2.3] Review `panel_service.py`** (Completed ✅)
    *   Findings: Significant refactoring applied to align with BaseRepo changes and ensure correct transaction boundaries.
    *   Actual Result: `panel_service.py` refactored to conform to architectural standards. ✅
*   **[Task-R2.4] Review `payment_service.py`** (Completed ✅)
    *   Actions: Completely rewrote the service to remove Tortoise ORM, use SQLAlchemy/Repositories, delegate transaction management, and use WalletServicePlaceholder.
    *   Findings: Major architectural inconsistency resolved. Dependencies on new repositories (Payment, Wallet, BankCard) identified and created. Requires WalletService implementation later.
    *   Actual Result: `payment_service.py` refactored to conform to architectural standards. ✅
*   **[Task-R2.5] Review `client_service.py`** (Completed ✅)
    *   **Action:** Read the code.
    *   **Action:** Check for correct session injection and usage.
    *   **Action:** Check for correct repository instantiation and usage (ClientAccount, Panel, User, Plan?).
    *   **Action:** Check interaction with PanelService and Panel Client (`xui_client`).
    *   **Action:** Check error handling, logging, and transaction management.
    *   **Action:** Apply necessary refactoring edits.
    *   **Expected Result:** `client_service.py` conforms to architectural standards.
    *   **Actual Result:** `client_service.py` полностью refactored включая `change_location` method. Успешно обновлены все методы для использования `inbound_id` и `panel_native_identifier`.
*   **[Task-R2.6] Add `panel_native_identifier` to `ClientAccount` model & migrate DB** (Completed ✅)
    *   Action: Added `panel_native_identifier: Mapped[Optional[str]]` to `core/database/models/client_account.py`.
    *   Action: Generated migration `4e61a3fdacab` using `moonvpn revision`.
    *   Action: Applied migration using `moonvpn migrate`.
    *   Actual Result: Database schema updated with the new field.
*   **[Task-R2.7] Review & Refactor `panel_service.py`** (Completed ✅)
    *   **Action:** Read the code.
    *   **Findings:**
        *   `__init__` requires `AsyncSession` injection (Fixed).
        *   Missing/Incorrect client management methods (add, update, delete, get_usage, get_config) (Fixed).
        *   Added support for `panel_native_identifier` AND `inbound_id` (Fixed).
        *   API calls updated to handle context of `protocol` (Fixed).
    *   **Actual Result:** `panel_service.py` fully refactored to conform to architectural standards and provide necessary methods for `ClientService`. Added missing method `get_panel_inbounds_by_panel_id`.
*   **[Task-R2.8] Add `inbound_id` to `ClientAccount` model & migrate DB** (Completed ✅)
    *   **Action:** Replaced `panel_inbound_id: Mapped[Optional[int]]` with `inbound_id: Mapped[int] = mapped_column(ForeignKey("panel_inbounds.id"), nullable=False, index=True)` in `core/database/models/client_account.py`. Updated relationship.
    *   **Action:** Generate new migration file using `moonvpn revision`. (Generated `4996f1134b19`)
    *   **Action:** Apply migration using `moonvpn migrate`.
    *   **Expected Result:** Database schema updated with `inbound_id` foreign key.
    *   **Actual Result:** Database schema updated. `ClientAccount` model now has a non-nullable `inbound_id` foreign key and index. ✅
*   **[Task-R2.9] Refactor `ClientService` for `inbound_id`** (Completed ✅)
    *   **Action:** Updated `create_client` to determine and save `inbound_id` in `ClientAccount` object.
    *   **Action:** Updated calls to `PanelService.update_client_on_panel` to pass `inbound_id`.
    *   **Expected Result:** `ClientService` correctly handles and passes `inbound_id`.
    *   **Actual Result:** All methods in `ClientService` now correctly use `inbound_id` with all `PanelService` interactions.
*   **[Task-R2.10] Refactor `PanelService` client methods** (Completed ✅)
    *   **Action:** Updated all client methods (`add_client_to_panel`, `update_client_on_panel`, `delete_client_from_panel`, etc.) to accept and use `inbound_id`.
    *   **Action:** Updated `XuiPanelClient` methods to accept and use `protocol` and `inbound_id` parameters to determine correct API endpoints and identifiers.
    *   **Action:** Implemented protocol-specific handling for all client operations (add, update, delete, reset, get traffic).
    *   **Expected Result:** `PanelService` correctly relays `inbound_id` to panel client APIs.
    *   **Actual Result:** All client methods in `PanelService` and `XuiPanelClient` now properly handle protocol-specific identifies and inbound_id parameters. ✅
*   **[Task-R2.11] Complete `ClientService` refactoring** (Completed ✅)
    *   **Action:** Updated remaining methods in `ClientService` to use the refactored `PanelService` methods with `inbound_id`.
    *   **Action:** Completed `change_location` method implementation to use `inbound_id` and `panel_native_identifier`.
    *   **Action:** Fixed repository references from `panel_inbound` to `inbound` in `ClientRepository`.
    *   **Expected Result:** `ClientService` completely refactored to use `inbound_id` with all `PanelService` interactions.
    *   **Actual Result:** `ClientService` fully refactored and working correctly with new relationship name `inbound`. All ORM mapping errors resolved.
*   **[Task-R2.12] Update `@project-requirements.md` API Section** (Current Focus 🎯)
    *   **Action:** Reflect the need for `inbound_id`, the strategy for `native_identifier`, API limitations, and updated client method signatures.
    *   **Expected Result:** Documentation accurately reflects the implementation reality.

**Phase R3: Repository Layer Review (`core/database/repositories/`)** (Current Focus 🎯)
*Goal: Final confirmation of consistency in repository patterns.*
*   **[Task-R3.0]** Review `base_repo.py` (Completed ✅ during Phase R2)
*   **[Task-R3.1]** Create missing repositories (Payment, Wallet, BankCard) (Completed ✅ during Phase R2)
*   **[Task-R3.2]** Check all repositories for consistent use of:
    * Direct session arg passing to all methods
    * Not storing session state in repository instance
    * Proper relationship loading (using selectinload)
    * Proper handling of nullable fields
    * Consistent return types (especially when None is possible)
*   **[Task-R3.3]** Verify repository coverage (are all models represented by repositories?)
*   **[Task-R3.4]** Ensure consistent naming conventions across repositories
*   **[Task-R3.5]** Check for proper annotation and type hints

**Phase R4: Core Components Review (`bot/main.py`, `middlewares`, etc.)**
*Goal: Verify core setup and middleware functionality.*
*   **[Task-R4.1]** Review `bot/main.py` for proper service instantiation and middleware registration.
*   **[Task-R4.2]** Check `DbSessionMiddleware` for proper session handling.
*   **[Task-R4.3]** Review other middlewares for consistent patterns.
*   **[Task-R4.4]** Check error handling and logging configuration.

**Identified Issues/Improvements:**
*   **[Improvement-1]** Fix `scripts/moonvpn.sh` restart command to correctly recognize 'Up' status. (Completed ✅)
*   **[Check-1]** Verify if database contains seed data (e.g., panels) for thorough testing.
*   **[TODO-1]** Create SQLAlchemy schemas (`core/schemas/`) for Wallet, Payment, BankCard.
*   **[TODO-2]** Implement `WalletService` to replace `WalletServicePlaceholder`.
*   **[Check-2]** Review Alembic migration (`2268f7a04299_...`) for correctness regarding Wallet model addition.

---
*End of Scratchpad*