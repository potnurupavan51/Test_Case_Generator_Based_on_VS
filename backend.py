from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

import pandas as pd
import json
import re
from datetime import datetime
import io

def get_llm_chain():
    """
    Creates and returns a LangChain chain that is context-aware with chat history.
    """
    load_dotenv()
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """
        You are an expert AI analyst. Answer the user's query based on the context and chat history provided below.
        If the context does not contain the answer, use your expertise to provide a relevant response.
        
        Document Context:
        {context}
        
        Chat History:
        {chat_history}
        """),
        ("user", "Query: {query}")
    ])

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY")
    )
    output_parser = StrOutputParser()
    chain = prompt_template | llm | output_parser
    
    return chain

def get_test_case_generation_chain():
    """
    Creates a specialized chain for generating test cases from client transcripts.
    """
    load_dotenv()
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """
        You are an expert test case analyst and test script writer. Analyze the provided client transcript/discussion and generate comprehensive test cases with 
         their Test scripts which anyone can run given the detailed steps given in the test scripts. The test scripts should be EXTREMELY DETAILED
         irrespective of the file size. Take time to understand the context and generate relevant test cases. 
         If you find the transcript to be big to process:
         1. Break it down into smaller sections
         2. Analyze each section for relevant test scenarios
         3. Combine the scenarios to form a comprehensive list of test cases
         4. Ensure no relevant test scenarios are missed
         5. Generate the test cases in a tabular format with the following fields
        
        While generating the test cases:
        1. Consider the application/software/system under test, its functionalities, and user roles
        2. Analyze actual user interactions in MAXIMUM detail
        3. Create COMPREHENSIVE and DETAILED test steps - each step should be specific and actionable
        4. Include ALL UI elements mentioned (buttons, fields, tabs, icons, dropdowns)
        5. Include verification steps after each major action
        6. DO NOT simplify or abbreviate - maintain maximum detail in all steps
        7. Each test step should be clear enough for someone unfamiliar with the system to execute
        8. Preconditions should list all prerequisites in detail
        9. Test data should include specific examples where applicable
        10. Include navigation paths, field names, and expected values explicitly
        
        CRITICAL REQUIREMENTS:
        - Test steps must be EXTREMELY DETAILED with 10-30+ steps per test case
        - Include every click, navigation, field entry, and verification step
        - Mention specific UI elements (buttons, tabs, dropdowns, icons) by name
        - Include verification/validation steps throughout the flow
        - Preconditions must list all setup requirements comprehensively
        - Test data must include specific realistic examples with values
        - Description should explain the complete scenario, not just a summary
        - When a test step requires visual confirmation or validation of UI elements/screens/displays, add "**Add screenshot here" in the expected_result field for that specific step
        
        IMPORTANT: You must respond with a valid JSON array containing test case objects. Each test case object must have these exact fields:
        - test_case_id: string (e.g., "TC001")
        - title: string (descriptive and specific)
        - description: string (comprehensive explanation of what is being tested)
        - preconditions: string (detailed list of all prerequisites)
        - test_steps: string (numbered steps separated by newlines - MUST BE VERY DETAILED 10-30+ steps)
        - expected_result: string (detailed expected outcome)
        - test_data: string (specific data values with examples)
        - module: string (feature/module name)
        
        Example response format:
        [
            {{
                "test_case_id": "TC001",
                "title": "Complete User Profile Setup with Account and Shipping Details in Ariba",
                "description": "Verify that a user can successfully log in to Ariba, navigate to profile settings, and update all profile information including personal details, account information, shipping address, and accounting details with complete validation at each step",
                "preconditions": "1. User has valid Ariba credentials\\n2. User has access to Ariba system\\n3. Company codes are configured in the system\\n4. GL accounts and cost centers are set up\\n5. User is assigned to appropriate groups",
                "test_steps": "1. Open web browser and navigate to Ariba URL\\n2. On the login page, locate the 'Username' field\\n3. Enter valid username in the 'Username' field\\n4. Locate the 'Password' field\\n5. Enter valid password in the 'Password' field\\n6. Click on the 'Login' button\\n7. Verify that the Ariba home page is displayed\\n8. Verify the presence of 'My Documents' tab\\n9. Verify the presence of 'My To Do' tab\\n10. Click on the user profile icon in the top right corner\\n11. Select 'Edit Profile' from the dropdown menu\\n12. On the Personal Information tab, verify pre-filled name and email\\n13. Click on 'Company Code' dropdown\\n14. Select 'US' from the company code list\\n15. Click 'Save' button\\n16. Verify success message is displayed\\n17. Navigate to 'Shipping Address' tab\\n18. Enter complete shipping address with all fields\\n19. Click 'Save and Continue'\\n20. Verify confirmation message\\n21. Click 'Submit' button\\n22. Verify profile update request is submitted successfully",
                "expected_result": "User should be able to login successfully, navigate through all profile tabs, update information in each section, see appropriate validation messages, and successfully submit the profile update request with confirmation",
                "test_data": "Username: test.user@company.com\\nPassword: Test@123\\nCompany Code: US\\nOrganization: MJ02\\nShipping Address: 123 Main St, New York, NY 10001\\nGL Account: 400001 - Office Supplies\\nCost Center: CC1001",
                "priority": "High",
                "test_type": "Functional",
                "module": "User Profile Management"
            }}
        ]
        
        Generate multiple relevant test cases based on the context. Always respond with valid JSON only. REMEMBER: MAXIMUM DETAIL IS REQUIRED.
        
        Context:
        {context}
        """),
        ("user", "Generate test cases: {query}")
    ])

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=9900,
        api_key=os.getenv("GROQ_API_KEY")
    )
    output_parser = StrOutputParser()
    chain = prompt_template | llm | output_parser
    
    return chain

