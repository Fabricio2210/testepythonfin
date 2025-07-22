import pandas as pd
import json
import math
import numpy as np
from datetime import datetime, date


def has_nan_values(obj):
    if isinstance(obj, dict):
        return any(has_nan_values(value) for value in obj.values())
    elif isinstance(obj, list):
        return any(has_nan_values(item) for item in obj)
    elif isinstance(obj, float) and math.isnan(obj):
        return True
    elif pd.isna(obj):
        return True
    return False


def convert_to_json_serializable(obj):
    if pd.isna(obj):
        return None
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    else:
        return obj


def prepare_dataframe_for_json(df):
    df_copy = df.copy()

    for col in df_copy.columns:
        if df_copy[col].dtype == 'datetime64[ns]':
            df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        elif df_copy[col].dtype == 'object':
            df_copy[col] = df_copy[col].apply(convert_to_json_serializable)

    return df_copy.where(pd.notnull(df_copy), None)


def normalize_nota_field(record):
    if "nota" not in record:
        return record

    value = record["nota"]
    if value is None:
        del record["nota"]
    elif isinstance(value, float) and value.is_integer():
        record["nota"] = int(value)

    return record


def clean_nan_from_records(records):
    cleaned_records = []
    for record in records:
        if has_nan_values(record):
            continue
        if 'soma_notas' in record and float(record['soma_notas']) == 0.0:
            continue
        cleaned_records.append(record)
    return cleaned_records


# def get_valor_empreendimento_total():
#     """Get the total project value from user input"""
#     while True:
#         try:
#             valor_str = input("Digite o valor total do empreendimento (R$): ")
#             valor_str = valor_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
#             valor_empreendimento_total = float(valor_str)
#             print(f"Valor total do empreendimento: R$ {valor_empreendimento_total:,.2f}")
#             return valor_empreendimento_total
#         except ValueError:
#             print("Por favor, digite um valor numérico válido. Exemplo: 1000000.50 ou 1.000.000,50")