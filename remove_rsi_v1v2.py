with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# RSI > 50 bloğunu bul ve sil (satır 224-318 arası)
new_lines = []
skip = False
for i, line in enumerate(lines):
    # RSI > 50 bloğu başlangıcı
    if 'elif strategy_mode == "RSI > 50 Stratejisi"' in line:
        skip = True
    # RSI V3 bloğu başlangıcı (RSI > 50 bloğu sonu)
    elif skip and 'elif strategy_mode == "RSI V3' in line:
        skip = False
    
    if not skip:
        new_lines.append(line)

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("RSI V1-V2 bloğu başarıyla kaldırıldı!")
