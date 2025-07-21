# from utils.data_utils import get_valor_empreendimento_total
from processors.file_processor import process_excel_folder, process_composicoes_folder
from processors.excel_generator import create_merged_excel_files
from utils.sharepoint import upload_excel_files_to_sharepoint


def main():
    print("="*60)
    print("INTEGRATED EXCEL AND COMPOSICOES PROCESSOR WITH GROUPING")
    print("="*60)
    
    # valor_empreendimento_total = get_valor_empreendimento_total()
    
    print(f"\n{'='*50}")
    print("PROCESSING EXCEL FOLDER")
    print(f"{'='*50}")
    excel_data = process_excel_folder()
    
    print(f"\n{'='*50}")
    print("PROCESSING COMPOSICOES FOLDER")
    print(f"{'='*50}")
    composicoes_data = process_composicoes_folder()
    
    create_merged_excel_files(
        excel_data,
        composicoes_data,
        #valor_empreendimento_total,
        output_folder="output"
    )
    
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE WITH GROUPING LOGIC!")
    print(f"💾 Output saved to folder: 'output/'")
    #print(f"Valor total do empreendimento: R$ {valor_empreendimento_total:,.2f}")
    print(f"{'='*60}")
    
    # Upload Excel files to SharePoint as the final step
    print(f"\n{'='*50}")
    print("UPLOADING TO SHAREPOINT")
    print(f"{'='*50}")
    
    try:
        upload_results = upload_excel_files_to_sharepoint("output")
        
        if upload_results.get("error"):
            print(f"❌ Upload failed: {upload_results['error']}")
        else:
            successful = len(upload_results.get("successful_uploads", []))
            failed = len(upload_results.get("failed_uploads", []))
            total = upload_results.get("total_files", 0)
            
            print(f"📤 SharePoint Upload Complete!")
            print(f"   Total files processed: {total}")
            print(f"   ✅ Successful uploads: {successful}")
            print(f"   ❌ Failed uploads: {failed}")
            
            if upload_results.get("successful_uploads"):
                print(f"\n   Successfully uploaded files:")
                for upload in upload_results["successful_uploads"]:
                    print(f"     • {upload['filename']}")
            
            if upload_results.get("failed_uploads"):
                print(f"\n   Failed uploads:")
                for failed in upload_results["failed_uploads"]:
                    print(f"     • {failed['filename']}: {failed.get('error', 'Unknown error')}")
                    
    except Exception as e:
        print(f"❌ Error during SharePoint upload: {e}")
    
    print(f"\n{'='*60}")
    print("ALL PROCESSING AND UPLOAD COMPLETE!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()