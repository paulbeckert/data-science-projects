import pandas as pd
import os

def extract_product_data():
    """Extract product data from Excel file"""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)  # Go up one level from src/
    
    # Build the correct path
    excel_path = os.path.join(project_dir, 'data', 'raw', 'Database-Overview-for-ecoinvent-v3.11.xlsx')
    
    print(f"Looking for file at: {excel_path}")
    
    if not os.path.exists(excel_path):
        print(f"Error: File not found at {excel_path}")
        return None
    
    try:
        # Load the Excel file
        print("Loading Excel file...")
        df = pd.read_excel(excel_path, sheet_name='Intermediate Exchanges')
        print(f"Loaded {len(df)} rows from Excel")
        
        # Check available columns
        print(f"Available columns: {df.columns.tolist()}")
        
        # Extract relevant columns
        if 'Name' in df.columns and 'Product Information' in df.columns:
            product_data = df[['Name', 'Product Information']].copy()
            
            # Create output directory if it doesn't exist
            processed_dir = os.path.join(project_dir, 'data', 'processed')
            os.makedirs(processed_dir, exist_ok=True)
            
            # Save to CSV for faster loading
            output_path = os.path.join(processed_dir, 'product_data.csv')
            product_data.to_csv(output_path, index=False)
            print(f"Saved {len(product_data)} products to CSV")
            
            return product_data
        else:
            print("Error: Required columns not found")
            return None
            
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return None

if __name__ == "__main__":
    extract_product_data()