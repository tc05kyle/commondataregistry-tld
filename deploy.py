"""Production deployment script for Data Registry Platform"""
import os
import sys
import subprocess
from database.production_setup import setup_production_database, get_database_status

def deploy_to_production():
    """Deploy application to production environment"""
    print("🚀 Starting Data Registry Platform deployment...")
    
    # Check environment
    print("📋 Checking environment...")
    required_env_vars = ['DATABASE_URL', 'SENDGRID_API_KEY']
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before deployment.")
        return False
    
    # Setup database
    print("🗄️  Setting up database...")
    db_status = get_database_status()
    print(f"Database status: {db_status['status']} ({db_status['type']})")
    
    if db_status['status'] == 'disconnected':
        print("Setting up production database...")
        if not setup_production_database():
            print("❌ Database setup failed")
            return False
    
    # Create required directories
    print("📁 Creating required directories...")
    directories = ['static/css', 'static/js', 'static/images', 'logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✓ {directory}")
    
    # Check static files
    print("🎨 Checking static files...")
    static_files = [
        'static/css/styles.css',
        'static/js/main.js', 
        'static/images/logo.svg'
    ]
    
    for file_path in static_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ⚠️  {file_path} not found")
    
    # Run Streamlit with production settings
    print("🌐 Starting Streamlit server...")
    try:
        # Set production environment variables
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        os.environ['STREAMLIT_SERVER_PORT'] = '5000'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        
        print("✅ Deployment completed successfully!")
        print("🔗 Application available at: http://0.0.0.0:5000")
        
        # Start the application
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'app.py',
            '--server.port', '5000',
            '--server.address', '0.0.0.0',
            '--server.headless', 'true'
        ])
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

def check_deployment_health():
    """Check deployment health status"""
    print("🔍 Checking deployment health...")
    
    # Check database
    db_status = get_database_status()
    print(f"Database: {db_status['status']}")
    
    # Check required files
    required_files = ['app.py', '.streamlit/config.toml']
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"❌ {file_path} missing")
    
    # Check environment variables
    env_vars = ['DATABASE_URL', 'SENDGRID_API_KEY']
    for var in env_vars:
        if os.getenv(var):
            print(f"✓ {var} configured")
        else:
            print(f"❌ {var} missing")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "health":
        check_deployment_health()
    else:
        deploy_to_production()