from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone, timedelta, date
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.installment import Installment
from app.models.customer import Customer

class SalesService:
    def __init__(self, db: AsyncSession, company_id: str):
        self.db = db
        self.company_id = company_id
    
    async def get(self, id: str) -> Sale | None:
        """Busca uma venda por ID validando company_id"""
        stmt = select(Sale).options(
            joinedload(Sale.items), 
            joinedload(Sale.installments)
        ).where(
            Sale.id == id, 
            Sale.company_id == self.company_id
        )
        return (await self.db.execute(stmt)).scalars().first()
    
    async def list(self, **filters):
        """Lista vendas com filtros opcionais"""
        stmt = select(Sale).options(
            joinedload(Sale.installments)
        ).where(
            Sale.company_id == self.company_id
        ).order_by(Sale.sale_date.desc())
        
        if (v := filters.get("customer_id")): 
            stmt = stmt.where(Sale.customer_id == v)
        if (v := filters.get("status")): 
            stmt = stmt.where(Sale.status == v)
        if (v := filters.get("payment_method")): 
            stmt = stmt.where(Sale.payment_method == v)
        if (v := filters.get("date_from")): 
            stmt = stmt.where(Sale.sale_date >= v)
        if (v := filters.get("date_to")): 
            stmt = stmt.where(Sale.sale_date < v)
        
        return (await self.db.execute(stmt)).scalars().all()
    
    async def create_sale(self, payload: dict) -> Sale:
        """
        Cria uma nova venda com validações completas
        
        Validações:
        - Cliente existe e pertence à empresa
        - Produtos existem, estão ativos e têm estoque
        - Desconto não excede o total
        - Parcelas são criadas corretamente para crediário
        """
        # Validar cliente
        customer = (await self.db.execute(
            select(Customer).where(
                Customer.id == payload["customer_id"], 
                Customer.company_id == self.company_id,
                Customer.status == "active"
            )
        )).scalars().first()
        
        if not customer:
            raise ValueError("Cliente não encontrado ou inativo")
        
        # Buscar produtos com lock para evitar race condition no estoque
        product_ids = [str(i["product_id"]) for i in payload["items"]]
        products = (await self.db.execute(
            select(Product).where(
                Product.id.in_(product_ids), 
                Product.company_id == self.company_id,
                Product.status == "active"
            ).with_for_update()
        )).scalars().all()
        
        if len(products) != len(product_ids):
            raise ValueError("Um ou mais produtos não encontrados ou inativos")
        
        pmap = {str(p.id): p for p in products}
        items = []
        total = 0.0
        total_cost = 0.0
        
        # Validar estoque e calcular totais
        for it in payload["items"]:
            p = pmap[str(it["product_id"])]
            qty = int(it["quantity"])
            
            if p.stock < qty:
                raise ValueError(f"Estoque insuficiente para produto {p.name}. Disponível: {p.stock}")
            
            price = float(p.price or 0)
            cost = float(p.cost_price or 0)
            total += price * qty
            total_cost += cost * qty
            
            items.append(SaleItem(
                product_id=p.id, 
                quantity=qty, 
                unit_price=price,
                unit_cost_price=cost
            ))
        
        discount = float(payload.get("discount_amount", 0))
        if discount < 0:
            raise ValueError("Desconto não pode ser negativo")
        if discount > total:
            raise ValueError("Desconto não pode ser maior que o total da venda")
        
        # Criar venda
        sale = Sale(
            company_id=self.company_id,
            customer_id=customer.id,
            total_amount=total,
            total_cost=total_cost,
            discount_amount=discount,
            payment_method=payload["payment_method"],
            sale_date=datetime.now(timezone.utc),
            first_due_date=payload.get("first_due_date"),
            status="completed"
        )
        self.db.add(sale)
        await self.db.flush()
        
        # Criar itens e debitar estoque
        for si in items:
            si.sale_id = sale.id
            self.db.add(si)
            pmap[str(si.product_id)].stock -= si.quantity
        
        # Criar parcelas para crediário
        if sale.payment_method == "credit":
            n = payload.get("num_installments") or 1
            if n < 1:
                n = 1
            
            first_due = payload.get("first_due_date")
            if not first_due:
                raise ValueError("Data do primeiro vencimento obrigatória para crediário")
            
            total_after_discount = total - discount
            base = round(total_after_discount / n, 2)
            amounts = [base] * n
            
            # Ajustar última parcela para compensar arredondamentos
            diff = round(total_after_discount - base * n, 2)
            if diff != 0:
                amounts[-1] = round(amounts[-1] + diff, 2)
            
            for i in range(n):
                due = first_due + timedelta(days=30 * i)
                self.db.add(Installment(
                    sale_id=sale.id,
                    amount=amounts[i],
                    due_date=due,
                    status="pending"
                ))
        
        await self.db.commit()
        await self.db.refresh(sale)
        return sale
    
    async def cancel(self, sale: Sale):
        """
        Cancela uma venda e restaura o estoque
        
        Validações:
        - Venda deve estar completa
        - Restaura estoque de todos os produtos
        - Cancela parcelas pendentes
        """
        if sale.status != "completed":
            return sale
        
        # Restaurar estoque
        for it in sale.items:
            p = (await self.db.execute(
                select(Product).where(
                    Product.id == it.product_id, 
                    Product.company_id == self.company_id
                )
            )).scalars().first()
            if p:
                p.stock += it.quantity
        
        sale.status = "canceled"
        
        # Cancelar parcelas não pagas
        for inst in sale.installments:
            if inst.status in ["pending", "overdue"]:
                inst.status = "canceled"
        
        await self.db.commit()
        await self.db.refresh(sale)
        return sale
