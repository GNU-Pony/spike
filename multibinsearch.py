#!/usr/bin/env python3

list = [c for c in range(100)]
items = [10, 20, 30, 40, 50, 60, 70, 80]

def binsearch(list, item, min, max):
    mid = 0
    while min <= max:
        mid = (min + max) >> 1
        elem = list[mid]
        if elem == item:
            return mid
        elif elem > item:
            max = mid - 1
        else:
            mid += 1
            min = mid
    return ~mid

count = len(items)
if count > 0:
    minomax = [(0, count - 1, 0, len(list) - 1)]
    while len(minomax) > 0:
        (min, max, lmin, lmax) = minomax.pop()
        while max != min:
            (lastmax, lastlmax) = (max, lmax)
            max = min + ((max - min) >> 1)
            lmax = binsearch(list, items[max], lmin, lmax)
            print(str('-' if lmax < 0 else list[lmax]), end=' ')
            if lmax < 0:
                lmax = ~lmax
            minomax.append((max + 1, lastmax, lmax + 1, lastlmax))
    max = count - 1
    lmax = binsearch(list, items[max], lmin, lmax)
    print(str('-' if lmax < 0 else list[lmax]))

