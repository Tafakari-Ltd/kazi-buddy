from django.test import TestCase
from .views import upload_file_to_supabase, get_file_url_from_supabase, delete_file_from_supabase


# Create your tests here.
class FileUploadTestCase(TestCase):
    def test_upload_file_to_supabase(self):
        # Create a dummy file for testing
        with open('test_feiless.txt', 'w') as f:
            f.write('This is a test file.')

        # Call the upload function
        response = upload_file_to_supabase('test_feiless.txt', 'test_feiless.txt', 'documents')

        

        print(f"Response from Supabase: {response}")

        # Clean up the test file
        import os
        os.remove('test_feiless.txt')

   

    def test_get_file_url_from_supabase(self):
        file_path = 'test_feiless.txt'
        file_type = 'documents'
        public_url = get_file_url_from_supabase(file_path, file_type)

        print(f"Public URL for the file: {public_url}")
        self.assertTrue(public_url.startswith("https://"))
    
    def test_delete_file_from_supabase(self):
       
        file_type = 'documents'
        file_name = 'test_feiless.txt'
         
        # Now delete the file
        response = delete_file_from_supabase(file_name, file_type)

        print(f"File deletion response: {response}")
        self.assertTrue(response)
