import pandas as pd
import numpy as np


def generate_and_analyze_data():
    data = {
        "Product": ["Apples", "Oranges", "Bananas", "Pears", "Grapes"],
        "Sales": np.random.randint(100, 500, size=5),
        "Price": [1.2, 0.8, 0.5, 1.5, 2.0],
    }

    df = pd.DataFrame(data)
    df["Revenue"] = df["Sales"] * df["Price"]

    print("Sales Data Analysis:")
    print(df)
    print(f"\nTotal Revenue: ${df['Revenue'].sum():.2f}")
    print(f"Average Sale: {df['Sales'].mean():.1f} units")


if __name__ == "__main__":
    generate_and_analyze_data()
