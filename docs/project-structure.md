.
├── admin_refactor_restart.sh
├── alembic.ini
├── bot
│   ├── buttons
│   │   ├── account_buttons.py
│   │   ├── admin
│   │   │   ├── bank_card_buttons.py
│   │   │   ├── __init__.py
│   │   │   ├── main_buttons.py
│   │   │   ├── order_buttons.py
│   │   │   ├── panel_buttons.py
│   │   │   ├── plan_buttons.py
│   │   │   ├── receipt_buttons.py
│   │   │   └── user_buttons.py
│   │   ├── admin_buttons.py
│   │   ├── buy_buttons.py
│   │   ├── common_buttons.py
│   │   ├── inbound_buttons.py
│   │   ├── __init__.py
│   │   ├── panel_buttons.py
│   │   ├── plan_buttons.py
│   │   ├── receipt_buttons.py
│   │   ├── start_buttons.py
│   │   └── wallet_buttons.py
│   ├── callbacks
│   │   ├── account_callbacks.py
│   │   ├── admin
│   │   │   ├── bank_card_callbacks.py
│   │   │   ├── __init__.py
│   │   │   ├── main_callbacks.py
│   │   │   ├── order_callbacks.py
│   │   │   ├── panel_callbacks.py
│   │   │   ├── plan_callbacks.py
│   │   │   ├── receipt_callbacks.py
│   │   │   └── user_callbacks.py
│   │   ├── admin_callbacks.py
│   │   ├── buy_callbacks.py
│   │   ├── client_callbacks.py
│   │   ├── common_callbacks.py
│   │   ├── inbound_callbacks.py
│   │   ├── __init__.py
│   │   ├── panel_callbacks.py
│   │   ├── plan_callbacks.py
│   │   ├── receipt_callbacks.py
│   │   └── wallet_callbacks.py
│   ├── commands
│   │   ├── admin.py
│   │   ├── buy.py
│   │   ├── __init__.py
│   │   ├── myaccounts.py
│   │   ├── plans.py
│   │   ├── profile.py
│   │   ├── start.py
│   │   └── wallet.py
│   ├── __init__.py
│   ├── keyboards
│   │   ├── admin_keyboard.py
│   │   ├── buy_keyboards.py
│   │   ├── __init__.py
│   │   ├── profile_keyboard.py
│   │   ├── receipt_keyboards.py
│   │   ├── start_keyboard.py
│   │   ├── user_keyboard.py
│   │   └── wallet_keyboard.py
│   ├── main.py
│   ├── middlewares
│   │   ├── auth.py
│   │   ├── error.py
│   │   ├── __init__.py
│   │   └── throttling.py
│   ├── notifications
│   │   ├── dispatcher.py
│   │   └── __init__.py
│   ├── receipts
│   │   ├── __init__.py
│   │   └── receipt_handlers.py
│   ├── states
│   │   ├── admin_states.py
│   │   ├── buy_states.py
│   │   ├── __init__.py
│   │   └── receipt_states.py
│   ├── states.py
│   └── utils.py
├── CHANGELOG.md
├── core
│   ├── __init__.py
│   ├── integrations
│   │   └── xui_client.py
│   ├── log_config.py
│   ├── scripts
│   │   ├── seed_panel_and_plan.py
│   │   └── seed_users.py
│   ├── services
│   │   ├── account_service.py
│   │   ├── bank_card_service.py
│   │   ├── client_renewal_log_service.py
│   │   ├── client_service.py
│   │   ├── inbound_service.py
│   │   ├── location_service.py
│   │   ├── notification_service.py
│   │   ├── order_service.py
│   │   ├── panel_service.py
│   │   ├── payment_service.py
│   │   ├── plan_service.py
│   │   ├── receipt_service.py
│   │   ├── settings_service.py
│   │   ├── transaction_service.py
│   │   ├── user_service.py
│   │   └── wallet_service.py
│   └── settings.py
├── db
│   ├── config.py
│   ├── __init__.py
│   ├── migrations
│   │   ├── env.py
│   │   ├── __init__.py
│   │   ├── script.py.mako
│   │   └── versions
│   │       ├── 20250425_053314_initial_schema_generation_final.py
│   │       ├── 20250427_015905_fix_panel_inbound_clientaccount_models.py
│   │       ├── 20250427_add_pending_receipt_status.py
│   │       ├── add_payment_settings.py
│   │       └── add_wallet_model.py
│   ├── models
│   │   ├── account_transfer.py
│   │   ├── bank_card.py
│   │   ├── client_account.py
│   │   ├── client_renewal_log.py
│   │   ├── discount_code.py
│   │   ├── enums.py
│   │   ├── inbound.py
│   │   ├── __init__.py
│   │   ├── notification_log.py
│   │   ├── order.py
│   │   ├── panel.py
│   │   ├── plan.py
│   │   ├── receipt_log.py
│   │   ├── setting.py
│   │   ├── test_account_log.py
│   │   ├── transaction.py
│   │   ├── user.py
│   │   └── wallet.py
│   ├── repositories
│   │   ├── account_repo.py
│   │   ├── bank_card_repository.py
│   │   ├── base_repository.py
│   │   ├── client_renewal_log_repo.py
│   │   ├── client_repo.py
│   │   ├── discount_code_repo.py
│   │   ├── inbound_repo.py
│   │   ├── __init__.py
│   │   ├── order_repo.py
│   │   ├── panel_repo.py
│   │   ├── plan_repo.py
│   │   ├── receipt_log_repository.py
│   │   ├── setting_repo.py
│   │   ├── transaction_repo.py
│   │   ├── user_repo.py
│   │   └── wallet_repo.py
│   └── schemas
│       ├── account_schema.py
│       ├── order.py
│       ├── transaction.py
│       └── user_schema.py
├── docker-compose.yml
├── Dockerfile
├── docs
│   ├── bot-log.md
│   ├── database-structure.md
│   ├── legacy-capabilities.md
│   ├── project-relationships.md
│   ├── project-requirements.md
│   ├── project-structure.md
│   ├── scratchpad.md
│   ├── tree-moonvpn.md
│   └── xui_api_methods.md
├── .env
├── .env.example
├── .gitignore
├── lessons-learned.md
├── memories.md
├── me.rule.md
├── poetry.lock
├── pyproject.toml
├── README.md
├── scratchpad.md
├── scripts
│   ├── moonvpn.sh
│   ├── sync_panels.py
│   ├── test_card_to_card_payment.py
│   └── test_receipt_approval.py
├── SECURITY.md
├── tests
│   ├── __init__.py
│   └── test_account_service.py
└── workspace.code-workspace