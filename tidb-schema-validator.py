import argparse
import glob
import os
import re
import sys

# support charsets
SUPPORTED_CHARSETS = {'utf8mb4', 'latin1', 'ascii', 'binary', 'gbk'}

# support collations
SUPPORTED_COLLATIONS = {
    'utf8mb4_bin', 'utf8mb4_general_ci', 'utf8mb4_unicode_ci', 'utf8mb4_0900_ai_ci', 'utf8mb4_0900_bin',
    'ascii_bin',
    'latin1_bin',
    'binary',
    'gbk_bin', 'gbk_chinese_ci'
}

# check rules
DETECTION_RULES = [
    {
        'name': 'Stored Procedures',
        'pattern': re.compile(r'^\s*CREATE\s+PROCEDURE\b', re.IGNORECASE),
        'action': 'remove',
        'message': 'TiDB does not support stored procedures. Removing procedure definition.'
    },
    {
        'name': 'Triggers',
        'pattern': re.compile(r'^\s*CREATE\s+TRIGGER\b', re.IGNORECASE),
        'action': 'remove',
        'message': 'TiDB does not support triggers. Removing trigger definition.'
    },
    {
        'name': 'Events',
        'pattern': re.compile(r'^\s*CREATE\s+EVENT\b', re.IGNORECASE),
        'action': 'remove',
        'message': 'TiDB does not support events. Removing event definition.'
    },
    {
        'name': 'User-Defined Functions',
        'pattern': re.compile(r'^\s*CREATE\s+FUNCTION\b', re.IGNORECASE),
        'action': 'remove',
        'message': 'TiDB does not support user-defined functions. Removing function definition.'
    },
    {
        'name': 'Full-Text Indexes',
        'pattern': re.compile(r'\bFULLTEXT\b', re.IGNORECASE),
        'action': 'remove_line',
        'message': 'TiDB does not support FULLTEXT indexes. Removing index definition.'
    },
    {
        'name': 'Spatial Indexes',
        'pattern': re.compile(r'\bSPATIAL\b', re.IGNORECASE),
        'action': 'remove_line',
        'message': 'TiDB does not support SPATIAL indexes. Removing index definition.'
    },
    {
        'name': 'Unsupported Character Sets',
        'pattern': re.compile(r'CHARACTER\s+SET\s+(\w+)', re.IGNORECASE),
        'action': 'force_replace_to_utf8mb4',
        'replace': 'CHARACTER SET utf8mb4',
        'message': 'Unsupported character set. Replacing with utf8mb4. 1'
    },
    {
        'name': 'Unsupported Character Sets',
        'pattern': re.compile(r'CHARSET\s*=\s*(\w+)', re.IGNORECASE),
        'action': 'force_replace_to_utf8mb4',
        'replace': 'CHARSET=utf8mb4',
        'message': 'Unsupported charet=. Replacing with utf8mb4. 2'
    },
    {
        'name': 'Unsupported COLLATE',
        'pattern': re.compile(r'COLLATE\s+(\w+)', re.IGNORECASE),
        'action': 'force_replace_to_utf8mb4_bin',
        'replace': 'COLLATE utf8mb4_bin',
        'message': 'Unsupported COLLATE. Replacing with utf8mb4_bin. 3'
    },
    {
        'name': 'Unsupported COLLATE',
        'pattern': re.compile(r'COLLATE\s*=\s*(\w+)', re.IGNORECASE),
        'action': 'force_replace_to_utf8mb4_bin',
        'replace': 'COLLATE = utf8mb4_bin',
        'message': 'Unsupported COLLATE=. Replacing with utf8mb4_bin. 4'
    },
    {
        'name': 'Column-Level Privileges',
        'pattern': re.compile(r'GRANT\s+.*?\([^)]+\)', re.IGNORECASE),
        'action': 'remove_line',
        'message': 'TiDB does not support column-level privileges. Removing grant statement.'
    },
    {
        'name': 'Tablespace Creation',
        'pattern': re.compile(r'CREATE\s+TABLESPACE\b', re.IGNORECASE),
        'action': 'remove_line',
        'message': 'TiDB does not support TABLESPACE. Removing tablespace definition.'
    },
    {
        'name': 'Descending Indexes',
        'pattern': re.compile(r'\bDESC\b', re.IGNORECASE),
        'action': 'remove_keyword',
        'remove': 'DESC',
        'message': 'TiDB ignores DESC in indexes. Removing DESC keyword.'
    },
    {
        'name': 'Subpartitioning',
        'pattern': re.compile(r'\bSUBPARTITION\b', re.IGNORECASE),
        'action': 'remove_line',
        'message': 'TiDB does not support subpartitioning. Removing subpartition definition.'
    },
    {
        'name': 'Subpartitions',
        'pattern': re.compile(r'\bSUBPARTITIONS\b\s+\d+', re.IGNORECASE),
        'action': 'replace',
        'replace': '',
        'message': 'TiDB does not support subpartitions Removing subpartitions definition.'
    },
    {
        'name': 'Auto-increment Behavior',
        'pattern': re.compile(r'\bAUTO_INCREMENT[^=]', re.IGNORECASE),
        'action': 'warn',
        'message': 'Note: TiDB auto_increment is instance-scoped monotonic but not cluster-wide continuous. '
                   'For global monotonicity, add AUTO_ID_CACHE=1.'
    },
    {
        'name': 'Auto-increment BigintType',
        'pattern': re.compile(r'\s(TINYINT|SMALLINT|MEDIUMINT|INT).*\bAUTO_INCREMENT[^=]', re.IGNORECASE),
        'action': 'warn',
        'message': 'Note: The data type of this auto_increment field is not BIGINT, which poses a risk of overflow.'
    },
    {
        'name': 'Row Format',
        'pattern': re.compile(r'\bROW_FORMAT\s*=\s*\w+', re.IGNORECASE),
        'action': 'replace',
        'replace': '',
        'message': 'TiDB does not support ROW_FORMAT. This option will be ignored.'
    }
]

