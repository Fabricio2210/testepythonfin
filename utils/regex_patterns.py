import re


def extract_nf_bracket_pattern(text):
    """Extract NF number from bracket pattern like 'NF <123>'"""
    match = re.search(r'NF\s*<(\d+)>', text.upper())
    return match.group(1) if match else None


def extract_date_number_pattern(text):
    """Extract number following date pattern like '12/01/2023 123'"""
    match = re.search(r'\d{2}/\d{2}/\d{4}\s+(\d+)', text)
    return match.group(1) if match else None


def extract_nfes_pattern(text):
    """Extract NFES number pattern"""
    match = re.search(r'NFES[\s\-]*(\d+)', text.upper())
    return match.group(1) if match else None


def extract_nf_ref_pattern(text):
    """Extract NF_REF number pattern"""
    match = re.search(r'NF_REF[\s\-]*(\d+)', text.upper())
    return match.group(1) if match else None


def extract_nfeletr_pattern(text):
    """Extract NFELETR number pattern"""
    match = re.search(r'NFELETR[\s\-]*(\d+)', text.upper())
    return match.group(1) if match else None


def extract_apolice_pattern(text):
    """Extract APÓLICE number pattern"""
    match = re.search(r'APÓLICE[\s\-]*(\d+)', text.upper())
    return match.group(1) if match else None


def extract_first_number_with_keywords(text):
    """Extract first number from text containing target keywords"""
    target_keywords = ['FATURA', 'NFES', 'BOLETO', 'DÉB', 'CONTRATO', 'APÓLICE']
    
    has_keyword = any(keyword in text.upper() for keyword in target_keywords)
    has_nfeletr = 'NFELETR' in text.upper()
    has_date = bool(re.search(r'\d{2}/\d{2}/\d{4}', text))

    if has_keyword or has_nfeletr or has_date:
        numbers = re.findall(r'\d+', text)
        if numbers:
            return numbers[0]
    return None


def extract_nota_from_parsed(complemento_parsed):
    """Extract nota number from parsed complemento using various patterns"""
    if not isinstance(complemento_parsed, list):
        return None

    # First, try to find NF bracket pattern in full text
    full_text = ' '.join(str(item) for item in complemento_parsed if isinstance(item, str))
    nf_bracket_result = extract_nf_bracket_pattern(full_text)
    if nf_bracket_result:
        return nf_bracket_result

    # Then try each pattern on individual items
    for item in complemento_parsed:
        if not isinstance(item, str):
            continue

        # Try all extraction patterns in order of priority
        patterns = [
            extract_nf_bracket_pattern,
            extract_date_number_pattern,
            extract_nfes_pattern,
            extract_nf_ref_pattern,
            extract_nfeletr_pattern,
            extract_apolice_pattern,
            extract_first_number_with_keywords
        ]

        for pattern_func in patterns:
            result = pattern_func(item)
            if result:
                return result

    return None