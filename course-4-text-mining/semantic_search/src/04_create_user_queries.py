import pandas as pd
import os

def create_user_queries():
    """Create a dataset of realistic user queries for popular datasets"""
    
    user_queries = [
        # Generic terms that need specificity
        "steel",
        "copper", 
        "aluminum",
        "plastic",
        "electricity",
        "diesel",
        "natural gas",
        "concrete",
        "glass",
        "paper",
        
        # Common user language vs technical terms
        "gasoline",           # → petrol
        "aluminum sheets",    # → sheet rolling, aluminium
        "car fuel",          # → petrol, diesel
        "building materials", # → concrete, steel, etc.
        "fossil fuels",      # → coal, oil, gas variants
        "metals",            # → specific metal types
    ]
    
    # Create DataFrame
    df = pd.DataFrame({
        'query': user_queries,
        'category': ['generic'] * 10 + ['vocabulary_gap'] * 6,
        'expected_results': ['multiple_specific_variants'] * len(user_queries)
    })
    
    # Save to CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    output_path = os.path.join(project_dir, 'data', 'processed', 'user_queries.csv')
    
    df.to_csv(output_path, index=False)
    print(f"Created {len(user_queries)} test queries")
    print(f"Saved to: {output_path}")
    
    return df

if __name__ == "__main__":
    create_user_queries()