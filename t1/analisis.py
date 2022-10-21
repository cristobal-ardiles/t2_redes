from contextlib import redirect_stdout
import sys
import numpy
import io
import matplotlib.pyplot as plt

proposed = numpy.linspace(1,9999,endpoint=True,num=50,dtype=int)
bandwidth_list = {"500b":[],"1kb":[],"10kb":[],"1mb":[]}

for size in proposed:
    for f_size in list(bandwidth_list.keys()): 
       with redirect_stdout(io.StringIO()) as f:
            sys.argv = ["bwc.py", str(size), f_size, f_size+".o", "anakena.dcc.uchile.cl", "1818"]
            exec(open("bwc.py").read())
            s = f.getvalue()
            bandwidth_list[f_size].append(float(s.strip())/(1024*1024))

plt.plot(proposed,bandwidth_list)
plt.savefig("fig1")
plt.show()