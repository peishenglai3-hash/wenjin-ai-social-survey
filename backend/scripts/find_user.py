"""Find user by name and optionally grant admin role.

Usage — run inside Docker container:
  docker exec ai-social-survey-backend-1 python3 /app/scripts/find_user.py "余一帆"
  docker exec ai-social-survey-backend-1 python3 /app/scripts/find_user.py "余一帆" --promote
"""

import asyncio
import sys

sys.path.insert(0, "/app")

from app.models.user import UserAccount
from app.core.database import async_session_factory
from sqlalchemy import select


async def main(search: str, promote: bool = False):
    async with async_session_factory() as session:
        # Fuzzy search by display_name, email, phone
        result = await session.execute(
            select(UserAccount).where(
                (UserAccount.display_name.ilike(f"%{search}%")) |
                (UserAccount.email.ilike(f"%{search}%"))
            )
        )
        users = result.scalars().all()

        if not users:
            print(f"\n  ❌ 未找到匹配 '{search}' 的用户")
            print(f"  💡 当前所有注册用户：")
            all_result = await session.execute(select(UserAccount))
            for u in all_result.scalars().all():
                print(f"     [{u.role:12}] ID={u.id:3d} | {u.display_name:15s} | {u.email}")
            return

        print(f"\n  ✅ 找到 {len(users)} 个匹配 '{search}' 的用户:\n")
        print(f"  {'ID':<5} {'角色':<12} {'显示名':<16} {'邮箱':<35} {'激活':<5} {'手机':<15}")
        print(f"  {'-'*5} {'-'*12} {'-'*16} {'-'*35} {'-'*5} {'-'*15}")
        for u in users:
            print(f"  {u.id:<5} {u.role:<12} {u.display_name:<16} {u.email:<35} {'是' if u.is_active else '否':<5} {u.phone or '—':<15}")

        if promote:
            for u in users:
                if u.role == "admin":
                    print(f"\n  ⏭️  ID={u.id} ({u.display_name}) 已是管理员，跳过")
                    continue
                u.role = "admin"
                print(f"\n  🔑 已将 ID={u.id} ({u.display_name} | {u.email}) 提升为管理员！")
            await session.commit()
            print("\n  ✅ 数据库已更新。")
        else:
            print(f"\n  💡 加 --promote 参数以提升为管理员")


if __name__ == "__main__":
    search_term = sys.argv[1] if len(sys.argv) > 1 else ""
    do_promote = "--promote" in sys.argv
    if not search_term or search_term == "--promote":
        print("Usage: python3 find_user.py <search_term> [--promote]")
        print("Example: python3 find_user.py 余一帆 --promote")
        sys.exit(1)
    asyncio.run(main(search_term, do_promote))
