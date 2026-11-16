import sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
old = 'expected_path = "/code/revizor-docker/src"'
new = 'expected_path = os.getcwd()'
assert s.count(old) == 1, old
open(dst, "w").write(s.replace(old, new))
print(f"wrote {dst}")
