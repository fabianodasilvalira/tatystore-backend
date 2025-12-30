
def generate_default_template(categories):
    category_examples = [cat.name for cat in categories] if categories else ["Maquiagem", "Perfumaria", "Cuidados"]
    csv_content = "nome,marca,categoria,descricao,preco_custo,preco_venda,estoque,estoque_minimo,sku,codigo_barras,ativo,em_promocao,preco_promocional\n"
    csv_content += f"Batom Natura 001,Natura,{category_examples[0]},Batom vermelho intenso,15.50,35.90,0,5,NAT-BAT-001,7891234567890,false,false,\n"
    csv_content += f"Perfume Boticário XYZ,Boticário,{category_examples[1] if len(category_examples) > 1 else category_examples[0]},Perfume masculino 100ml,45.00,120.00,0,3,BOT-PER-001,7891234567891,false,false,\n"
    csv_content += f"Creme Eudora ABC,Eudora,{category_examples[2] if len(category_examples) > 2 else category_examples[0]},Creme hidratante facial,25.00,65.00,0,10,EUD-CRE-001,7891234567892,false,true,49.90\n"
    return csv_content
