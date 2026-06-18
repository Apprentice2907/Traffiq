import pandas as pd

def explore_data(file_path):
    print("Loading data from", file_path, "...")
    df = pd.read_csv(file_path)
    
    print("\n--- SHAPE ---")
    print(df.shape)
    
    print("\n--- COLUMNS ---")
    print(df.columns.tolist())
    
    print("\n--- DTYPES ---")
    print(df.dtypes)
    
    print("\n--- FIRST 3 ROWS ---")
    print(df.head(3))
    
    print("\n--- NULL COUNTS ---")
    print(df.isnull().sum())
    
    print("\n--- UNIQUE VALUE COUNTS ---")
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['violation', 'type', 'category', 'status']):
            print(f"\nValue counts for '{col}':")
            print(df[col].value_counts())

if __name__ == "__main__":
    explore_data('data.csv')
