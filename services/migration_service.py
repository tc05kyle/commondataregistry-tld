"""Migration service to transition from old schema to new user-centric schema"""
import streamlit as st
from database.connection import get_db_connection
from database.canonical_id_system import canonical_id_service
from typing import Dict, List, Tuple
import json

class MigrationService:
    """Handles migration from old individuals/organizations tables to new user-centric schema"""
    
    def __init__(self):
        self.migration_log = []
    
    def create_new_tables(self) -> bool:
        """Create the new database schema"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Read and execute the new schema
            with open('database/new_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            # Execute schema creation
            cursor.execute(schema_sql)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            self.migration_log.append("✅ New database schema created successfully")
            return True
            
        except Exception as e:
            self.migration_log.append(f"❌ Error creating new schema: {e}")
            return False
    
    def migrate_individuals_to_users(self) -> bool:
        """Migrate data from individuals table to new users structure"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get all individuals
            cursor.execute("""
                SELECT individual_id, canonical_id, first_name, last_name, email, 
                       domain, phone, status, request_date, approved_date, 
                       approved_by, rejection_reason, metadata, created_at
                FROM individuals
            """)
            
            individuals = cursor.fetchall()
            migrated_count = 0
            
            for individual in individuals:
                try:
                    # Generate new canonical ID based on the new system
                    if individual[6]:  # phone exists
                        new_canonical_id = canonical_id_service.generate_canonical_id(
                            individual[2],  # first_name
                            individual[3],  # last_name
                            individual[6],  # phone
                            individual[4]   # email
                        )
                    else:
                        # If no phone, use old canonical_id but validate format
                        new_canonical_id = individual[1]
                    
                    # Insert into users table
                    cursor.execute("""
                        INSERT INTO users (canonical_id, first_name, last_name, status, 
                                         approved_date, approved_by, rejection_reason, metadata, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING user_id
                    """, (
                        new_canonical_id, individual[2], individual[3], individual[7],
                        individual[9], individual[10], individual[11], individual[12], individual[13]
                    ))
                    
                    user_id = cursor.fetchone()[0]
                    
                    # Insert primary email
                    cursor.execute("""
                        INSERT INTO user_emails (user_id, email, domain, is_primary, is_verified)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, individual[4], individual[5], True, True))
                    
                    # Insert primary phone if exists
                    if individual[6]:
                        cursor.execute("""
                            INSERT INTO user_phones (user_id, phone, is_primary, is_verified)
                            VALUES (%s, %s, %s, %s)
                        """, (user_id, individual[6], True, True))
                    
                    migrated_count += 1
                    
                except Exception as e:
                    self.migration_log.append(f"⚠️ Error migrating individual {individual[1]}: {e}")
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.migration_log.append(f"✅ Migrated {migrated_count} individuals to users table")
            return True
            
        except Exception as e:
            self.migration_log.append(f"❌ Error migrating individuals: {e}")
            return False
    
    def migrate_organizations(self) -> bool:
        """Migrate organizations to new structure"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get all organizations
            cursor.execute("""
                SELECT organization_id, canonical_id, organization_name, organization_type,
                       primary_contact_email, domain, phone, address, website, status,
                       request_date, approved_date, approved_by, rejection_reason, metadata, created_at
                FROM organizations
            """)
            
            organizations = cursor.fetchall()
            migrated_count = 0
            
            for org in organizations:
                try:
                    # Generate organization canonical ID (keep ORG- prefix)
                    org_canonical_id = org[1] if org[1].startswith('ORG-') else f"ORG-{org[1]}"
                    
                    # Insert into new organizations table
                    cursor.execute("""
                        INSERT INTO organizations (organization_canonical_id, organization_name, 
                                                 organization_type, address, website, status, 
                                                 approved_date, approved_by, rejection_reason, metadata, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING organization_id
                    """, (
                        org_canonical_id, org[2], org[3], org[7], org[8], org[9],
                        org[11], org[12], org[13], org[14], org[15]
                    ))
                    
                    new_org_id = cursor.fetchone()[0]
                    
                    # Insert primary email
                    cursor.execute("""
                        INSERT INTO organization_emails (organization_id, email, is_primary)
                        VALUES (%s, %s, %s)
                    """, (new_org_id, org[4], True))
                    
                    # Insert primary phone if exists
                    if org[6]:
                        cursor.execute("""
                            INSERT INTO organization_phones (organization_id, phone, is_primary)
                            VALUES (%s, %s, %s)
                        """, (new_org_id, org[6], True))
                    
                    migrated_count += 1
                    
                except Exception as e:
                    self.migration_log.append(f"⚠️ Error migrating organization {org[1]}: {e}")
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.migration_log.append(f"✅ Migrated {migrated_count} organizations")
            return True
            
        except Exception as e:
            self.migration_log.append(f"❌ Error migrating organizations: {e}")
            return False
    
    def validate_migration(self) -> Dict[str, int]:
        """Validate the migration by comparing record counts"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Count records in old tables
            cursor.execute("SELECT COUNT(*) FROM individuals")
            old_individuals_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM organizations")
            old_organizations_count = cursor.fetchone()[0]
            
            # Count records in new tables
            cursor.execute("SELECT COUNT(*) FROM users")
            new_users_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM organizations WHERE organization_canonical_id LIKE 'ORG-%'")
            new_organizations_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_emails WHERE is_primary = TRUE")
            primary_emails_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_phones WHERE is_primary = TRUE")
            primary_phones_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            validation_results = {
                'old_individuals': old_individuals_count,
                'new_users': new_users_count,
                'old_organizations': old_organizations_count,
                'new_organizations': new_organizations_count,
                'primary_emails': primary_emails_count,
                'primary_phones': primary_phones_count
            }
            
            # Log validation results
            if old_individuals_count == new_users_count:
                self.migration_log.append("✅ User migration validated successfully")
            else:
                self.migration_log.append(f"⚠️ User count mismatch: {old_individuals_count} -> {new_users_count}")
            
            if old_organizations_count == new_organizations_count:
                self.migration_log.append("✅ Organization migration validated successfully")
            else:
                self.migration_log.append(f"⚠️ Organization count mismatch: {old_organizations_count} -> {new_organizations_count}")
            
            return validation_results
            
        except Exception as e:
            self.migration_log.append(f"❌ Error validating migration: {e}")
            return {}
    
    def run_full_migration(self) -> bool:
        """Run the complete migration process"""
        st.info("Starting database migration to user-centric schema...")
        
        # Step 1: Create new tables
        if not self.create_new_tables():
            return False
        
        # Step 2: Migrate individuals to users
        if not self.migrate_individuals_to_users():
            return False
        
        # Step 3: Migrate organizations
        if not self.migrate_organizations():
            return False
        
        # Step 4: Validate migration
        validation_results = self.validate_migration()
        
        # Display results
        st.success("Migration completed!")
        
        with st.expander("Migration Log"):
            for log_entry in self.migration_log:
                st.text(log_entry)
        
        if validation_results:
            st.subheader("Migration Validation Results")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Individuals → Users", validation_results['new_users'], 
                         validation_results['new_users'] - validation_results['old_individuals'])
                st.metric("Primary Emails", validation_results['primary_emails'])
            
            with col2:
                st.metric("Organizations", validation_results['new_organizations'],
                         validation_results['new_organizations'] - validation_results['old_organizations'])
                st.metric("Primary Phones", validation_results['primary_phones'])
        
        return True
    
    def get_migration_log(self) -> List[str]:
        """Get the migration log"""
        return self.migration_log

# Global migration service instance
migration_service = MigrationService()