
s = '蠎苓・逋ｻ骭ｲ'
print(f"Original: {s}")
try:
    # Try encode to cp932 then decode as utf-8
    b = s.encode('cp932')
    print(f"Bytes (CP932): {b.hex(' ')}")
    r = b.decode('utf-8')
    print(f"Decoded (UTF-8): {r}")
except Exception as e:
    print(f"Error: {e}")

s2 = '繧ｿ繧､繝溘・'
print(f"Original 2: {s2}")
try:
    b2 = s2.encode('cp932')
    print(f"Bytes 2 (CP932): {b2.hex(' ')}")
    r2 = b2.decode('utf-8')
    print(f"Decoded 2 (UTF-8): {r2}")
except Exception as e:
    print(f"Error 2: {e}")
