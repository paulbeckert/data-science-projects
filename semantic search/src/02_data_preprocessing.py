import pandas as pd
import os

def clean_product_data():
    """Clean and prepare product data for semantic matching"""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    # Load the extracted data
    csv_path = os.path.join(project_dir, 'data', 'processed', 'product_data.csv')
    if not os.path.exists(csv_path):
        print(f"Error: Run 01_data_extraction.py first - file not found at {csv_path}")
        return None
    
    try:
        print("Loading product data...")
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} products")
        
        # Check for missing data
        print(f"Products with missing names: {df['Name'].isna().sum()}")
        print(f"Products with missing Product Information: {df['Product Information'].isna().sum()}")
        
        # Remove rows with missing Product Information (critical for matching)
        df_clean = df.dropna(subset=['Product Information']).copy()
        print(f"After removing missing descriptions: {len(df_clean)} products")
        
        # Create combined descriptions for better matching
        df_clean['combined_description'] = df_clean['Name'] + ': ' + df_clean['Product Information']
        
        # Show some examples
        print("\nFirst 3 combined descriptions:")
        for i, desc in enumerate(df_clean['combined_description'].head(3)):
            print(f"{i+1}. {desc[:100]}...")
        
        # Save cleaned data
        output_path = os.path.join(project_dir, 'data', 'processed', 'product_data_clean.csv')
        df_clean.to_csv(output_path, index=False)
        print(f"\nSaved cleaned data to product_data_clean.csv")
        
        return df_clean
        
    except Exception as e:
        print(f"Error processing data: {e}")
        return None

if __name__ == "__main__":
    clean_product_data()