def parse_test_cases_from_response(response_text):
    """
    Parse the LLM response and extract test cases data.
    Returns a pandas DataFrame suitable for Excel export.
    """
    try:
        response_text = response_text.strip()
        
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            test_cases = json.loads(json_str)
            print(f"Successfully parsed {len(test_cases)} test cases from JSON")
        else:
            print("No JSON found, creating test cases from text content")
            test_cases = [{"test_case_id": "TC001", "title": "Generated Test Case", "description": response_text[:200], 
                          "preconditions": "System access required", "test_steps": "1. Review context\n2. Execute test\n3. Validate results",
                          "expected_result": "Test executes successfully", "test_data": "As per requirements", 
                          "priority": "Medium", "test_type": "Functional", "module": "General"}]
        
        if not isinstance(test_cases, list):
            test_cases = [test_cases]
        
        # Convert escaped newlines to actual newlines in test_steps and preconditions
        for test_case in test_cases:
            if 'test_steps' in test_case and isinstance(test_case['test_steps'], str):
                test_case['test_steps'] = test_case['test_steps'].replace('\\n', '\n')
            if 'preconditions' in test_case and isinstance(test_case['preconditions'], str):
                test_case['preconditions'] = test_case['preconditions'].replace('\\n', '\n')
            if 'expected_result' in test_case and isinstance(test_case['expected_result'], str):
                test_case['expected_result'] = test_case['expected_result'].replace('\\n', '\n')
        
        df = pd.DataFrame(test_cases)
        
        required_columns = {
            'test_case_id': 'Test Case ID',
            'title': 'Test Case Title', 
            'description': 'Description',
            'preconditions': 'Preconditions',
            'test_steps': 'Test Steps',
            'expected_result': 'Expected Result',
            'test_data': 'Test Data',
            'module': 'Module/Feature'
        }
        
        for old_col, new_col in required_columns.items():
            if old_col not in df.columns:
                df[old_col] = "To be defined"
        
        df = df.rename(columns=required_columns)
        df = df[list(required_columns.values())]
        
        print(f"Created DataFrame with {len(df)} rows")
        return df
        
    except Exception as e:
        print(f"Error in parse_test_cases_from_response: {e}")
        return pd.DataFrame([{
            'Test Case ID': 'TC001',
            'Test Case Title': 'Parsing Error',
            'Description': f'Error: {e}',
            'Preconditions': 'Manual review required',
            'Test Steps': response_text[:500],
            'Expected Result': 'Successful generation after review',
            'Test Data': 'N/A',
            'Module/Feature': 'System'
        }])