def check_compatibility(input_file, apply_fix=False):
    """ MySQL schema SQL ファイルの互換性チェック """
    warnings = []
    output_lines = []
    in_delimiter_block = False
    delimiter_block_lines = []
    block_start_line = 0
    
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i]
        line_num = i + 1
        original_line = line
        
        # process DELIMITER block (Procedure , function, trigger)
        if line.strip().upper() == 'DELIMITER ;;':
            in_delimiter_block = True
            delimiter_block_lines = [line]
            block_start_line = line_num
            i += 1
            continue
        
        if in_delimiter_block:
            delimiter_block_lines.append(line)
            if line.strip().upper() == 'DELIMITER ;':
                in_delimiter_block = False
                block_content = ''.join(delimiter_block_lines)
                
                # check rules in the block
                block_warning = None
                if re.search(r'CREATE\s+PROCEDURE\b', block_content, re.IGNORECASE):
                    block_warning = 'Stored procedure'
                elif re.search(r'CREATE\s+FUNCTION\b', block_content, re.IGNORECASE):
                    block_warning = 'User-defined function'
                elif re.search(r'CREATE\s+TRIGGER\b', block_content, re.IGNORECASE):
                    block_warning = 'Trigger'
                
                if block_warning:
                    warnings.append((block_start_line, 
                                    f'{block_warning} is not supported by TiDB'))
                    if not apply_fix:
                        # add comment when do not apply_fix
                        output_lines.append(f'/* TiDB INCOMPATIBLE: {block_warning.upper()} REMOVED */\n')
                else:
                    # normal line
                    output_lines.extend(delimiter_block_lines)
            
            i += 1
            continue
        
        # check create table block
        if line.strip().upper().startswith('CREATE TABLE'):
            table_block_lines = [line]
            j = i + 1
            # block_end
            block_end_pattern = re.compile(r'^\s*\)\s*(;|\w.*;)', re.IGNORECASE)
            while j < len(lines):
                table_block_lines.append(lines[j])
                if block_end_pattern.search(lines[j]):
                    break
                j += 1
            table_content = ''.join(table_block_lines)
            if not re.search(r'\bPRIMARY\s+KEY\b', table_content, re.IGNORECASE) and \
               not re.search(r'\bUNIQUE\s+KEY\b', table_content, re.IGNORECASE):
                warnings.append((line_num, 
                                'Table without PRIMARY KEY or UNIQUE KEY is not recommended in TiDB'))

        # process single line rule
        line_modified = line
        line_warnings = []
        skip_line = False
        
        for rule in DETECTION_RULES:
            if skip_line:
                break
                
            match = rule['pattern'].search(line)
            if match:
                # charset
                if rule['name'] in ( 'Unsupported Character Sets' ) :
                    charset = match.group(1).lower()
                    if charset not in SUPPORTED_CHARSETS:
                        line_modified = rule['pattern'].sub(rule['replace'], line_modified)
                        line_warnings.append(rule['message'])
                        

                # collate
                if rule['name'] in ( 'Unsupported COLLATE' ) :
                    collate = match.group(1).lower()
                    if collate not in SUPPORTED_COLLATIONS:
                        line_modified = rule['pattern'].sub(rule['replace'], line_modified)
                        line_warnings.append(rule['message'])
                
                # desc index
                elif rule['name'] == 'Descending Indexes':
                    # process DESC only in index
                    if 'INDEX' in line.upper() or 'KEY' in line.upper():
                        line_modified = line_modified.replace(' DESC', '').replace(' desc', '')
                        line_warnings.append(rule['message'])
                
                # output warning only
                elif rule['action'] == 'warn':
                    line_warnings.append(rule['message'])
                
                # remove one line
                elif rule['action'] in ('remove_line', 'remove'):
                    skip_line = True
                    line_warnings.append(rule['message'])
                
                # replace words
                elif rule['action'] == 'replace':
                    line_modified = rule['pattern'].sub(rule['replace'], line_modified)
                    line_warnings.append(rule['message'])
        
        # collect warnings
        for warn in line_warnings:
            warnings.append((line_num, warn))
        
        # append to output
        if not skip_line:
            if apply_fix:
                output_lines.append(line_modified)
            else:
                output_lines.append(original_line)
        
        i += 1
    
    # output warnings
    for line_num, warning in warnings:
        print(f"{input_file}:{line_num} : WARNING - {warning}")
    
    # output to file when apply_fix
    if apply_fix:
        with open(input_file, 'w') as f:
            f.writelines(output_lines)
        print(f"\nSchema file has been modified in place: {input_file}")
        print("Note: Some incompatible features have been removed or modified. "
              "Review the output file and test thoroughly before using in TiDB.")

