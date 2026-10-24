import pandas as pd
import os
import sys

# Add the src directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from semantic_matching import ProductMatcher

def evaluate_queries():
    """Run evaluation on all test queries and save results"""
    
    # Load test queries
    project_dir = os.path.dirname(script_dir)
    queries_path = os.path.join(project_dir, 'data', 'processed', 'user_queries.csv')
    
    if not os.path.exists(queries_path):
        print("Creating user queries first...")
        # Run the create_user_queries function
        exec(open(os.path.join(script_dir, '04_create_user_queries.py')).read())
    
    queries_df = pd.read_csv(queries_path)
    print(f"Loaded {len(queries_df)} test queries")
    
    # Initialize matcher
    print("Initializing semantic matcher...")
    matcher = ProductMatcher()
    matcher.load_data()
    matcher.create_embeddings()
    
    # Run evaluation
    all_results = []
    
    for _, row in queries_df.iterrows():
        query = row['query']
        print(f"Processing: {query}")
        
        matches = matcher.find_matches(query, top_k=5)
        
        for i, match in enumerate(matches):
            all_results.append({
                'query': query,
                'rank': i + 1,
                'product_name': match['product_name'],
                'similarity': match['similarity'],
                'category': row['category']
            })
    
    # Save results
    results_df = pd.DataFrame(all_results)
    output_path = os.path.join(project_dir, 'data', 'output', 'results.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    results_df.to_csv(output_path, index=False)
    print(f"Saved evaluation results to: {output_path}")
    
    # Show summary statistics
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    
    avg_similarity = results_df[results_df['rank'] == 1]['similarity'].mean()
    print(f"Average similarity for top matches: {avg_similarity:.3f}")
    
    by_category = results_df[results_df['rank'] == 1].groupby('category')['similarity'].mean()
    print("\nAverage similarity by category:")
    for category, sim in by_category.items():
        print(f"  {category}: {sim:.3f}")
    
    return results_df

if __name__ == "__main__":
    evaluate_queries()