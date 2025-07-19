import pandas as pd


def deduplicate_by_valor(records):
    """
    Deduplicate records if they have the same nota, empresa, and *exact* same Valor and Valor_Total.
    Prefer records with source 'excel' over 'composicoes'.
    """
    deduped = {}
    result = []

    for record in records:
        nota = int(record.get("nota")) if record.get("nota") is not None else None
        empresa = record.get("empresa", "").strip().upper()
        valor = record.get("Valor")
        valor_total = record.get("Valor_Total")

        # Only deduplicate if Valor and Valor_Total are equal (exact match)
        if valor == valor_total:
            key = (nota, empresa, valor, valor_total)
            if key not in deduped or record.get("source") == "excel":
                deduped[key] = {
                    **record,
                    "nota": nota  # ensure nota is int
                }
        else:
            # For records where Valor != Valor_Total, keep them all (no dedupe)
            result.append(record)

    # Add deduplicated records to the result
    result.extend(deduped.values())
    return result


def remove_company_duplicates(records):
    """
    Remove duplicatas baseado em valor_nota e Valor iguais, mas empresa diferente.
    Prioriza manter registros que NÃO tenham LTDA, S.A ou S/A no campo empresa.
    """
    if not records:
        return records
    
    # Criar grupos baseados em valor_nota e Valor
    groups = {}
    for record in records:
        valor_nota = record.get('valor_nota', '')
        valor = record.get('Valor', 0)
        key = (valor_nota, valor)
        
        if key not in groups:
            groups[key] = []
        groups[key].append(record)
    
    filtered_records = []
    
    for key, group_records in groups.items():
        if len(group_records) == 1:
            # Se só tem um registro, mantém
            filtered_records.extend(group_records)
        else:
            # Se tem múltiplos registros, aplica a lógica de filtro
            empresas_diferentes = set()
            for record in group_records:
                empresa = record.get('empresa', '').strip().upper()
                empresas_diferentes.add(empresa)
            
            # Se todas as empresas são iguais, mantém todos
            if len(empresas_diferentes) <= 1:
                filtered_records.extend(group_records)
            else:
                # Empresas diferentes - aplicar lógica de prioridade
                records_sem_siglas = []
                records_com_siglas = []
                
                for record in group_records:
                    empresa = record.get('empresa', '').strip().upper()
                    tem_sigla = any(sigla in empresa for sigla in ['LTDA', 'S.A', 'S/A'])
                    
                    if tem_sigla:
                        records_com_siglas.append(record)
                    else:
                        records_sem_siglas.append(record)
                
                # Prioridade: manter registros SEM siglas
                if records_sem_siglas:
                    # Se tem registros sem siglas, manter apenas um deles (o primeiro)
                    filtered_records.append(records_sem_siglas[0])
                else:
                    # Se todos têm siglas, manter apenas um (o primeiro)
                    filtered_records.append(records_com_siglas[0])
    
    return filtered_records


def apply_grouping_logic(all_records):
    """
    Apply the grouping logic before creating JSON:
    1. Filter by empresa and nota number
    2. If all integer parts of soma values are equal, divide total by unit value to get number of rows
    3. If values are different, sum them all together
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
        
        soma_values = group['soma'].dropna().tolist()
        soma_notas_values = group['soma_notas'].dropna().tolist()
        
        if not soma_values:
            print(f"  ⚠ No valid soma values found, skipping group")
            continue
        
        print(f"  Soma values: {soma_values}")
        print(f"  Soma_notas values: {soma_notas_values}")
        
        # For checking equality: integer part only
        soma_values_int = [int(val) for val in soma_values]
        unique_soma_values = list(set(soma_values_int))
        
        if len(unique_soma_values) == 1:
            # Use integer unit_value for logic only
            unit_value_int = unique_soma_values[0]
            
            total_value = soma_notas_values[0] if soma_notas_values else sum(soma_values)
            
            if unit_value_int != 0:
                num_rows = abs(total_value / unit_value_int)
                print(f"  ✓ Rule 2 applied: All values equal (integer part only: {unit_value_int})")
                print(f"  ✓ Total value: {total_value}, Unit value (int): {unit_value_int}")
                print(f"  ✓ Number of rows to create: {num_rows}")
                
                # When creating rows, use original decimal unit_value from first record (not int)
                original_unit_value = soma_values[0]
                
                for i in range(int(num_rows)):
                    grouped_results.append({
                        'nota': nota,
                        'empresa': empresa,
                        'Valor': round(original_unit_value, 2),      # keep decimals here
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
            
            print(f"  ✓ Rule 3 applied: Values are different")
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
    
    print(f"\n✓ Grouping logic applied successfully")
    print(f"✓ Original records: {len(df_filtered)}")
    print(f"✓ Grouped results: {len(grouped_results)}")
    
    return grouped_results