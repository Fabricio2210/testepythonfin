# Excel and Composições Processor

A Python application for processing and merging Excel files with composições data, applying intelligent grouping logic and generating consolidated reports.

## Features

- **Multi-source Processing**: Handles both Excel files and composições data
- **Intelligent Parsing**: Extracts nota numbers and company names from complex text patterns
- **Smart Grouping**: Applies sophisticated logic to group and deduplicate records
- **Company Deduplication**: Removes duplicate entries based on company name patterns
- **Excel Generation**: Creates consolidated Excel reports with processed data
- **Modular Architecture**: Clean, maintainable code structure with separation of concerns

## Project Structure

```
├── main.py                     # Main entry point
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── data_utils.py          # Data manipulation and JSON utilities
│   └── regex_patterns.py      # Regex patterns for text extraction
├── parsers/                    # Text parsing logic
│   ├── __init__.py
│   └── complemento_parser.py  # Complemento text parsing
├── processors/                 # Business logic processors
│   ├── __init__.py
│   ├── file_processor.py      # File processing logic
│   ├── grouping_logic.py      # Grouping and deduplication
│   └── excel_generator.py     # Excel file generation
├── excel/                      # Input Excel files
├── composicoes/               # Input composições files
├── output/                    # Generated output files
└── merged_data.json           # Processed data in JSON format
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd excel-composicoes-processor
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install pandas openpyxl numpy
   ```

## Usage

1. **Prepare your data**:
   - Place Excel files in the `excel/` directory
   - Place composições files in the `composicoes/` directory

2. **Run the processor**:
   ```bash
   python main.py
   ```

3. **Enter project value**:
   - When prompted, enter the total project value (e.g., `1000000.50`)

4. **Check results**:
   - Processed Excel files will be saved in the `output/` directory
   - Merged data will be available in `merged_data.json`

## Processing Logic

### Grouping Rules

The application applies intelligent grouping logic:

1. **Equal Values Division**: When all soma values in a group have the same integer part, the total is divided by the unit value to determine the number of rows to create.

2. **Different Values Sum**: When soma values differ, they are summed together into a single record.

### Deduplication

- **Value-based**: Removes exact duplicates with same nota, empresa, Valor, and Valor_Total
- **Company-based**: Removes duplicates with same valor_nota and Valor but different company names, prioritizing entries without corporate suffixes (LTDA, S.A, S/A)

### Text Parsing

The system extracts information using sophisticated regex patterns:

- **Nota Numbers**: From various formats (NF <123>, NFES-456, etc.)
- **Company Names**: Identifies companies by corporate suffixes
- **Document References**: Extracts invoice and document numbers

## Data Sources

### Excel Files
- Processes standard Excel files with financial data
- Extracts nota, empresa, and value information
- Supports multiple sheets per file

### Composições Files
- Handles composições data with complemento text parsing
- Extracts structured information from unstructured text
- Calculates soma_notas based on matching criteria

## Output

### Excel Files
Generated Excel files contain:
- `nota`: Invoice/document number
- `empresa`: Company name
- `Valor`: Individual value
- `Valor_Total`: Total value for the group
- `total da planilha`: Sum of all Valor_Total in the file

### JSON Data
The `merged_data.json` file includes:
- Processing summary with statistics
- All grouped records with metadata
- Source tracking (excel vs composicoes)

## Configuration

### File Locations
- Input Excel files: `excel/` directory
- Input composições: `composicoes/` directory
- Output files: `output/` directory

### Processing Parameters
- Project total value: Entered at runtime
- Grouping logic: Configurable in `processors/grouping_logic.py`
- Regex patterns: Defined in `utils/regex_patterns.py`

## Development

### Adding New Patterns
To add new regex patterns for nota extraction:

1. Add the pattern function to `utils/regex_patterns.py`
2. Include it in the `extract_nota_from_parsed` function
3. Test with sample data

### Modifying Grouping Logic
Grouping rules can be customized in `processors/grouping_logic.py`:

- Modify `apply_grouping_logic()` for new grouping rules
- Update deduplication logic in `deduplicate_by_valor()`
- Adjust company filtering in `remove_company_duplicates()`

### Testing
Run the application with sample data to verify:
- Correct nota extraction from various text formats
- Proper grouping and deduplication
- Accurate Excel file generation

## Troubleshooting

### Common Issues

1. **Missing Dependencies**:
   ```bash
   pip install pandas openpyxl numpy
   ```

2. **File Not Found**:
   - Ensure input files are in correct directories
   - Check file permissions

3. **Invalid Data**:
   - Verify Excel file format and structure
   - Check for corrupted files

4. **Memory Issues**:
   - For large datasets, consider processing files individually
   - Monitor memory usage during processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the existing code structure
4. Test thoroughly with sample data
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.