def create_excel_file(test_cases_df):
    """
    Create an Excel file with test cases in a professional format.
    Each test step gets its own row in Excel.
    Returns the Excel file as bytes for download.
    """
    print(f"Creating Excel file with {len(test_cases_df)} test cases")
    
    output = io.BytesIO()
    
    try:
        expanded_rows = []
        
        for idx, row in test_cases_df.iterrows():
            test_steps = str(row['Test Steps']).split('\n')
            test_steps = [step.strip() for step in test_steps if step.strip()]
            
            # Split expected results by step if LLM provided them
            expected_results = str(row['Expected Result']).split('\n')
            expected_results = [result.strip() for result in expected_results if result.strip()]
            
            for step_num, step in enumerate(test_steps, 1):
                # Check if step requires visual confirmation and add screenshot instruction
                step_expected_result = ''
                if any(keyword in step.lower() for keyword in ['verify', 'check', 'confirm', 'validate', 'ensure', 'displayed', 'appears', 'shown', 'visible']):
                    step_expected_result = '**Add screenshot here'
                elif step_num == len(test_steps):
                    step_expected_result = row['Expected Result']
                
                # If it's the last step and has verification keywords, append to existing result
                if step_num == len(test_steps) and any(keyword in step.lower() for keyword in ['verify', 'check', 'confirm', 'validate', 'ensure', 'displayed', 'appears', 'shown', 'visible']):
                    step_expected_result = '**Add screenshot here\n' + row['Expected Result']
                
                expanded_rows.append({
                    'Test Case ID': row['Test Case ID'] if step_num == 1 else '',
                    'Test Case Title': row['Test Case Title'] if step_num == 1 else '',
                    'Description': row['Description'] if step_num == 1 else '',
                    'Preconditions': row['Preconditions'] if step_num == 1 else '',
                    'Step Number': step_num,
                    'Test Step': step,
                    'Expected Result': step_expected_result,
                    'Screenshot': '',
                    'Test Data': row['Test Data'] if step_num == 1 else ''
                })
        
        expanded_df = pd.DataFrame(expanded_rows)
        print(f"Expanded to {len(expanded_df)} rows")
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            expanded_df.to_excel(writer, sheet_name='Test Cases', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Test Cases']
            
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0055a4',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True
            })
            
            cell_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'top',
                'text_wrap': True
            })
            
            step_number_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bold': True
            })
            
            column_widths = {
                'Test Case ID': 15,
                'Test Case Title': 35,
                'Description': 40,
                'Preconditions': 35,
                'Step Number': 10,
                'Test Step': 60,
                'Expected Result': 40,
                'Screenshot': 20,
                'Test Data': 30
            }
            
            for col_num, col_name in enumerate(expanded_df.columns):
                worksheet.write(0, col_num, col_name, header_format)
                worksheet.set_column(col_num, col_num, column_widths.get(col_name, 20))
            
            step_num_col = expanded_df.columns.get_loc('Step Number')
            
            for row_num in range(len(expanded_df)):
                excel_row = row_num + 1
                for col_num in range(len(expanded_df.columns)):
                    cell_value = expanded_df.iloc[row_num, col_num]
                    if pd.isna(cell_value):
                        cell_value = ""
                    else:
                        cell_value = str(cell_value)
                    
                    fmt = step_number_format if col_num == step_num_col else cell_format
                    worksheet.write(excel_row, col_num, cell_value, fmt)
                
                worksheet.set_row(excel_row, 25)
            
            worksheet.set_row(0, 30)
            
            summary_data = {
                'Metric': ['Total Test Cases', 'Total Test Steps', 'Generated On'],
                'Value': [len(test_cases_df), len(expanded_df), datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            summary_worksheet = writer.sheets['Summary']
            summary_worksheet.set_column('A:A', 20)
            summary_worksheet.set_column('B:B', 30)
        
        excel_data = output.getvalue()
        print(f"Excel file created successfully, size: {len(excel_data)} bytes")
        return excel_data
    
    except Exception as e:
        print(f"Error creating Excel file: {e}")
        simple_output = io.BytesIO()
        test_cases_df.to_excel(simple_output, index=False)
        return simple_output.getvalue()
