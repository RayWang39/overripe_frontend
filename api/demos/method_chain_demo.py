#!/usr/bin/env python3
"""
IYP Method Chain Translation API Demo

This script demonstrates the method chain translation API that converts
method chains like '.find.with_organizations.upstream' into Cypher queries.

Perfect for integration into systems that need programmatic Cypher generation!
"""

import requests
import json
from typing import Dict, Any

# API Configuration  
API_BASE = "http://localhost:8001"

# Colors for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.END}")

def print_cypher(cypher: str, params: Dict[str, Any] = None):
    """Print Cypher query with syntax highlighting"""
    print(f"{Colors.BOLD}📝 Generated Cypher:{Colors.END}")
    print(f"{Colors.BLUE}{cypher}{Colors.END}")
    if params:
        print(f"{Colors.BOLD}🔧 Parameters:{Colors.END}")
        print(f"{Colors.YELLOW}{json.dumps(params, indent=2)}{Colors.END}")

def demo_method_chains():
    """Demo various method chain translations"""
    print_header("Method Chain Translation Examples")
    
    examples = [
        {
            "name": "Basic AS Lookup",
            "chain": ".find",
            "params": {"asn": 15169},
            "description": "Find a specific AS by number"
        },
        {
            "name": "AS with Organization",
            "chain": ".find.with_organizations",
            "params": {"asn": 15169},
            "description": "Get AS details including managing organization"
        },
        {
            "name": "Upstream Providers",
            "chain": ".find.upstream",
            "params": {"asn": 216139, "hops": 2},
            "description": "Find upstream providers up to 2 hops away"
        },
        {
            "name": "Complex Chain",
            "chain": ".find.with_organizations.upstream.limit",
            "params": {"asn": 15169, "hops": 1, "limit": 5},
            "description": "AS with org, upstream providers, limited results"
        },
        {
            "name": "Peering Partners",
            "chain": ".find.peers.limit",
            "params": {"asn": 3356, "limit": 10},
            "description": "Find AS peering partners with limit"
        },
        {
            "name": "Custom Relationship",
            "chain": ".find.with_relationship",
            "params": {"asn": 15169, "relationship": "COUNTRY", "to": "Country"},
            "description": "Find AS with country relationship"
        }
    ]
    
    for example in examples:
        print(f"{Colors.BOLD}📌 {example['name']}{Colors.END}")
        print(f"   Description: {example['description']}")
        print(f"   Chain: {Colors.YELLOW}{example['chain']}{Colors.END}")
        print(f"   Parameters: {json.dumps(example['params'])}")
        
        try:
            response = requests.post(
                f"{API_BASE}/api/v1/translate/method-chain",
                json={
                    "method_chain": example["chain"],
                    "parameters": example["params"]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    print_success(f"Translation: {data.get('method_chain', 'N/A')}")
                    print_cypher(data["cypher"], data.get("parameters"))
                    if data.get("explanation"):
                        print(f"   💡 {data['explanation']}")
                else:
                    print(f"   ❌ {data.get('error', 'Translation failed')}")
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        print("-" * 60)

def demo_available_methods():
    """Show available methods"""
    print_header("Available Methods for Chaining")
    
    try:
        response = requests.get(f"{API_BASE}/api/v1/translate/help")
        
        if response.status_code == 200:
            data = response.json()
            
            methods = data.get("available_methods", {})
            
            for method_name, info in methods.items():
                print(f"\n{Colors.BOLD}.{method_name}{Colors.END}")
                print(f"  📝 {info['description']}")
                print(f"  🔧 Parameters: {Colors.YELLOW}{', '.join(info['parameters']) if info['parameters'] else 'none'}{Colors.END}")
                print(f"  💡 Example: {Colors.BLUE}{info['example']}{Colors.END}")
                
        else:
            print(f"❌ Failed to get help: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting help: {e}")

def demo_integration_pattern():
    """Show integration pattern for web servers"""
    print_header("Web Server Integration Pattern")
    
    print_info("Your colleague can integrate this API easily:")
    print()
    
    integration_code = '''// JavaScript/Node.js Example
async function translateMethodChain(chain, params) {
    const response = await fetch('http://your-api-host:8001/api/v1/translate/method-chain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            method_chain: chain,     // e.g., ".find.upstream.limit"
            parameters: params        // e.g., {asn: 15169, hops: 2, limit: 10}
        })
    });
    
    const result = await response.json();
    
    if (result.success) {
        // Use the generated Cypher with your Neo4j driver
        const session = neo4jDriver.session();
        const queryResult = await session.run(result.cypher, result.parameters);
        session.close();
        return queryResult.records;
    } else {
        throw new Error(result.error);
    }
}

// Usage example
const cypher = await translateMethodChain('.find.with_organizations', {asn: 15169});'''
    
    print(f"{Colors.BLUE}{integration_code}{Colors.END}")
    
    print()
    print_success("Benefits of this approach:")
    print("  ✓ No need to understand Cypher query language")
    print("  ✓ Consistent, optimized query generation")
    print("  ✓ Parameters are properly escaped (injection safe)")
    print("  ✓ Easy to chain complex operations")
    print("  ✓ Get explanations of what each query does")

def main():
    """Run method chain translation demo"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("🔄 IYP Method Chain Translation API")
    print("====================================")
    print("Convert Method Chains to Cypher Queries")
    print(f"API Server: {API_BASE}{Colors.END}\n")
    
    # Check if API is available
    try:
        response = requests.get(f"{API_BASE}/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("database_connected"):
                print_success("API is running and database is connected!")
            else:
                print("⚠️  API is running but database is not connected")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print_info("Make sure the server is running: cd api && python -m uvicorn main:app --port 8001")
        return
    
    # Run demonstrations
    demo_method_chains()
    demo_available_methods()
    demo_integration_pattern()
    
    print_header("Method Chain API Ready!")
    print_success("🎯 Perfect for programmatic Cypher generation!")
    print()
    print(f"{Colors.BOLD}📍 Key Endpoints:{Colors.END}")
    print(f"  POST /api/v1/translate/method-chain - Translate method chains")
    print(f"  GET  /api/v1/translate/help - Get available methods")
    print(f"  GET  /api/v1/translate/examples - Get example translations")
    print()
    print(f"🌐 Interactive test interface: {API_BASE}/")
    print(f"📚 API documentation: {API_BASE}/docs")

if __name__ == "__main__":
    main()