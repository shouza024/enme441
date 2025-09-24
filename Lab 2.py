# Problem 1
def between(x:float ,lower:float = 0.0,upper:float=0.3):
    if x > lower and x < upper: return True   #
    else: return False


# Problem 2
def rangef(max:float | int,step:float | int):
    n =0
    while n <= max:
        yield n
        n = n + step

for i in rangef(5,0.5): print(i, end=' ')
print()

# Problem 3a
alist = list(rangef(1,0.25))
print(alist)
a = alist[::-1] #copy from start to end alist but with negative steps(or backwards)
alist.extend(a)
print(alist)

# Problem 3b
alist.sort(key=between)
print(alist)

# Problem 4
the_list = [val for val in range(0,17,1) if (val%2) == 0 or (val%3)==0]
print(the_list)



