import time
import os
import sys
import random
import gmpy2
from gmpy2 import mpz
from functools import lru_cache
from multiprocessing import Pool, cpu_count

modulo = gmpy2.mpz(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F)
order = gmpy2.mpz(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141)
Gx = gmpy2.mpz(0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798)
Gy = gmpy2.mpz(0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)

class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

PG = Point(Gx, Gy)
Z = Point(0, 0)  # zero-point, infinite in real x,y-plane

def mul2(P, p=modulo):
    c = (3 * P.x * P.x * pow(2 * P.y, -1, p)) % p
    R = Point()
    R.x = (c * c - 2 * P.x) % p
    R.y = (c * (P.x - R.x) - P.y) % p
    return R

def add(P, Q, p=modulo):
    dx = Q.x - P.x
    dy = Q.y - P.y
    c = dy * gmpy2.invert(dx, p) % p
    R = Point()
    R.x = (c * c - P.x - Q.x) % p
    R.y = (c * (P.x - R.x) - P.y) % p
    return R

@lru_cache(maxsize=None)
def X2Y(X, y_parity, p=modulo):
    Y = 3
    tmp = 1
    while Y:
        if Y & 1:
            tmp = tmp * X % p
        Y >>= 1
        X = X * X % p

    X = (tmp + 7) % p

    Y = (p + 1) // 4
    tmp = 1
    while Y:
        if Y & 1:
            tmp = tmp * X % p
        Y >>= 1
        X = X * X % p

    Y = tmp

    if Y % 2 != y_parity:
        Y = -Y % p

    return Y

def compute_P_table():
    P = [PG]
    for k in range(255):
        P.append(mul2(P[k]))
    return P

P = compute_P_table()

os.system('clear')
t = time.ctime()
sys.stdout.write("\033[01;33m")
sys.stdout.write(t + "\n")
sys.stdout.write("P-table prepared" + "\n")
sys.stdout.write("tame and wild herds is being prepared" + "\n")
sys.stdout.flush()

def comparator(A, Ak, B, Bk):
    result = set(A).intersection(set(B))
    if result:
        sol_kt = A.index(next(iter(result)))
        sol_kw = B.index(next(iter(result)))
        print('total time: %.2f sec' % (time.time() - starttime))
        difference = Ak[sol_kt] - Bk[sol_kw]
        HEX = "%064x" % difference  # Convert to a hexadecimal string
        t = time.ctime()
        print('SOLVED:', t, difference)
        with open("KEYFOUNDKEYFOUND.txt", 'a') as file:
            file.write('\n\nSOLVED ' + t)
            file.write('\nPrivate Key (decimal): ' + str(difference))
            file.write('\nPrivate Key (hex): ' + HEX)
            file.write('\n-------------------------------------------------------------------------------------------------------------------------------------\n')
        return True
    else:
        return False

def check(P, Pindex, DP_rarity, file2save, A, Ak, B, Bk):
    if P.x % DP_rarity == 0:
        A.append(P.x)
        Ak.append(Pindex)
        with open(file2save, 'a') as file:
            file.write(('%064x %d' % (P.x, Pindex)) + "\n")
        # Print the public key
        message = "\rPublic key: {:064x}".format(P.x)
        sys.stdout.write("\033[01;33m")
        sys.stdout.write(message)
        sys.stdout.flush()
        return comparator(A, Ak, B, Bk)
    else:
        return False

# Memoization for ecmultiply
ecmultiply_memo = {}

def ecmultiply(k, P=PG, p=modulo):
    if k == 0:
        return Z
    elif k == 1:
        return P
    elif k % 2 == 0:
        if k in ecmultiply_memo:
            return ecmultiply_memo[k]
        else:
            result = ecmultiply(k // 2, mul2(P, p), p)
            ecmultiply_memo[k] = result
            return result
    else:
        return add(P, ecmultiply((k - 1) // 2, mul2(P, p), p))

def mulk(k, P=PG, p=modulo):
    if k == 0:
        return Z
    elif k == 1:
        return P
    elif k % 2 == 0:
        return mulk(k // 2, mul2(P, p), p)
    else:
        return add(P, mulk((k - 1) // 2, mul2(P, p), p))

def search(Nt, Nw, puzzle, kangoo_power, starttime):
    DP_rarity = 1 << ((puzzle - 2 * kangoo_power) // 2 - 2)
    hop_modulo = ((puzzle - 1) // 2) + kangoo_power
    T, t, dt = [], [], []
    W, w, dw = [], [], []
    for k in range(Nt):
        t.append((3 << (puzzle - 2)) + random.randint(1, (1 << (puzzle - 1))))
        T.append(mulk(t[k]))
        dt.append(0)
    for k in range(Nw):
        w.append(random.randint(1, (1 << (puzzle - 1))))
        W.append(add(W0, mulk(w[k])))
        dw.append(0)
    oldtime = time.time()
    Hops, Hops_old = 0, 0
    t0 = time.time()
    oldtime = time.time()
    starttime = oldtime
    while True:
        for k in range(Nt):
            Hops += 1
            pw = T[k].x % hop_modulo
            dt[k] = 1 << pw
            solved = check(T[k], t[k], DP_rarity, "tame.txt", T, t, W, w)
            if solved:
                return 'sol. time: %.2f sec' % (time.time() - starttime)
            t[k] += dt[k]
            T[k] = add(P[pw], T[k])
        for k in range(Nw):
            Hops += 1
            pw = W[k].x % hop_modulo
            dw[k] = 1 << pw
            solved = check(W[k], w[k], DP_rarity, "wild.txt", W, w, T, t)
            if solved:
                return 'sol. time: %.2f sec' % (time.time() - starttime)
            w[k] += dw[k]
            W[k] = add(P[pw], W[k])

puzzle = 32
compressed_public_key = "037fcaac9d3dcbf73c0a6c6e7a5451dca03fe30fc3302247492af92caf26941ec6"  # Puzzle 130
kangoo_power = 8 #For Puzzle 50-56 use 9 to 11, for Puzzle 60-80 use 14 to 16 / 24 cores or above preferred
Nt = Nw = 2 ** kangoo_power
X = int(compressed_public_key, 16)
Y = X2Y(X % (2 ** 256), X >> 256)
if Y % 2 != (X >> 256) % 2:
    Y = modulo - Y
X = X % (2 ** 256)
W0 = Point(X, Y)
starttime = oldtime = time.time()

Hops = 0
random.seed()

hops_list = []
N_tests = kangoo_power

for k in range(N_tests):
    buffer_size = 1024 * 1024 * 1024  # 1024 MB in bytes
    with open("tame.txt", 'w', buffering=buffer_size) as tame_file, open("wild.txt", 'w', buffering=buffer_size) as wild_file:
        tame_file.write('')
        wild_file.write('')

def parallel_search(process_count, Nt, Nw, puzzle, kangoo_power, starttime):
    pool = Pool(process_count)
    results = pool.starmap(search, [(Nt, Nw, puzzle, kangoo_power, starttime)] * process_count)
    pool.close()
    pool.join()
    return results

if __name__ == '__main__':
    process_count = cpu_count()  # Use all available CPU cores
    print(f"Using {process_count} CPU cores for parallel search.")
    results = parallel_search(process_count, Nt, Nw, puzzle, kangoo_power, starttime)
    for result in results:
        print(result)