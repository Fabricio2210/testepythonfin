import pandas as pd


def safe_float_conversion(value):
    if pd.isna(value) or value is None:
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        cleaned_value = value.strip().replace(',', '').replace(' ', '')
        
        if not cleaned_value:
            return 0.0
        
        try:
            return float(cleaned_value)
        except ValueError:
            print(f"Warning: Could not convert '{value}' to float, returning 0.0")
            return 0.0
    
    try:
        return float(value)
    except (ValueError, TypeError):
        print(f"Warning: Could not convert '{value}' to float, returning 0.0")
        return 0.0


def deduplicate_by_valor(records):
    deduped = {}
    result = []

    for record in records:
        nota = int(record.get("nota")) if record.get("nota") is not None else None
        empresa = record.get("empresa", "").strip().upper()
        valor = safe_float_conversion(record.get("Valor"))
        valor_total = safe_float_conversion(record.get("Valor_Total"))

        if valor == valor_total:
            key = (nota, empresa, valor, valor_total)
            if key not in deduped or record.get("source") == "excel":
                deduped[key] = {
                    **record,
                    "nota": nota,
                    "Valor": valor,
                    "Valor_Total": valor_total
                }
        else:
            result.append(record)

    result.extend(deduped.values())
    return result


def remove_company_duplicates(records):
    if not records:
        return records
    groups = {}
    for record in records:
        valor_nota = record.get('valor_nota', '')
        valor = safe_float_conversion(record.get('Valor', 0))
        key = (valor_nota, valor)
        
        if key not in groups:
            groups[key] = []
        groups[key].append(record)
    
    filtered_records = []
    
    for key, group_records in groups.items():
        if len(group_records) == 1:
            filtered_records.extend(group_records)
        else:
            empresas_diferentes = set()
            for record in group_records:
                empresa = record.get('empresa', '').strip().upper()
                empresas_diferentes.add(empresa)
            
            if len(empresas_diferentes) <= 1:
                filtered_records.extend(group_records)
            else:
                records_sem_siglas = []
                records_com_siglas = []
                
                for record in group_records:
                    empresa = record.get('empresa', '').strip().upper()
                    tem_sigla = any(sigla in empresa for sigla in ['LTDA', 'S.A', 'S/A'])
                    
                    if tem_sigla:
                        records_com_siglas.append(record)
                    else:
                        records_sem_siglas.append(record)
                
                if records_sem_siglas:
                    filtered_records.append(records_sem_siglas[0])
                else:
                    filtered_records.append(records_com_siglas[0])
    
    return filtered_records


def cancel_opposing_values(grouped_results):
    print(f"\n{'='*50}")
    print("APPLYING CANCELLATION LOGIC")
    print(f"{'='*50}")
    
    rule2_records = []
    other_records = []
    
    for record in grouped_results:
        if record.get('processing_rule') == 'equal_values_division':
            rule2_records.append(record)
        else:
            other_records.append(record)
    
    print(f"Records from rule 2 (equal_values_division): {len(rule2_records)} - EXCLUDED from cancellation")
    print(f"Records from other rules: {len(other_records)} - WILL BE processed for cancellation")
    
    empresa_groups = {}
    for record in other_records:
        empresa = record['empresa']
        if empresa not in empresa_groups:
            empresa_groups[empresa] = []
        empresa_groups[empresa].append(record)
    
    final_results = []
    
    for empresa, records in empresa_groups.items():
        print(f"\nProcessing cancellations for empresa: '{empresa}'")
        print(f"  Records before cancellation: {len(records)}")
        
        to_cancel = set()

        for i, record1 in enumerate(records):
            if i in to_cancel:
                continue
                
            valor1 = safe_float_conversion(record1['Valor'])
            
            for j, record2 in enumerate(records[i+1:], i+1):
                if j in to_cancel:
                    continue
                    
                valor2 = safe_float_conversion(record2['Valor'])
                
                if abs(valor1 + valor2) < 0.01:
                    print(f"  ✓ Cancelling: {valor1} + {valor2} = {valor1 + valor2}")
                    print(f"    Record 1: Nota {record1['nota']}, Valor {valor1}")
                    print(f"    Record 2: Nota {record2['nota']}, Valor {valor2}")
                    to_cancel.add(i)
                    to_cancel.add(j)
                    break 
        
        remaining_records = [record for i, record in enumerate(records) if i not in to_cancel]
        final_results.extend(remaining_records)
        
        print(f"  Records after cancellation: {len(remaining_records)}")
        if len(remaining_records) != len(records):
            print(f"  ✓ Cancelled {len(records) - len(remaining_records)} records")
    
    final_results.extend(rule2_records)
    
    print(f"\n✓ Cancellation logic completed")
    print(f"✓ Records before cancellation: {len(other_records)} (rule 2 records excluded)")
    print(f"✓ Records after cancellation: {len(final_results) - len(rule2_records)}")
    print(f"✓ Rule 2 records added back: {len(rule2_records)}")
    print(f"✓ Total final records: {len(final_results)}")
    
    return final_results


