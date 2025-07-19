from utils.data_utils import get_valor_empreendimento_total
from processors.file_processor import process_excel_folder, process_composicoes_folder
from processors.excel_generator import create_merged_excel_files


def main():
    print("="*60)
    print("INTEGRATED EXCEL AND COMPOSICOES PROCESSOR WITH GROUPING")
    print("="*60)
    
    valor_empreendimento_total = get_valor_empreendimento_total()
    
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
        valor_empreendimento_total,
        output_folder="output"
    )
    
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE WITH GROUPING LOGIC!")
    print(f"💾 Output saved to folder: 'output/'")
    print(f"Valor total do empreendimento: R$ {valor_empreendimento_total:,.2f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()