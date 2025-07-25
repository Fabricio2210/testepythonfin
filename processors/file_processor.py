import os
import re
import pandas as pd
from pathlib import Path
from collections import defaultdict
from utils.data_utils import prepare_dataframe_for_json, normalize_nota_field, clean_nan_from_records
from parsers.complemento_parser import parse_complemento_column


def get_excel_files(folder_path):
    if not os.path.exists(folder_path):
        print(f"Warning: Folder '{folder_path}' does not exist.")
        return []

    excel_files = [file for file in os.listdir(folder_path) if file.endswith(('.xlsx', '.xls'))]
    return excel_files


def process_single_composicoes_file(file_path, file_stem):
    try:
        df = pd.read_excel(file_path, sheet_name='Fornecedores', skiprows=11)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        if 'Valor' in df.columns:
            df = df.dropna(subset=['Valor'])
            print(f"  ✓ Removed rows with NaN 'Valor'")
        else:
            print(f"  ⚠ Warning: 'Valor' column not found in {file_stem}")

        df_clean = prepare_dataframe_for_json(df)

        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].astype(str).str.strip()

        df_transformed = df_clean.rename(columns={
            "Mês": "nota",
            "NF-s": "nota", 
            "Descriçao": "empresa",
            "Valor": "soma"
        })

        if "Saldo" in df_transformed.columns:
            df_transformed = df_transformed.drop(columns=["Saldo"])

        records = df_transformed.to_dict('records')

        processed_records = []
        for r in records:
            r = normalize_nota_field(r)
            try:
                r['nota'] = int(re.sub(r'\D', '', str(r.get('nota', ''))))
            except (ValueError, TypeError):
                r['nota'] = None
            processed_records.append(r)

        print(f"  ✓ Successfully processed 'Fornecedores' sheet ({len(processed_records)} records)")
        return processed_records

    except ValueError as e:
        if "Worksheet named 'Fornecedores' not found" in str(e):
            print(f"  ✗ Sheet 'Fornecedores' not found in {file_stem}")
            try:
                xl_file = pd.ExcelFile(file_path)
                print(f"    Available sheets: {xl_file.sheet_names}")
            except Exception:
                pass
        else:
            print(f"  ✗ Error reading {file_stem}: {e}")
        return []
    except Exception as e:
        print(f"  ✗ Error processing {file_stem}: {e}")
        return []


def build_composicoes_lookup(fornecedores_data):
    composicoes_lookup = set()
    
    for file_data in fornecedores_data.values():
        for record in file_data:
            if record.get('empresa') and record.get('nota') is not None:
                empresa = str(record['empresa']).strip().lower()
                nota = record['nota']
                composicoes_lookup.add((empresa, nota))
    
    return composicoes_lookup


def check_empresa_against_composicoes(records, composicoes_lookup):
    empresa_groups = defaultdict(list)
    for record in records:
        if record.get('empresa'):
            empresa = str(record['empresa']).strip().lower()
            empresa_groups[empresa].append(record)
    
    records_to_remove = []
    
    for empresa, empresa_records in empresa_groups.items():
        empresa_sum = sum(
            float(record.get('soma_notas', 0)) 
            for record in empresa_records 
            if record.get('soma_notas') is not None
        )
        
        if abs(empresa_sum) < 0.01:
            has_nota_in_composicoes = False
            
            for record in empresa_records:
                nota = record.get('nota')
                if nota is not None:
                    lookup_key = (empresa, nota)
                    if lookup_key in composicoes_lookup:
                        has_nota_in_composicoes = True
                        break
            
            if has_nota_in_composicoes:
                records_to_remove.extend(empresa_records)
                print(f"  🗑️  Removing empresa '{empresa}' (sum=0, found in composicoes)")
    
    return records_to_remove


def process_single_excel_file(file_path, composicoes_lookup=None):
    try:
        print(f"Processing excel: {file_path.name}")
        excel_sheets = pd.read_excel(file_path, sheet_name=None)
        
        file_data = {}
        file_soma_total = 0.0

        for sheet_name, df in excel_sheets.items():
            df = parse_complemento_column(df) 
            print(df[["Complemento", "nota", "empresa", "Débito", "Crédito", "soma"]])
            records = df.to_dict('records')
            cleaned_records = clean_nan_from_records(records) 

            if composicoes_lookup is not None:
                records_to_remove = check_empresa_against_composicoes(cleaned_records, composicoes_lookup)
                if records_to_remove:
                    records_to_remove_set = set(id(r) for r in records_to_remove)
                    cleaned_records = [r for r in cleaned_records if id(r) not in records_to_remove_set]
                    print(f"  📊 Removed {len(records_to_remove)} records due to composicoes cross-check")

            soma_notas_sheet_total = sum(
                float(r['soma_notas']) for r in cleaned_records if 'soma_notas' in r
            )
            file_soma_total += soma_notas_sheet_total

            file_data[sheet_name] = {
                "records": cleaned_records,
                "soma_notas_total": round(soma_notas_sheet_total, 2)
            }

            removed_count = len(records) - len(cleaned_records)
            if removed_count > 0:
                print(f"  Sheet '{sheet_name}': Removed {removed_count} records total")

        print(f"  ✓ Processed {file_path.name} (Total: R$ {file_soma_total:,.2f})")
        return file_data, file_soma_total

    except Exception as e:
        print(f"  ✗ Error processing {file_path.name}: {str(e)}")
        return {}, 0.0


def process_composicoes_folder(folder_path="composicoes"):

    excel_files = get_excel_files(folder_path)
    
    if not excel_files:
        print(f"No Excel files found in '{folder_path}' folder.")
        return {}

    print(f"Found {len(excel_files)} Excel file(s) in '{folder_path}' folder")

    fornecedores_data = {}

    for file in excel_files:
        file_path = os.path.join(folder_path, file)
        file_stem = Path(file).stem
        print(f"Processing composicoes: {file}")

        records = process_single_composicoes_file(file_path, file_stem)
        fornecedores_data[file_stem] = records

    return fornecedores_data


def process_excel_folder(excel_folder="razoes", fornecedores_data=None):

    excel_files = []
    for ext in ['*.xlsx', '*.xls']:
        excel_files.extend(Path(excel_folder).glob(ext))

    if not excel_files:
        print(f"No Excel files found in '{excel_folder}' folder")
        return {}

    print(f"Found {len(excel_files)} Excel file(s) in '{excel_folder}' folder")
    
    composicoes_lookup = None
    if fornecedores_data:
        composicoes_lookup = build_composicoes_lookup(fornecedores_data)
        print(f"📋 Built composicoes lookup with {len(composicoes_lookup)} empresa-nota combinations")
    
    excel_data = {}
    soma_notas_grand_total = 0.0

    for file_path in excel_files:
        file_stem = file_path.stem
        file_data, file_soma_total = process_single_excel_file(file_path, composicoes_lookup)
        
        excel_data[file_stem] = file_data
        soma_notas_grand_total += file_soma_total

    print(f"🔢 Excel folder total: R$ {soma_notas_grand_total:,.2f}")
    return excel_data


def process_both_folders(excel_folder="excel", composicoes_folder="composicoes"):

    print("=== Processing Composicoes Folder ===")
    fornecedores_data = process_composicoes_folder(composicoes_folder)
    
    print("\n=== Processing Excel Folder with Composicoes Cross-Check ===")
    excel_data = process_excel_folder(excel_folder, fornecedores_data)
    
    return excel_data, fornecedores_data