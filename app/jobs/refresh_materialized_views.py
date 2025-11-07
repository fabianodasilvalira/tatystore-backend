from app.core.db import AsyncSessionLocal

async def refresh_materialized_views():
    async with AsyncSessionLocal() as session:
        await session.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY sales_summary_mv;")
        await session.commit()
