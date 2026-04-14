with open(r'requirements.txt', 'r') as f:
    lines = f.readlines()

# Hapus duplikat, keep yang ada versi
seen = {}
result = []
for line in lines:
    pkg = line.split(r'==')[0].strip()
    if pkg not in seen:
        seen[pkg] = line
        result.append(line)
    elif r'==' in line:
        idx = result.index(seen[pkg])
        result[idx] = line
        seen[pkg] = line

with open(r'requirements.txt', 'w') as f:
    f.writelines(result)

print("Done!")
