"""
Setup script for QuantFlow
Run this script to install dependencies and initialize the system
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    print("🚀 QuantFlow Setup")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    if sys.prefix == sys.base_prefix:
        print("⚠️  Warning: Not in a virtual environment")
        print("   It's recommended to use a virtual environment")
        print("   Run: python -m venv .venv && .venv\\Scripts\\activate")
        response = input("   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    else:
        print("✅ Virtual environment detected")
    
    # Install dependencies
    print(f"\n📦 Installing dependencies...")
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        print("❌ Failed to install dependencies")
        return
    
    # Create necessary directories
    print(f"\n📁 Creating directories...")
    directories = ['data', 'logs', 'results']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   Created: {directory}/")
    
    # Check .env file
    print(f"\n⚙️  Checking configuration...")
    if not os.path.exists('.env'):
        print("   Creating .env file from template...")
        with open('.env.example', 'r') as src, open('.env', 'w') as dst:
            dst.write(src.read())
        print("   ✅ Created .env file")
        print("   📝 Please edit .env file with your API keys")
    else:
        print("   ✅ .env file already exists")
    
    # Test basic functionality
    print(f"\n🧪 Testing basic functionality...")
    test_script = """
import asyncio
from src.engine import QuantFlowEngine

async def test():
    try:
        engine = QuantFlowEngine()
        print("✅ Engine initialization successful")
        
        # Test data provider
        prices = await engine.get_real_time_prices(['AAPL'])
        if prices:
            print(f"✅ Data provider working: AAPL = ${prices['AAPL']:.2f}")
        else:
            print("⚠️  Data provider returned no data")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test())
"""
    
    with open('test_setup.py', 'w') as f:
        f.write(test_script)
    
    if run_command("python test_setup.py", "Running functionality test"):
        os.remove('test_setup.py')
        
        print(f"\n🎉 Setup completed successfully!")
        print(f"=" * 50)
        print(f"📚 Next steps:")
        print(f"   1. Edit .env file with your API keys (optional)")
        print(f"   2. Try the examples:")
        print(f"      python examples/example_1_data_analysis.py")
        print(f"      python examples/example_2_backtest.py")
        print(f"      python examples/example_3_paper_trading.py")
        print(f"   3. Use the CLI:")
        print(f"      python main.py --help")
        print(f"      python main.py backtest -s AAPL MSFT")
        print(f"      python main.py paper-trade -s AAPL -t 10")
        print(f"\n🔗 Resources:")
        print(f"   • Alpha Vantage API: https://www.alphavantage.co/support/#api-key")
        print(f"   • Documentation: docs/")
        print(f"   • Examples: examples/")
    else:
        os.remove('test_setup.py')
        print(f"\n❌ Setup test failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
