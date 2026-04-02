with open('requirements.txt', 'r') as f:
    lines = f.readlines()

# Hapus duplikat, keep yang ada versi
seen = {}
result = []
for line in lines:
    pkg = line.split('==')[0].strip()
    if pkg not in seen:
        seen[pkg] = line
        result.append(line)
    elif '==' in line:
        idx = result.index(seen[pkg])
        result[idx] = line
        seen[pkg] = line

with open('requirements.txt', 'w') as f:
    f.writelines(result)

print("Done!")
