import os

filepath = "frontend/views/counterfactual_view.py"

with open(filepath, "r") as f:
    lines = f.readlines()

new_lines = []
# Keep first 91 lines (index 0 to 90) unchanged
for i in range(91):
    new_lines.append(lines[i])

# Un-indent lines 92 to 276 (index 91 to 275) by 8 spaces
for i in range(91, 276):
    line = lines[i]
    if line.startswith("            "):
        new_lines.append(line[8:])
    elif line.strip() == "":
        new_lines.append("\n")
    else:
        # Fallback if line has fewer spaces
        new_lines.append(line.lstrip())

# Write back
with open(filepath, "w") as f:
    f.writelines(new_lines)

print("Indentation fixed successfully.")
