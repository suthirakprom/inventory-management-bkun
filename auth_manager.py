import bcrypt
from typing import Dict, Optional, List
from datetime import datetime
from data_store import DataStore

class AuthManager:
    # Role Definitions
    ROLE_ADMIN = "Admin"
    ROLE_STAFF = "Staff"
    
    # Permission Definitions
    PERM_ADD_ITEM = "add_item"
    PERM_EDIT_ITEM = "edit_item"
    PERM_DELETE_ITEM = "delete_item"
    PERM_RESTOCK = "restock"
    PERM_MANAGE_USERS = "manage_users"
    PERM_VIEW_REPORTS = "view_reports"

    # Role -> Permissions Mapping
    ROLE_PERMISSIONS = {
        ROLE_ADMIN: [PERM_ADD_ITEM, PERM_EDIT_ITEM, PERM_DELETE_ITEM, PERM_RESTOCK, PERM_MANAGE_USERS, PERM_VIEW_REPORTS],
        ROLE_STAFF: [PERM_ADD_ITEM, PERM_EDIT_ITEM, PERM_RESTOCK, PERM_VIEW_REPORTS]
    }

    def __init__(self):
        self.db = DataStore()
        
    def _generate_user_id(self) -> str:
        """Generates a new User ID (e.g., USR003)."""
        users = self.db.get_all_users()
        if not users:
            return "USR001"
        
        max_id = 0
        for u in users:
            uid = str(u.get("User_ID", ""))
            if uid.startswith("USR"):
                try:
                    num = int(uid[3:])
                    max_id = max(max_id, num)
                except ValueError:
                    continue
        return f"USR{max_id + 1:03d}"

    def hash_password(self, plain_password: str) -> str:
        """Hashes a password using bcrypt."""
        return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies a password against its hash."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def create_user(self, creator_admin: Optional[Dict], username: str, password: str, role: str, email: str = ""):
        """Creates a new user. Enforces that only Admin can create users (except specific initial setup)."""
        # Initial setup check: if no users exist, allow creation without admin
        all_users = self.db.get_all_users()
        if all_users and (not creator_admin or creator_admin.get("Role") != self.ROLE_ADMIN):
            raise PermissionError("Only Admins can create new users.")
        
        # Check if username exists
        for u in all_users:
            if u.get("Username").lower() == username.lower():
                raise ValueError(f"Username '{username}' already exists.")

        user_id = self._generate_user_id()
        password_hash = self.hash_password(password)
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        new_user = {
            "User_ID": user_id,
            "Username": username,
            "Email": email,
            "Password_Hash": password_hash,
            "Role": role,
            "Created_Date": today,
            "Last_Login": "",
            "Account_Status": "Active",
            "Created_By": creator_admin["Username"] if creator_admin else "SYSTEM_INIT",
            "Notes": ""
        }
        
        self.db.add_user(new_user)
        self.db.log_activity(creator_admin["User_ID"] if creator_admin else user_id, "CREATE_USER", f"Created user {username} ({role})")
        return new_user

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticates a user and returns their profile if successful."""
        users = self.db.get_all_users()
        for user in users:
            if user.get("Username").lower() == username.lower():
                if user.get("Account_Status") != "Active":
                    raise PermissionError("Account is locked or suspended.")
                
                if self.verify_password(password, user.get("Password_Hash")):
                    self.db.update_last_login(user["User_ID"])
                    self.db.log_activity(user["User_ID"], "LOGIN", "User logged in")
                    return user
                else:
                    return None # Invalid password
        return None # User not found

    def check_permission(self, user: Dict, permission: str) -> bool:
        """Checks if the user has the required permission."""
        if not user or "Role" not in user:
            return False
        
        allowed_perms = self.ROLE_PERMISSIONS.get(user["Role"], [])
        return permission in allowed_perms

    def update_user(self, admin_user: Dict, user_id: str, username: str = None, email: str = None, role: str = None, status: str = None):
        """Updates user details. Only Admin can update users."""
        if not admin_user or admin_user.get("Role") != self.ROLE_ADMIN:
            raise PermissionError("Only Admins can update users.")
        
        # Check if username is being changed and if it's unique
        if username:
            all_users = self.db.get_all_users()
            for u in all_users:
                if u.get("User_ID") != user_id and u.get("Username").lower() == username.lower():
                    raise ValueError(f"Username '{username}' already exists.")
        
        # Build updates dict
        updates = {}
        if username:
            updates["Username"] = username
        if email is not None:
            updates["Email"] = email
        if role:
            updates["Role"] = role
        if status:
            updates["Account_Status"] = status
        
        self.db.update_user(user_id, updates)
        self.db.log_activity(admin_user["User_ID"], "UPDATE_USER", f"Updated user {user_id}")
        
        return self.db.get_user_by_id(user_id)

    def delete_user(self, admin_user: Dict, user_id: str):
        """Deletes a user. Only Admin can delete users. Cannot delete self or last admin."""
        if not admin_user or admin_user.get("Role") != self.ROLE_ADMIN:
            raise PermissionError("Only Admins can delete users.")
        
        # Cannot delete yourself
        if admin_user.get("User_ID") == user_id:
            raise PermissionError("Cannot delete yourself.")
        
        # Check if this is the last admin
        all_users = self.db.get_all_users()
        admin_count = sum(1 for u in all_users if u.get("Role") == self.ROLE_ADMIN)
        
        target_user = self.db.get_user_by_id(user_id)
        if not target_user:
            raise ValueError(f"User {user_id} not found.")
        
        if target_user.get("Role") == self.ROLE_ADMIN and admin_count <= 1:
            raise PermissionError("Cannot delete the last admin account.")
        
        username = target_user.get("Username")
        self.db.delete_user(user_id)
        self.db.log_activity(admin_user["User_ID"], "DELETE_USER", f"Deleted user {username} ({user_id})")
        
        return {"status": "success", "message": f"User {username} deleted"}

    def reset_user_password(self, admin_user: Dict, user_id: str, new_password: str):
        """Admin resets another user's password."""
        if not admin_user or admin_user.get("Role") != self.ROLE_ADMIN:
            raise PermissionError("Only Admins can reset user passwords.")
        
        target_user = self.db.get_user_by_id(user_id)
        if not target_user:
            raise ValueError(f"User {user_id} not found.")
        
        new_hash = self.hash_password(new_password)
        self.db.update_user_password(user_id, new_hash)
        self.db.log_activity(admin_user["User_ID"], "RESET_PASSWORD", f"Reset password for user {target_user.get('Username')} ({user_id})")
        
        return {"status": "success", "message": f"Password reset for {target_user.get('Username')}", "temporary_password": new_password}

    def change_password(self, user: Dict, current_password: str, new_password: str):
        """User changes their own password."""
        # Verify current password
        if not self.verify_password(current_password, user.get("Password_Hash")):
            raise PermissionError("Current password is incorrect.")
        
        # Update password
        new_hash = self.hash_password(new_password)
        self.db.update_user_password(user["User_ID"], new_hash)
        self.db.log_activity(user["User_ID"], "CHANGE_PASSWORD", "User changed their own password")
        
        return {"status": "success", "message": "Password changed successfully"}

