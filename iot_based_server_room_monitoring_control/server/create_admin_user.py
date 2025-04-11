# iot_based_server_room_monitoring_control/server/create_admin_user.py
import os
import sys
import logging

# Add the directory *containing* the 'iot_based_server_room_monitoring_control' package to sys.path
# This allows imports like 'from iot_based_server_room_monitoring_control...'
script_dir = os.path.dirname(os.path.abspath(__file__)) # .../server
project_dir = os.path.dirname(script_dir) # .../iot_based_server_room_monitoring_control
workspace_root = os.path.dirname(project_dir) # /home/admin/iot_project_server_room_security
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

# Now import necessary components from the server app
# It's important that these imports happen *after* modifying sys.path
try:
    from iot_based_server_room_monitoring_control.server.app.database import SessionLocal, engine, Base
    from iot_based_server_room_monitoring_control.server.app.models import User
    from iot_based_server_room_monitoring_control.server.app.auth import get_password_hash
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error importing server modules: {e}")
    print("Please ensure you run this script from a location where Python can find the 'iot_based_server_room_monitoring_control' package.")
    print(f"Current working directory: {os.getcwd()}")
    print(f"sys.path includes: {sys.path}") # Added for debugging
    sys.exit(1)

# Configure basic logging for the script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables (might be needed for database connection string etc.)
# Assuming .env is in workspace_root
env_path = os.path.join(workspace_root, '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    # Look for .env in the original project_root as well, just in case
    original_project_root_env_path = os.path.join(project_dir, '.env')
    if os.path.exists(original_project_root_env_path):
        load_dotenv(dotenv_path=original_project_root_env_path)
        logger.info(f"Loaded environment variables from {original_project_root_env_path}")
    else:
        logger.warning(f".env file not found at {env_path} or {original_project_root_env_path}")

# --- User Details ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123" # Choose a secure password in production
ADMIN_EMAIL = "admin@example.com"
# --- ---

def create_admin():
    logger.info("Attempting to create admin user...")
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if existing_user:
            logger.warning(f"User '{ADMIN_USERNAME}' already exists. Skipping creation.")
            return

        # Create the user if they don't exist
        hashed_password = get_password_hash(ADMIN_PASSWORD)
        admin_user = User(
            username=ADMIN_USERNAME,
            hashed_password=hashed_password,
            email=ADMIN_EMAIL,
            is_active=True,
            is_admin=True, # Make this user an admin
            role='Admin' # Explicitly set the role string
        )
        db.add(admin_user)
        db.commit()
        logger.info(f"Admin user '{ADMIN_USERNAME}' created successfully.")

    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        db.rollback()
    finally:
        db.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    # Optional: Ensure tables exist (though main app startup should handle this)
    # try:
    #     logger.info("Ensuring database tables exist...")
    #     Base.metadata.create_all(bind=engine)
    # except Exception as e:
    #     logger.error(f"Could not ensure tables exist: {e}")
    #     # Decide if you want to exit if tables can't be created
    #     # sys.exit(1)

    create_admin() 