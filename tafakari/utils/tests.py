from django.test import TestCase
from .views import upload_file_to_supabase, get_file_url_from_supabase, delete_file_from_supabase
import os
import tempfile
import time
from django.conf import settings

class FileUploadTestCase(TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_filename = f'test_file_{int(time.time())}.txt'
        self.test_content = 'This is a test file for Supabase operations.'
        
        # Check if Supabase is configured
        if not hasattr(settings, 'SUPABASE_URL') or not hasattr(settings, 'SUPABASE_KEY'):
            self.skipTest("Supabase not configured - skipping tests")
        
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            self.skipTest("Supabase credentials not provided - skipping tests")
    
    def test_upload_file_to_supabase(self):
        """Test file upload to Supabase"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(self.test_content)
            temp_file_path = f.name
        
        try:
            # Test upload
            response = upload_file_to_supabase(temp_file_path, self.test_filename, 'documents')
            print(f"Upload response: {response}")
            
            # Verify response is a URL
            self.assertIsNotNone(response)
            self.assertTrue(response.startswith("https://"), f"Expected URL, got: {response}")
            
        except Exception as e:
            self.fail(f"Upload test failed: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def test_get_file_url_from_supabase(self):
        """Test getting file URL from Supabase"""
        try:
            # First upload a file to ensure it exists
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(self.test_content)
                temp_file_path = f.name
            
            # Upload file first
            upload_response = upload_file_to_supabase(temp_file_path, self.test_filename, 'documents')
            self.assertIsNotNone(upload_response)
            
            # Now test getting URL
            public_url = get_file_url_from_supabase(self.test_filename, 'documents')
            print(f"Public URL for the file: {public_url}")
            
            self.assertIsNotNone(public_url)
            self.assertTrue(public_url.startswith("https://"), f"Expected URL, got: {public_url}")
            
        except Exception as e:
            self.fail(f"Get URL test failed: {str(e)}")
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def test_delete_file_from_supabase(self):
        """Test file deletion from Supabase"""
        try:
            # First upload a file to ensure it exists for deletion
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(self.test_content)
                temp_file_path = f.name
            
            # Upload file first
            upload_response = upload_file_to_supabase(temp_file_path, self.test_filename, 'documents')
            self.assertIsNotNone(upload_response)
            
            # Small delay to ensure upload completes
            time.sleep(1)
            
            # Now test deletion
            delete_response = delete_file_from_supabase(self.test_filename, 'documents')
            print(f"File deletion response: {delete_response}")
            
            self.assertTrue(delete_response, "Delete operation should return True")
            
        except Exception as e:
            self.fail(f"Delete test failed: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def tearDown(self):
        """Clean up after tests"""
        # Attempt to clean up any remaining test files
        try:
            delete_file_from_supabase(self.test_filename, 'documents')
        except:
            pass  # Ignore cleanup errors


# Additional debugging helper
def test_supabase_connection():
    """Test basic Supabase connection"""
    from .views import get_supabase_client
    
    client = get_supabase_client()
    if not client:
        print("❌ Supabase client creation failed")
        return False
    
    try:
        # Test basic bucket access
        buckets = client.storage.list_buckets()
        print(f"✅ Supabase connection successful. Available buckets: {buckets}")
        return True
    except Exception as e:
        print(f"❌ Supabase connection test failed: {str(e)}")
        return False