import os
import pandas as pd
from processors.grouping_logic import apply_grouping_logic, deduplicate_by_valor, remove_company_duplicates


def create_processing_summary(excel_data, composicoes_data, total_records, grouped_records_count):
    """Create processing summary for merged data"""
    all_files = set(excel_data.keys()) | set(composicoes_data.keys())
    
    return {
        "total_files": len(all_files),
        "excel_files": len(excel_data),
        "composicoes_files": len(composicoes_data),
        "files_with_both_sources": len(set(excel_data.keys()) & set(composicoes_data.keys())),
        "total_original_records": total_records,
        "total_grouped_records": grouped_records_count,
        "grouping_applied": True
    }


def merge_file_records(file_stem, excel_data, composicoes_data):
    """Merge records from excel and composicoes data for a single file"""
    file_records = []
    excel_records_count = 0
    composicoes_records_count = 0
    
    # Add all records from excel data if exists
    if file_stem in excel_data:
        for sheet_name, sheet_data in excel_data[file_stem].items():
            if 'records' in sheet_data:
                for record in sheet_data['records']:
                    record_copy = record.copy()
                    record_copy['source'] = 'excel'
                    record_copy['sheet'] = sheet_name
                    file_records.append(record_copy)
                    excel_records_count += 1
    
    # Add all records from composicoes data if exists
    if file_stem in composicoes_data:
        for record in composicoes_data[file_stem]:
            record_copy = record.copy()
            record_copy['source'] = 'composicoes'
            record_copy['sheet'] = 'Fornecedores'
            file_records.append(record_copy)
            composicoes_records_count += 1
    
    return file_records, excel_records_count, composicoes_records_count


def create_merged_excel_files(excel_data, composicoes_data, valor_empreendimento_total, output_folder="output"):
    """Create Excel files per file stem with grouped and deduplicated records"""

    os.makedirs(output_folder, exist_ok=True)
    all_files = set(excel_data.keys()) | set(composicoes_data.keys())

    print(f"\n{'='*50}")
    print("CREATING MERGED EXCEL FILES")
    print(f"{'='*50}")

    total_grouped = 0

    for file_stem in all_files:
        # Merge records
        file_records, excel_count, composicoes_count = merge_file_records(
            file_stem, excel_data, composicoes_data
        )
        print(f"✓ Merged {file_stem}: {len(file_records)} records (Excel: {excel_count}, Composicoes: {composicoes_count})")

        grouped_records = apply_grouping_logic(file_records)
        grouped_records = [record for record in grouped_records if record.get("Valor_Total", 0) >= 0]
        grouped_records = deduplicate_by_valor(grouped_records)
        
        # NOVA FUNCIONALIDADE: Remover duplicatas por empresa
        records_before_company_dedup = len(grouped_records)
        grouped_records = remove_company_duplicates(grouped_records)
        records_after_company_dedup = len(grouped_records)
        
        if records_before_company_dedup != records_after_company_dedup:
            removed_count = records_before_company_dedup - records_after_company_dedup
            print(f"  🔄 Removed {removed_count} company duplicates (same valor_nota + Valor, different empresa)")

        if not grouped_records:
            print(f"  ⚠ No grouped records for '{file_stem}', skipping Excel file.")
            continue

        # Calculate total from Valor column (not Valor_Total)
        total_valor = round(sum(r.get('Valor', 0) for r in grouped_records), 2)

        # Clean records: remove unnecessary fields
        cleaned_records = []
        for record in grouped_records:
            cleaned_record = {
                k: v for k, v in record.items()
                if k not in ['source', 'sheet', 'processing_rule']
            }
            cleaned_records.append(cleaned_record)

        # Create DataFrame
        df_result = pd.DataFrame(cleaned_records)
        
        # Add total row only once at the end
        if not df_result.empty:
            # Create a total row with empty values except for the total
            total_row = {col: '' for col in df_result.columns}
            total_row['total da planilha'] = total_valor
            
            # Add the total row to the DataFrame
            df_result = pd.concat([df_result, pd.DataFrame([total_row])], ignore_index=True)

        output_path = os.path.join(output_folder, f"{file_stem}.xlsx")
        df_result.to_excel(output_path, index=False)
        print(f"  💾 Saved Excel: {output_path} ({len(cleaned_records)} records + 1 total row)")

        total_grouped += len(cleaned_records)

    print(f"\n📊 Total grouped records saved across all files: {total_grouped}")
    print(f"💰 Valor do empreendimento: R$ {valor_empreendimento_total:,.2f}")