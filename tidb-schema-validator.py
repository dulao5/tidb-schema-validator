import re
import sys
import argparse

# support charsets
SUPPORTED_CHARSETS = {'utf8mb4', 'utf8', 'latin1', 'ascii', 'binary', 'gbk'}

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
        'action': 'replace',
        'replace': 'CHARACTER SET utf8mb4',
        'message': 'Unsupported character set. Replacing with utf8mb4.'
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
        'pattern': re.compile(r'\bAUTO_INCREMENT\b', re.IGNORECASE),
        'action': 'warn',
        'message': 'Note: TiDB auto_increment is instance-scoped monotonic but not cluster-wide continuous. '
                   'For global monotonicity, add AUTO_ID_CACHE=1.'
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
                if rule['name'] == 'Unsupported Character Sets':
                    charset = match.group(1).lower()
                    if charset not in SUPPORTED_CHARSETS:
                        line_modified = rule['pattern'].sub(rule['replace'], line)
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
                    line_modified = rule['pattern'].sub(rule['replace'], line)
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
        print(f"Line {line_num}: WARNING - {warning}")
    
    # output to file when apply_fix
    if apply_fix:
        output_file = 'tidb_compatible_' + input_file
        with open(output_file, 'w') as f:
            f.writelines(output_lines)
        print(f"\nModified schema file generated: {output_file}")
        print("Note: Some incompatible features have been removed or modified. "
              "Review the output file and test thoroughly before using in TiDB.")

def main():
    parser = argparse.ArgumentParser(
        description='Check MySQL schema compatibility with TiDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python tidb-schema-validator.py schema.sql
  python tidb-schema-validator.py schema.sql --apply'''
    )
    parser.add_argument('input_file', help='Input MySQL schema SQL file')
    parser.add_argument('--apply', action='store_true', 
                        help='Generate modified schema file with fixes applied')
    
    args = parser.parse_args()
    
    print(f"Checking TiDB compatibility for: {args.input_file}")
    print("=" * 60)
    check_compatibility(args.input_file, args.apply)

if __name__ == '__main__':
    main()