def apply_grouping_logic(all_records):
    """
    Apply the grouping logic before creating JSON:
    1. Filter by empresa and nota number
    2. If single record, keep as-is
    3. If multiple records with all integer parts of soma values equal, divide total by unit value to get number of rows
    4. If multiple records with different values, sum them all together
    5. Cancel opposing values for same empresa
    """
    print(f"\n{'='*50}")
    print("APPLYING GROUPING LOGIC")
    print(f"{'='*50}")
    
    df = pd.DataFrame(all_records)
    df_filtered = df.dropna(subset=['nota', 'empresa'])
    
    print(f"Total records before filtering: {len(df)}")
    print(f"Records with both nota and empresa: {len(df_filtered)}")
    
    grouped_results = []
    
    for (empresa, nota), group in df_filtered.groupby(['empresa', 'nota']):
        print(f"\nProcessing group: Empresa='{empresa}', Nota='{nota}'")
        print(f"  Records in group: {len(group)}")
        
        # Convert soma values to float safely
        soma_values = [safe_float_conversion(val) for val in group['soma'].dropna().tolist()]
        soma_notas_values = [safe_float_conversion(val) for val in group['soma_notas'].dropna().tolist()]
        
        if not soma_values:
            print(f"  ⚠ No valid soma values found, skipping group")
            continue
        
        print(f"  Soma values: {soma_values}")
        print(f"  Soma_notas values: {soma_notas_values}")
        
        if len(group) == 1:
            print(f"  ✓ Rule 1 applied: Single record, keeping as-is")
            single_record = group.iloc[0]
            soma_value = safe_float_conversion(single_record['soma'])
            soma_notas_value = safe_float_conversion(soma_notas_values[0] if soma_notas_values else single_record['soma'])
            
            grouped_results.append({
                'nota': nota,
                'empresa': empresa,
                'Valor': round(soma_value, 2),
                'Valor_Total': round(soma_notas_value, 2),
                'source': single_record.get('source', 'unknown'),
                'sheet': single_record.get('sheet', 'unknown'),
                'processing_rule': 'single_record'
            })
            continue
        
        soma_values_int = [int(val) for val in soma_values]
        unique_soma_values = list(set(soma_values_int))
        
        if len(unique_soma_values) == 1:
            unit_value_int = unique_soma_values[0]
            
            total_value = soma_notas_values[0] if soma_notas_values else sum(soma_values)
            
            if unit_value_int != 0:
                num_rows = abs(total_value / unit_value_int)
                print(f"  ✓ Rule 2 applied: Multiple records with all values equal (integer part only: {unit_value_int})")
                print(f"  ✓ Total value: {total_value}, Unit value (int): {unit_value_int}")
                print(f"  ✓ Number of rows to create: {num_rows}")
                
                original_unit_value = soma_values[0]
                
                for i in range(int(num_rows)):
                    grouped_results.append({
                        'nota': nota,
                        'empresa': empresa,
                        'Valor': round(original_unit_value, 2),
                        'Valor_Total': round(total_value, 2),
                        'source': group.iloc[0].get('source', 'unknown'),
                        'sheet': group.iloc[0].get('sheet', 'unknown'),
                        'processing_rule': 'equal_values_division'
                    })
            else:
                print(f"  ⚠ Unit value is 0, skipping division")
        else:
            total_soma = sum(soma_values)
            total_soma_notas = soma_notas_values[0] if soma_notas_values else total_soma
            
            print(f"  ✓ Rule 3 applied: Multiple records with different values")
            print(f"  ✓ Total soma: {total_soma}")
            print(f"  ✓ Total soma_notas: {total_soma_notas}")
            
            if abs(total_soma - total_soma_notas) < 0.01:
                print(f"  ✓ Sum equals soma_nota, creating single row")
                grouped_results.append({
                    'nota': nota,
                    'empresa': empresa,
                    'Valor': round(total_soma, 2),
                    'Valor_Total': round(total_soma_notas, 2),
                    'source': group.iloc[0].get('source', 'unknown'),
                    'sheet': group.iloc[0].get('sheet', 'unknown'),
                    'processing_rule': 'different_values_sum'
                })
            else:
                print(f"  ⚠ Sum ({total_soma}) does not equal soma_nota ({total_soma_notas})")
                grouped_results.append({
                    'nota': nota,
                    'empresa': empresa,
                    'Valor': round(total_soma, 2),
                    'Valor_Total': round(total_soma_notas, 2),
                    'source': group.iloc[0].get('source', 'unknown'),
                    'sheet': group.iloc[0].get('sheet', 'unknown'),
                    'processing_rule': 'different_values_sum_discrepancy'
                })
    
    print(f"\n✓ Initial grouping logic applied")
    print(f"✓ Original records: {len(df_filtered)}")
    print(f"✓ Grouped results: {len(grouped_results)}")
    
    final_results = cancel_opposing_values(grouped_results)
    
    return final_results