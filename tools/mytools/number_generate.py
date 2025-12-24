import random

def generate_engineering_all_styles(count=10000):
    texts = []
    units = ["LED", "MAX", "MIN", "mm", "deg", "R", "SR", "x", "X"]
    
    for _ in range(count):
        # 随机选择一种模式
        mode = random.choice(['equation', 'tolerance', 'parentheses', 'basic_dim'])
        
        if mode == 'equation':
            # 模式 1: 等式 13.97X5=69.85
            n1 = round(random.uniform(1, 100), 2)
            n2 = random.randint(1, 12)
            res = round(n1 * n2, 2)
            op = random.choice(['X', 'x'])
            texts.append(f"{n1}{op}{n2}={res}")
            
        elif mode == 'tolerance':
            # 模式 2: 公差 0.50 ±0.08 LED
            val = round(random.uniform(0, 100), 2)
            tol = round(random.uniform(0.01, 0.5), 2)
            has_unit = random.random() > 0.5
            if has_unit:
                unit = random.choice(units)
                texts.append(f"{val:g} ±{tol:g} {unit}")
            else:
                texts.append(f"{val:g} ±{tol:g}")
                
        elif mode == 'parentheses':
            # 模式 3: 参考尺寸 (20.0) 或 (R5.0)
            val = round(random.uniform(0.5, 500), 1)
            is_radius = random.random() > 0.7
            if is_radius:
                texts.append(f"(R{val:g})")
            else:
                texts.append(f"({val:g})")
                
        elif mode == 'basic_dim':
            # 模式 4: 基础尺寸 10.89
            val = round(random.uniform(0.1, 1000), 2)
            texts.append(f"{val:g}")

    with open("engineering_mix.txt", "w", encoding="utf-8") as f:
        for t in texts:
            f.write(t + "\n")

generate_engineering_all_styles(20000)
print("混合语料已生成至 engineering_mix.txt")