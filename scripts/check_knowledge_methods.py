"""Check what methods Knowledge object actually has"""
from my_os import knowledge

print("\n🔍 Knowledge object methods:\n")

methods = [m for m in dir(knowledge) if not m.startswith('_')]
for method in sorted(methods):
    print(f"  - {method}")

print(f"\n📊 Total methods: {len(methods)}")

# Check for load-related methods
print("\n🔎 Load-related methods:")
load_methods = [m for m in methods if 'load' in m.lower()]
if load_methods:
    for m in load_methods:
        print(f"  ✅ {m}")
else:
    print("  ❌ No load methods found")

# Check for create-related methods
print("\n🔎 Create-related methods:")
create_methods = [m for m in methods if 'create' in m.lower()]
if create_methods:
    for m in create_methods:
        print(f"  ✅ {m}")
else:
    print("  ❌ No create methods found")