def main():
    parser = argparse.ArgumentParser(
        description='Check MySQL schema compatibility with TiDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python tidb-schema-validator.py <path or file> [filename-pattern] [--apply]
  python tidb-schema-validator.py schema.sql --apply
  python tidb-schema-validator.py ./schemas "*-schema.sql" --apply
        '''
    )
    parser.add_argument('input_path', help='Input MySQL schema SQL file or directory')
    parser.add_argument('filename_pattern', nargs='?', default='*schema.sql',
                        help='Filename pattern for directory mode (default: "*schema.sql")')
    parser.add_argument('--apply', action='store_true',
                        help='modify input file(s) in place, removing incompatible features')

    args = parser.parse_args()

    if os.path.isdir(args.input_path):
        # Directory mode
        search_pattern = os.path.join(args.input_path, args.filename_pattern)
        files = glob.glob(search_pattern)
        if not files:
            print(f"No files matched pattern: {search_pattern}")
            sys.exit(1)
        print(f"Checking TiDB compatibility for files in: {args.input_path}")
        print(f"Pattern: {args.filename_pattern}")
        print("=" * 60)
        for fpath in files:
            print(f"\nProcessing: {fpath}")
            check_compatibility(fpath, args.apply)
    elif os.path.isfile(args.input_path):
        # Single file mode
        print(f"Checking TiDB compatibility for: {args.input_path}")
        print("=" * 60)
        check_compatibility(args.input_path, args.apply)
    else:
        print(f"Error: {args.input_path} is not a valid file or directory.")
        sys.exit(1)

if __name__ == '__main__':
    main()
