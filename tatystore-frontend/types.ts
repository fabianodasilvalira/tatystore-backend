
export interface Product {
  id: string;
  name: string;
  brand: string | null;
  description: string;
  sale_price: number;
  cost_price: number;
  stock_quantity: number;
  min_stock: number;
  sku: string | null;
  barcode: string | null;
  image_url?: string;
  is_active: boolean;
  is_on_sale: boolean;
  promotional_price?: number | null;
  category_id?: number | null;
  category?: Category | null;
  company_id: number;
  created_at?: string;
  updated_at?: string;
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  cpf: string;
  is_active: boolean;
  status: 'active' | 'inactive'; // Derived from is_active
  total_debt: number;
  company_id: number;
  created_at: string;
  updated_at?: string;
}

export interface SaleItem {
  productId: string;
  quantity: number;
  unitPrice: number;
  unitCostPrice: number; // Custo no momento da venda
  productName?: string;
}

export type PaymentMethod = 'cash' | 'credit' | 'pix';
export type InstallmentStatus = 'pending' | 'paid' | 'overdue' | 'canceled';

export interface Installment {
  id: string;
  saleId: string;
  customerId: string;
  amount: number;
  dueDate: Date;
  status: InstallmentStatus;
  customerName?: string;
  saleDate?: Date;
  remainingAmount?: number;
}

// --- Tipos para Pagamento Parcial ---
export interface PaymentHistoryItem {
  id: number;
  installment_id: number;
  amount_paid: number;
  created_at: string;
  paid_at: string;
}

export interface InstallmentDetail {
  id: number;
  sale_id: number;
  customer_id: number;
  installment_number: number;
  amount: number; // Valor original total da parcela
  due_date: string;
  status: InstallmentStatus;
  total_paid: number; // Soma dos pagamentos parciais
  remaining_amount: number; // Quanto falta pagar
  payments: PaymentHistoryItem[]; // Histórico
}
// ------------------------------------

export interface Sale {
  id: string;
  customerId: string;
  customerName?: string;
  items: SaleItem[];
  total: number;
  totalCost: number; // Custo total da venda
  profit?: number;
  profit_margin_percentage?: number;
  discountAmount: number;
  paymentMethod: PaymentMethod;
  installments: Installment[];
  date: Date;
  firstDueDate?: Date;
  status: 'completed' | 'canceled';
}

export interface Company {
  id: number;
  name: string;
  cnpj: string;
  email: string;
  phone: string;
  address: string;
  slug: string;
  is_active: boolean;
  created_at: string;
  access_url: string;
  logo_url: string | null;
  theme_color?: string;
  pix?: {
    pix_key: string;
    pix_type: string;
  } | null;
}

export interface Category {
  id: number;
  name: string;
  description: string | null;
  company_id: number;
  is_active: boolean;
  product_count?: number;
  created_at: string;
  updated_at: string;
}

export type Page = 'dashboard' | 'products' | 'sales' | 'customers' | 'reports' | 'settings' | 'companies' | 'users' | 'categories' | 'installments' | 'company';

export type FilterType = 'today' | 'week' | 'month' | 'to_date' | 'custom';

export type ReportType = 'sales' | 'profit' | 'overdue' | 'sold_products' | 'low_stock' | 'canceled_sales';

export type Role = string;

export interface User {
  id: number;
  name: string;
  email: string;
  company_id: number;
  role_id: number;
  last_login_at: string;
  must_change_password: boolean;
  company_slug: string;
  role: Role;
  is_active: boolean;
  company_name: string;
  company_logo_url: string | null;
}

export interface RoleInfo {
  id: number;
  name: string;
}

export interface AuthContextType {
  user: User | null;
  tokens: { access_token: string, redirect_url: string } | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<any>;
  logout: () => void;
  setUser: (user: User | null) => void;
}

export interface ProductProfitAnalysis {
  product_id: number;
  product_name: string;
  cost_price: number;
  sale_price: number;
  promotional_price: number | null;
  is_on_sale: boolean;
  normal_profit: number;
  normal_margin_percentage: number;
  promotional_profit: number | null;
  promotional_margin_percentage: number | null;
  active_profit: number;
  active_margin_percentage: number;
  active_price: number;
  recommendation: string;
}
