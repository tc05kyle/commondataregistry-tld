"""Examples and utilities for the new IP-like canonical ID system"""
from database.canonical_id_system import canonical_id_service

def generate_examples():
    """Generate example canonical IDs to demonstrate the new format"""
    examples = [
        {
            'name': 'John Smith',
            'first_name': 'John',
            'last_name': 'Smith',
            'phone': '+1-555-123-4567',
            'email': 'john.smith@domain.com',
            'expected_id': 'J.SMITH.4567.john.smith@domain.com'
        },
        {
            'name': 'Maria Garcia-Rodriguez',
            'first_name': 'Maria',
            'last_name': 'Garcia-Rodriguez',
            'phone': '(555) 987-6543',
            'email': 'maria@tech.startup.io',
            'expected_id': 'M.GARCIARODRIGUEZ.6543.maria@tech.startup.io'
        },
        {
            'name': 'Alex Chen',
            'first_name': 'Alex',
            'last_name': 'Chen',
            'phone': '555.555.1000',
            'email': 'a.chen@university.edu',
            'expected_id': 'A.CHEN.1000.a.chen@university.edu'
        },
        {
            'name': 'Dr. Sarah O\'Connor',
            'first_name': 'Sarah',
            'last_name': "O'Connor",
            'phone': '1-800-555-2020',
            'email': 'dr.sarah@medical.center.org',
            'expected_id': 'S.OCONNOR.2020.dr.sarah@medical.center.org'
        }
    ]
    
    return examples

def explain_format():
    """Explain the canonical ID format structure"""
    return {
        'format': 'FirstInitial.LastName.Last4Phone.FullEmail',
        'segments': {
            '1': 'First Initial - Single uppercase letter from first name',
            '2': 'Last Name - Cleaned last name (letters only, uppercase)',
            '3': 'Phone Digits - Last 4 digits of primary phone number',
            '4': 'Full Email - Complete email address (lowercase)'
        },
        'examples': {
            'individual': 'J.SMITH.1234.jsmith@hotmail.com',
            'organization': 'ORG.ACMECORP.5000.contact@acme.biz',
            'with_counter': 'J.SMITH.1234.jsmith@hotmail.com.01'
        },
        'benefits': [
            'Fully identifies the person with email context',
            'Hierarchical structure like IP addresses',
            'Easy to parse and validate',
            'Supports collision resolution with counters',
            'Can group by email domains and providers',
            'Direct email contact information embedded'
        ],
        'network_analogy': {
            'description': 'Like IP addresses, canonical IDs can be grouped by segments',
            'examples': {
                'same_company': ['J.SMITH.1234.jsmith@acme.com', 'M.JONES.5678.mjones@acme.com'],
                'same_provider': ['J.SMITH.1234.jsmith@gmail.com', 'A.DOE.5678.adoe@gmail.com'],
                'same_family': ['J.SMITH.1234.john@smithfamily.com', 'M.SMITH.5678.mary@smithfamily.com']
            }
        }
    }

def validate_canonical_id_examples():
    """Test canonical ID validation with various formats"""
    test_cases = [
        {'id': 'J.SMITH.1234.jsmith@hotmail.com', 'valid': True, 'reason': 'Standard format'},
        {'id': 'J.SMITH.1234.jsmith@hotmail.com.01', 'valid': True, 'reason': 'With counter'},
        {'id': 'A.VERYLONGNAME.5678.alex@company.org', 'valid': True, 'reason': 'Long last name'},
        {'id': 'J.SMITH.1234.j.smith@sub.domain.com', 'valid': True, 'reason': 'Email with dots'},
        {'id': 'JSmith1234jsmith@hotmail.com', 'valid': False, 'reason': 'No periods'},
        {'id': 'J.smith.1234.jsmith@hotmail.com', 'valid': False, 'reason': 'Lowercase name'},
        {'id': 'J.SMITH.12345.jsmith@hotmail.com', 'valid': False, 'reason': 'Phone too long'},
        {'id': 'J.SMITH.123.jsmith@hotmail.com', 'valid': False, 'reason': 'Phone too short'},
        {'id': 'JJ.SMITH.1234.jsmith@hotmail.com', 'valid': False, 'reason': 'Multiple initials'},
        {'id': 'J.SMITH.1234.invalid-email', 'valid': False, 'reason': 'Invalid email format'},
    ]
    
    results = []
    for case in test_cases:
        is_valid = canonical_id_service.validate_canonical_id_format(case['id'])
        results.append({
            'canonical_id': case['id'],
            'expected_valid': case['valid'],
            'actual_valid': is_valid,
            'test_passed': is_valid == case['valid'],
            'reason': case['reason']
        })
    
    return results

def demo_parsing():
    """Demonstrate parsing canonical IDs into components"""
    test_ids = [
        'J.SMITH.1234.jsmith@hotmail.com',
        'M.GARCIA.5678.maria@company.org.01',
        'A.CHEN.9999.a.chen@university.edu',
        'S.OCONNOR.0123.sarah@medical.center.gov.99'
    ]
    
    parsed_results = []
    for canonical_id in test_ids:
        components = canonical_id_service.parse_canonical_id(canonical_id)
        parsed_results.append({
            'canonical_id': canonical_id,
            'components': components
        })
    
    return parsed_results