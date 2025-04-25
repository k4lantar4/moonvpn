#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from db import async_session_maker
from db.models.panel import Panel, PanelStatus, PanelType
from db.models.plan import Plan, PlanStatus
from db.models.user import User

async def seed_panel_and_plan():
    async with async_session_maker() as session:
        # ensure admin test user exists
        result = await session.execute(select(User).filter(User.telegram_id == 9000000001))
        user = result.scalars().first()
        if not user:
            print('⚠️ Admin user with telegram_id=9000000001 not found. Cannot seed plan.')
            return

        # seed panel
        panel_name = 'پنل تستی'
        result = await session.execute(select(Panel).filter(Panel.name == panel_name))
        panel = result.scalars().first()
        if not panel:
            new_panel = Panel(
                name=panel_name,
                location_name='Germany',
                url='http://example.com:54321',
                username='admin',
                password='password',
                type=PanelType.XUI,
                status=PanelStatus.ACTIVE,
                notes='ساخته شده برای تست'
            )
            session.add(new_panel)
            try:
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                print(f'⚠️ Failed to insert panel: {e}')
            else:
                print('✅ Test panel seeded')
        else:
            print('🔁 Test panel already exists, skipping')

        # seed plan
        plan_name = 'پلن تستی'
        result = await session.execute(select(Plan).filter(Plan.name == plan_name))
        plan = result.scalars().first()
        if not plan:
            new_plan = Plan(
                name=plan_name,
                description='پلن با حجم کم برای تست',
                traffic_gb=5,
                duration_days=7,
                price=10000,
                available_locations=['Germany'],
                status=PlanStatus.ACTIVE,
                created_by_id=user.id
            )
            session.add(new_plan)
            try:
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                print(f'⚠️ Failed to insert plan: {e}')
            else:
                print('✅ Test plan seeded')
        else:
            print('🔁 Test plan already exists, skipping')

    print('✅ Test panel and plan seeded successfully')

if __name__ == '__main__':
    asyncio.run(seed_panel_and_plan())