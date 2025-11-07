from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timedelta, timezone
from app.core.deps import get_company_id_from_path, require_permission
from app.core.db import get_db
from app.middleware.rate_limit import limiter

router = APIRouter(prefix="/{company_slug}/api/v1/reports", tags=["Reports"])

@router.get("/dash/overview", dependencies=[Depends(require_permission("reports.view"))])
@limiter.limit("30/minute")
async def overview(company_id: str = Depends(get_company_id_from_path), db: AsyncSession = Depends(get_db)):
    sql = text("""
        SELECT
          COALESCE(SUM(CASE WHEN s.status='completed' THEN s.total_amount - s.discount_amount ELSE 0 END),0)::numeric as revenue,
          COUNT(*) FILTER (WHERE s.status='completed')::int as sales_count,
          COUNT(*) FILTER (WHERE s.status='canceled')::int as canceled_count,
          (SELECT COALESCE(SUM(i.amount),0) FROM installments i
           JOIN sales sx ON sx.id = i.sale_id
           WHERE sx.company_id = :cid AND i.status='overdue')::numeric as overdue_amount
        FROM sales s WHERE s.company_id=:cid
    """ )
    row = (await db.execute(sql, {"cid": company_id})).mappings().first()
    return row

@router.get("/dash/sales-by-day", dependencies=[Depends(require_permission("reports.view"))])
@limiter.limit("60/minute")
async def sales_by_day(company_id: str = Depends(get_company_id_from_path),
                       days: int = Query(default=15, ge=1, le=90),
                       db: AsyncSession = Depends(get_db)):
    sql = text("""
        SELECT to_char(date_trunc('day', sale_date),'YYYY-MM-DD') as day,
               COALESCE(SUM(CASE WHEN status='completed' THEN total_amount - discount_amount ELSE 0 END),0)::numeric as revenue,
               COUNT(*) FILTER (WHERE status='completed')::int as count
        FROM sales WHERE company_id=:cid AND sale_date >= (NOW() - (:days || ' days')::interval)
        GROUP BY 1 ORDER BY 1
    """)
    rows = (await db.execute(sql, {"cid": company_id, "days": days})).mappings().all()
    return rows

@router.get("/dash/top-products", dependencies=[Depends(require_permission("reports.view"))])
@limiter.limit("60/minute")
async def top_products(company_id: str = Depends(get_company_id_from_path),
                       limit: int = Query(default=5, ge=1, le=20),
                       db: AsyncSession = Depends(get_db)):
    sql = text("""
        SELECT p.id, p.name, SUM(si.quantity)::int as qty, SUM(si.quantity*si.unit_price)::numeric as total
        FROM sale_items si
        JOIN sales s ON s.id = si.sale_id
        JOIN products p ON p.id = si.product_id
        WHERE s.company_id = :cid AND s.status='completed'
        GROUP BY p.id, p.name
        ORDER BY total DESC
        LIMIT :lim
    """ )
    rows = (await db.execute(sql, {"cid": company_id, "lim": limit})).mappings().all()
    return rows

@router.get("/dash/payment-method-share", dependencies=[Depends(require_permission("reports.view"))])
@limiter.limit("60/minute")
async def payment_method_share(company_id: str = Depends(get_company_id_from_path), db: AsyncSession = Depends(get_db)):
    sql = text("""
        SELECT payment_method, COUNT(*)::int as count,
               COALESCE(SUM(total_amount - discount_amount),0)::numeric as total
        FROM sales WHERE company_id=:cid AND status='completed'
        GROUP BY payment_method
    """ )
    rows = (await db.execute(sql, {"cid": company_id})).mappings().all()
    return rows

@router.get("/dash/overdue-customers", dependencies=[Depends(require_permission("reports.view"))])
@limiter.limit("30/minute")
async def overdue_customers(company_id: str = Depends(get_company_id_from_path), db: AsyncSession = Depends(get_db)):
    sql = text("""
        SELECT c.id, c.name, c.phone, c.email,
               COALESCE(SUM(i.amount),0)::numeric as overdue_total,
               COUNT(*)::int as overdue_count
        FROM installments i
        JOIN sales s ON s.id = i.sale_id
        JOIN customers c ON c.id = s.customer_id
        WHERE s.company_id=:cid AND i.status='overdue'
        GROUP BY c.id, c.name, c.phone, c.email
        ORDER BY overdue_total DESC
        LIMIT 20
    """)
    rows = (await db.execute(sql, {"cid": company_id})).mappings().all()
    return rows

@router.get("/dash/low-stock", dependencies=[Depends(require_permission("reports.view"))])
@limiter.limit("60/minute")
async def low_stock(company_id: str = Depends(get_company_id_from_path),
                    threshold: int = Query(default=5, ge=0, le=100),
                    db: AsyncSession = Depends(get_db)):
    sql = text("""
        SELECT id, name, stock FROM products
        WHERE company_id=:cid AND stock <= :th
        ORDER BY stock ASC, name ASC
        LIMIT 50
    """ )
    rows = (await db.execute(sql, {"cid": company_id, "th": threshold})).mappings().all()
    return rows

