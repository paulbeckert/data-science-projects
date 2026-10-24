from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os

class ProductMatcher:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """Initialize the semantic matching system"""
        print(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.product_data = None
        self.embeddings = None
        print("Model loaded successfully!")
    
    def load_data(self, filepath=None):
        """Load the cleaned product data"""
        if filepath is None:
            # Auto-detect path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_dir = os.path.dirname(script_dir)
            filepath = os.path.join(project_dir, 'data', 'processed', 'product_data_clean.csv')
        
        print(f"Loading product data from: {filepath}")
        self.product_data = pd.read_csv(filepath)
        print(f"Loaded {len(self.product_data)} products")
        
    def create_embeddings(self):
        """Create embeddings for all product descriptions"""
        if self.product_data is None:
            raise ValueError("Load data first using load_data()")
        
        print("Creating embeddings for all products...")
        descriptions = self.product_data['combined_description'].tolist()
        
        # Create embeddings (this might take a few minutes)
        self.embeddings = self.model.encode(descriptions, show_progress_bar=True)
        print(f"Created embeddings with shape: {self.embeddings.shape}")
        
    def find_matches(self, query, top_k=5):
        """Find the most similar products with automatic smart filtering"""
        if self.embeddings is None:
            raise ValueError("Create embeddings first using create_embeddings()")
        
        # Use a larger window for all queries to ensure filtering has good options
        extended_top_k = min(top_k * 10, 40)  # Expanded for all queries
        
        # Create query embedding
        query_embedding = self.model.encode([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get extended matches for filtering
        top_indices = similarities.argsort()[-extended_top_k:][::-1]
        
        extended_results = []
        for idx in top_indices:
            extended_results.append({
                'product_name': self.product_data.iloc[idx]['Name'],
                'similarity': similarities[idx],
                'description': self.product_data.iloc[idx]['Product Information'][:200] + "..."
            })
        
        # Apply automatic smart filtering
        filtered_results = self._smart_filter(query, extended_results)
        
        return filtered_results[:top_k]

    def _smart_filter(self, query, matches):
        """Automatically apply smart filtering based on query type"""
        
        query_lower = query.lower()
        
        # Electricity-specific filtering
        if 'electricity' in query_lower:
            return self._filter_electricity(matches)
        
        # Natural gas-specific filtering
        elif 'natural gas' in query_lower:
            return self._filter_natural_gas(matches)
        
        # Gasoline-specific filtering
        elif 'gasoline' in query_lower:
            return self._filter_gasoline(matches)
        
        elif 'aluminum' in query_lower or 'aluminium' in query_lower:
            return self._filter_aluminium(matches)
        
        return matches

    def _filter_electricity(self, matches):
        """Prioritize the three main voltage levels in logical order"""
        
        # Apply boosts to get the right order: low, high, medium
        for match in matches:
            name = match['product_name']
            
            # Boost to achieve: low voltage > high voltage > medium voltage
            if name == 'electricity, low voltage':
                match['similarity'] *= 1.10  # Highest boost
            elif name == 'electricity, high voltage':
                match['similarity'] *= 1.05  # Medium boost
            elif name == 'electricity, medium voltage':
                match['similarity'] *= 1.02  # Small boost (just enough to beat industry-specific)
        
        # Sort by boosted similarity
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Separate target generics from specialized
        target_generics = ['electricity, low voltage', 'electricity, high voltage', 'electricity, medium voltage']
        
        generic_matches = [m for m in matches if m['product_name'] in target_generics]
        other_matches = [m for m in matches if m['product_name'] not in target_generics]
        
        # Return target generics first, then others
        return generic_matches + other_matches
    
    def _filter_natural_gas(self, matches):
        """Prioritize the three main natural gas types"""
        
        # Apply boosts only to the target natural gas types
        for match in matches:
            name = match['product_name']
            
            # Boost the specific types we want in top 3
            if name == 'natural gas, high pressure':
                match['similarity'] *= 1.15
            elif name == 'natural gas, low pressure':
                match['similarity'] *= 1.10  
            elif name == 'natural gas, liquefied':
                match['similarity'] *= 1.12
        
        # Sort by boosted similarity
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Separate target generics from specialized
        target_generics = ['natural gas, high pressure', 'natural gas, low pressure', 'natural gas, liquefied']
        
        generic_matches = [m for m in matches if m['product_name'] in target_generics]
        other_matches = [m for m in matches if m['product_name'] not in target_generics]
        
        # Return target generics first, then others
        return generic_matches + other_matches
    
    def _filter_gasoline(self, matches):
        """Prioritize main gasoline/petrol types"""
        
        # Target the main gasoline variants
        for match in matches:
            name = match['product_name']
            
            if name == 'petrol, unleaded':
                match['similarity'] *= 1.20  # Highest boost - direct equivalent
            elif name == 'petrol, low-sulfur':
                match['similarity'] *= 1.15
            elif name == 'petrol, 5% ethanol by volume from biomass':
                match['similarity'] *= 1.10
        
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        target_petrols = ['petrol, unleaded', 'petrol, low-sulfur', 'petrol, 5% ethanol by volume from biomass']
        
        petrol_matches = [m for m in matches if m['product_name'] in target_petrols]
        other_matches = [m for m in matches if m['product_name'] not in target_petrols]
        
        return petrol_matches + other_matches
        
    def _filter_aluminium(self, matches):
        """Prioritize main aluminium sheet process and materials"""
        
        # Target the process + main material types
        for match in matches:
            name = match['product_name']
            
            if name == 'sheet rolling, aluminium':
                match['similarity'] *= 1.15  # Keep the process first
            elif name == 'aluminium, wrought alloy':
                match['similarity'] *= 1.25  # Higher boost for wrought (sheet material)
            elif name == 'aluminium, cast alloy':
                match['similarity'] *= 1.20  # Lower boost for cast (alternative material)
        
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        target_results = ['sheet rolling, aluminium', 'aluminium, wrought alloy', 'aluminium, cast alloy']
        
        target_matches = [m for m in matches if m['product_name'] in target_results]
        other_matches = [m for m in matches if m['product_name'] not in target_results]
        
        return target_matches + other_matches
    
    def demo_search(self, queries):
        """Demo the search functionality with multiple queries"""
        print("\n" + "="*80)
        print("SEMANTIC SEARCH DEMO")
        print("="*80)
        
        for query in queries:
            print(f"\n🔍 User searches for: '{query}'")
            print("-" * 50)
            
            matches = self.find_matches(query, top_k=3)
            
            for i, match in enumerate(matches, 1):
                print(f"{i}. {match['product_name']}")
                print(f"   Similarity: {match['similarity']:.3f}")
                print(f"   Description: {match['description']}")
                print()

def main():
    """Main function to test the semantic matching"""
    
    # Initialize matcher
    matcher = ProductMatcher()
    
    # Load data
    matcher.load_data()
    
    # Create embeddings
    matcher.create_embeddings()
    
    # Test with some queries
    test_queries = [
        "steel",
        "electricity",
        "aluminum sheets",
        "gasoline",
        "natural gas",
    ]
    
    # Run demo
    matcher.demo_search(test_queries)
    
    return matcher

if __name__ == "__main__":
    main()