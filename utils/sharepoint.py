import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_microsoft_access_token():
    """
    Get an access token from Microsoft OAuth2 endpoint using client credentials flow.
    
    Returns:
        str: The access token if successful
        None: If the request fails
    """
    
    # Get configuration from environment variables
    tenant_id = os.getenv('TENANT_ID')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    grant_type = os.getenv('GRANT_TYPE', 'client_credentials')
    scope = os.getenv('SCOPE', 'https://graph.microsoft.com/.default')
    
    # Validate required environment variables
    if not all([tenant_id, client_id, client_secret]):
        print("Error: Missing required environment variables (TENANT_ID, CLIENT_ID, CLIENT_SECRET)")
        return None
    
    # OAuth2 endpoint
    url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    
    # Headers (including cookies from original code)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'fpc=AhgZ3_SgOz1KhApKs_5fm1psCCyZAQAAABguEOAOAAAA; stsservicecookie=estsfd; x-ms-gateway-slice=estsfd'
    }
    
    # Request body data
    data = {
        'grant_type': grant_type,
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': scope
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        return token_data.get('access_token')
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None

def upload_excel_files_to_sharepoint(output_folder_path="./output"):
    """
    Upload all Excel files from the specified folder to SharePoint.
    
    Args:
        output_folder_path (str): Path to the folder containing Excel files
        
    Returns:
        dict: Results of upload attempts with success/failure status
    """
    
    # Get access token
    access_token = get_microsoft_access_token()
    if not access_token:
        print("Failed to get access token")
        return {"error": "Authentication failed"}
    
    # Get SharePoint configuration from environment variables
    drive_id = os.getenv('SHAREPOINT_DRIVE_ID')
    folder_path = os.getenv('SHAREPOINT_FOLDER_PATH', '/TI/composições')
    
    if not drive_id:
        print("Error: Missing SHAREPOINT_DRIVE_ID environment variable")
        return {"error": "SharePoint configuration missing"}
    
    # Base URL for the SharePoint drive location
    base_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{folder_path}"
    
    # Headers for API requests
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Check if output folder exists
    output_path = Path(output_folder_path)
    if not output_path.exists():
        print(f"Output folder '{output_folder_path}' does not exist")
        return {"error": f"Folder '{output_folder_path}' not found"}
    
    # Find all Excel files in the folder
    excel_extensions = ['.xlsx', '.xls', '.xlsm', '.xlsb']
    excel_files = []
    
    for ext in excel_extensions:
        excel_files.extend(output_path.glob(f'*{ext}'))
    
    if not excel_files:
        print(f"No Excel files found in '{output_folder_path}'")
        return {"message": "No Excel files found"}
    
    print(f"Found {len(excel_files)} Excel file(s) to upload")
    
    results = {
        "successful_uploads": [],
        "failed_uploads": [],
        "total_files": len(excel_files)
    }
    
    # Upload each Excel file
    for file_path in excel_files:
        try:
            print(f"Uploading: {file_path.name}")
            
            # Read file content
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            # Construct upload URL
            upload_url = f"{base_url}/{file_path.name}:/content"
            
            # Upload headers (different from API headers)
            upload_headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/octet-stream'
            }
            
            # Upload file
            response = requests.put(upload_url, headers=upload_headers, data=file_content)
            
            if response.status_code in [200, 201]:
                print(f"✓ Successfully uploaded: {file_path.name}")
                results["successful_uploads"].append({
                    "filename": file_path.name,
                    "size": len(file_content),
                    "status": "success"
                })
            else:
                print(f"✗ Failed to upload {file_path.name}: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                results["failed_uploads"].append({
                    "filename": file_path.name,
                    "error": f"HTTP {response.status_code}: {response.text}"
                })
                
        except Exception as e:
            print(f"✗ Error uploading {file_path.name}: {e}")
            results["failed_uploads"].append({
                "filename": file_path.name,
                "error": str(e)
            })
    
    # Print summary
    print("\n" + "="*50)
    print(f"Upload Summary:")
    print(f"Total files: {results['total_files']}")
    print(f"Successful: {len(results['successful_uploads'])}")
    print(f"Failed: {len(results['failed_uploads'])}")
    print("="*50)
    
    return results

# Example usage
if __name__ == "__main__":
    # Upload all Excel files from the "output" folder
    results = upload_excel_files_to_sharepoint("./output")
    
    # Print detailed results
    if results.get("successful_uploads"):
        print("\nSuccessful uploads:")
        for upload in results["successful_uploads"]:
            print(f"  - {upload['filename']} ({upload['size']} bytes)")
    
    if results.get("failed_uploads"):
        print("\nFailed uploads:")
        for failed in results["failed_uploads"]:
            print(f"  - {failed['filename']}: {failed['error']}")