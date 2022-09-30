
def trial(n):
    sum_ = 0
    for i in range(n):
        sum_ += np.random.randint(1, 7)
        if sum_ == n:
            return True
    return False

results = []
for i in range(10000):
    results.append(trial(1000))
print(np.mean(results))
