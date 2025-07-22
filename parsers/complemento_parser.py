import re
import pandas as pd
from utils.regex_patterns import extract_nota_from_parsed


def extract_initial_document_pattern(text):
    pattern = r"^(Pg PGELETR\s+\d+|FATURA\s+\d+|Ref\. AV DÉB\s+\d+|AP/\d+|CONTRATO|Valor ref\. IRRF s/ NF\s*<\d+>|Valor ref\. IRRF s/ NF|Valor ref\. NF_REF[\s\-]*\d+|ISS retido conf\. NFES[\s\-]*\d+|Pis, Cofins e Csll sobre NFES[\s\-]*\d+|APÓLICE[\s\-]*\d+)\s*-?"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def extract_date_document_pattern(text):
    match = re.search(r"^(\d{2}/\d{2}/\d{4}\s+\d+)\s*-", text)
    return match.group(1).strip() if match else None


def extract_document_reference_pattern(text):
    match = re.search(r"(NFES[\s\-]*\d+|NF_REF[\s\-]*\d+|NFELETR[\s\-]*\d+|APÓLICE[\s\-]*\d+|BOLETO[\s\-]?\d*|<\d+>)", text)
    return match.group(1).strip() if match else None


def extract_company_name_pattern(text):
    pattern = r"([A-ZÀ-ÿ][A-ZÀ-ÿ\s\-&\.,]*?(?:\bLTDA\b\.?|S\/A|S\.A\.|ME\b|EPP\b|SOCIEDADE(?: INDIVIDUAL DE ADVOCACIA)?|COMPANHIA))"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip(" -") if match else None


def parse_complemento_text(text):
    if not isinstance(text, str):
        return []

    parts = []
    remaining_text = text
    initial_doc = extract_initial_document_pattern(text)
    if initial_doc:
        parts.append(initial_doc)
        remaining_text = text[len(initial_doc):].strip()

    if not initial_doc:
        date_doc = extract_date_document_pattern(text)
        if date_doc:
            parts.append(date_doc)
            remaining_text = text[len(date_doc):].strip()

    doc_ref = extract_document_reference_pattern(remaining_text)
    if doc_ref:
        parts.append(doc_ref)
        remaining_text = remaining_text.replace(doc_ref, "").strip(" -")

    company_name = extract_company_name_pattern(remaining_text)
    if company_name:
        parts.append(company_name)
        remaining_text = remaining_text.replace(company_name, "").strip(" -")

    if remaining_text and remaining_text not in parts and len(remaining_text) > 3:
        remaining_parts = [part.strip() for part in remaining_text.split(" - ") if part.strip()]
        parts.extend(remaining_parts)

    cleaned_parts = []
    seen = set()
    for part in parts:
        cleaned_part = part.strip(" -")
        if cleaned_part and cleaned_part not in seen and len(cleaned_part) > 1:
            cleaned_parts.append(cleaned_part)
            seen.add(cleaned_part)

    return cleaned_parts


def extract_empresa_from_parsed(parsed_parts):
    """Extract empresa name by taking last segment with company keyword after splitting on ' - '"""
    if not isinstance(parsed_parts, list):
        return None
    
    keywords = ["LTDA", "S/A", "S.A", "SOCIEDADE", "COMPANHIA", "ME", "EPP"]
    
    for part in parsed_parts:
        # Split by ' - ' to isolate potential company name parts
        segments = [seg.strip() for seg in part.split(' - ')]
        
        # Check segments from right to left (last segments first)
        for segment in reversed(segments):
            if any(keyword.upper() in segment.upper() for keyword in keywords):
                return segment.strip()
    return None


def calculate_soma_notas(df):
    if 'nota' not in df.columns or 'soma' not in df.columns:
        return [0.00] * len(df)

    soma_notas = []
    for i, row in df.iterrows():
        current_nota = row['nota']
        current_empresa = row.get('empresa', None)
        
        if pd.isna(current_nota) or current_nota is None:
            soma_notas.append(0.00)
        else:
            if 'empresa' in df.columns and not pd.isna(current_empresa):
                matching_rows = df[
                    (df['nota'] == current_nota) & 
                    (df['empresa'] == current_empresa)
                ]
            else:
                matching_rows = df[df['nota'] == current_nota]
            
            total_sum = matching_rows['soma'].sum()
            soma_notas.append(round(total_sum, 2))

    return soma_notas


def parse_complemento_column(df):
    if "Complemento" not in df.columns:
        return df

    df["ComplementoParsed"] = df["Complemento"].apply(parse_complemento_text)
    df["nota"] = df["ComplementoParsed"].apply(extract_nota_from_parsed)
    df["empresa"] = df["ComplementoParsed"].apply(extract_empresa_from_parsed)

    if "Débito" in df.columns and "Crédito" in df.columns:
        df["soma"] = -df["Débito"] + df["Crédito"]
        df["soma_notas"] = calculate_soma_notas(df)

    return df