import sys
import os
sys.path.append("/app")

print("--- DIAGNOSTIC SCRIPT START ---")

try:
    print("1. Importing products_import module...")
    from app.api.v1.endpoints import products_import
    print(f"   products_import module: {products_import}")
    print(f"   products_import.router: {products_import.router}")
    print(f"   Router routes count: {len(products_import.router.routes)}")
    for r in products_import.router.routes:
        print(f"   - {r.path} {r.methods}")

    print("\n2. Importing api module...")
    from app.api.v1 import api
    print(f"   api module: {api}")
    print(f"   api_router routes count: {len(api.api_router.routes)}")
    
    print("\n3. Searching for 'products' routes in api_router (ORDER MATTERS)...")
    count = 0
    for r in api.api_router.routes:
        if "products" in r.path:
            count += 1
            print(f"   [{count}] {r.path} {r.methods}")
            if count > 20:
                print("   ... (limiting output) ...")
                break

except Exception as e:
    print(f"\nEXCEPTION: {e}")
    import traceback
    traceback.print_exc()

print("--- DIAGNOSTIC SCRIPT END ---")
