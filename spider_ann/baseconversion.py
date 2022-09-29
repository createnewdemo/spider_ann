import struct

a = open("test.txt","r")#十六进制数据文件
lines = a.read()
res = [lines[i:i+2] for i in range(0,len(lines),2)]

with open("1.jpg","wb") as f:
	for i in res:
		s = struct.pack('B',int(i,16))
		f.write(s)
