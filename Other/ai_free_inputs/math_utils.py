import numpy as np
from scipy import stats


def perform_statistics():
    observations = np.random.normal(loc=10, scale=2, size=100)

    mean = np.mean(observations)
    std_dev = np.std(observations)
    skewness = stats.skew(observations)

    print("Statistical Summary of Normal Distribution:")
    print(f"Mean: {mean:.4f}")
    print(f"Standard Deviation: {std_dev:.4f}")
    print(f"Skewness: {skewness:.4f}")


if __name__ == "__main__":
    perform_statistics()
