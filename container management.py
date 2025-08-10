# -*- coding: utf-8 -*-
"""
Created on Sun Aug 10 13:59:52 2025

@author: Fampride
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pytesseract
import re
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(page_title="Container Number Validator", layout="wide")

# Title and description
st.title("📦 Container Number Verification System")
st.markdown("""
Validate container numbers against ISO 6346 standards and terminal database.
Upload an image or manually enter a container number for verification.
""")

# Constants
CONTAINER_PATTERN = r"^[A-Z]{3}[UJZ][0-9]{6}[0-9]$"
LETTER_VALUES = {
    'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18,
    'I': 19, 'J': 20, 'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27,
    'Q': 28, 'R': 29, 'S': 30, 'T': 31, 'U': 32, 'V': 34, 'W': 35, 'X': 36,
    'Y': 37, 'Z': 38
}

# Sample database - replace with your actual database connection
CONTAINER_DB = pd.DataFrame({
    'container_number': ['TGHU1234565', 'MSKU9876543', 'ABCD1234561'],
    'status': ['In Yard', 'Departed', 'Invalid'],
    'last_seen': ['2023-10-15', '2023-09-20', '2023-01-01']
})

# Sidebar for additional options
with st.sidebar:
    st.header("Verification Settings")
    check_digit_validation = st.checkbox("Enable Check Digit Validation", True)
    db_validation = st.checkbox("Check Against Terminal Database", True)
    
    st.header("OCR Settings")
    preprocessing_method = st.selectbox(
        "Image Preprocessing",
        ["None", "Grayscale", "Threshold", "Edge Enhancement"]
    )

# Tab interface
tab1, tab2, tab3 = st.tabs(["Image Upload", "Manual Entry", "Report Issues"])

def calculate_check_digit(container_num):
    """Calculate the ISO 6346 check digit"""
    total = 0
    for i, char in enumerate(container_num[:10]):
        # Letters have specific values, numbers use their face value
        value = LETTER_VALUES[char] if char.isalpha() else int(char)
        # Weighting: each position is multiplied by 2^position (0-9)
        total += value * (2 ** i)
    
    check_digit = total % 11
    return str(check_digit) if check_digit < 10 else '0'

def validate_container_number(container_num, check_digit=True):
    """Validate container number format and check digit"""
    # Basic format validation
    if not re.match(CONTAINER_PATTERN, container_num):
        return False, "Format does not match XXXU1234567 pattern"
    
    # Check digit validation
    if check_digit:
        calculated_digit = calculate_check_digit(container_num[:-1])
        if container_num[-1] != calculated_digit:
            return False, f"Check digit invalid (should be {calculated_digit})"
    
    return True, "Valid container number"

def check_against_database(container_num):
    """Check if container exists in terminal database"""
    if container_num in CONTAINER_DB['container_number'].values:
        record = CONTAINER_DB[CONTAINER_DB['container_number'] == container_num].iloc[0]
        return True, f"Found in database (Status: {record['status']}, Last seen: {record['last_seen']})"
    return False, "Not found in terminal database"

def preprocess_image(image, method):
    """Apply selected preprocessing to the image"""
    img_array = np.array(image)
    
    if method == "Grayscale":
        return cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    elif method == "Threshold":
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    elif method == "Edge Enhancement":
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        return cv2.addWeighted(gray, 0.7, edges, 0.3, 0)
    else:
        return img_array

def extract_text_from_image(image):
    """Use OCR to extract text from image"""
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=custom_config)
    potential_numbers = re.findall(r"[A-Z]{3}[UJZ][0-9]{6}[0-9]?", text.upper().replace(" ", ""))
    return potential_numbers[0] if potential_numbers else None

# Image Upload Tab
with tab1:
    st.header("Image Verification")
    uploaded_file = st.file_uploader(
        "Upload container image", 
        type=["jpg", "jpeg", "png"],
        key="image_upload"
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        processed_image = preprocess_image(image, preprocessing_method)
        if preprocessing_method != "None":
            st.image(processed_image, caption="Processed Image", use_column_width=True)
        
        if st.button("Verify Container Number from Image"):
            with st.spinner("Processing image..."):
                container_number = extract_text_from_image(processed_image)
            
            if container_number:
                st.session_state.container_number = container_number
                st.success(f"Detected Container Number: {container_number}")
                
                # Perform validations
                format_valid, format_msg = validate_container_number(
                    container_number, 
                    check_digit_validation
                )
                
                db_valid, db_msg = (True, "Skipped database check") 
                if db_validation and format_valid:
                    db_valid, db_msg = check_against_database(container_number)
                
                # Display results
                st.subheader("Verification Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Format Validation:** {'✅' if format_valid else '❌'}")  
                    st.caption(format_msg)
                
                with col2:
                    st.markdown(f"**Database Check:** {'✅' if db_valid else '❌'}")  
                    st.caption(db_msg)
                
                if not format_valid or not db_valid:
                    st.error("This container number appears to be invalid or problematic")
                else:
                    st.success("Container number is valid and verified")
            else:
                st.error("Could not detect a container number in the image")

# Manual Entry Tab
with tab2:
    st.header("Manual Verification")
    container_number = st.text_input(
        "Enter Container Number", 
        value=st.session_state.get('container_number', ''),
        placeholder="e.g. TGHU1234565",
        key="manual_entry"
    ).upper().strip()
    
    if st.button("Verify Container Number"):
        if container_number:
            # Perform validations
            format_valid, format_msg = validate_container_number(
                container_number, 
                check_digit_validation
            )
            
            db_valid, db_msg = (True, "Skipped database check") 
            if db_validation and format_valid:
                db_valid, db_msg = check_against_database(container_number)
            
            # Display results
            st.subheader("Verification Results")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Format Validation:** {'✅' if format_valid else '❌'}")  
                st.caption(format_msg)
            
            with col2:
                st.markdown(f"**Database Check:** {'✅' if db_valid else '❌'}")  
                st.caption(db_msg)
            
            if not format_valid or not db_valid:
                st.error("This container number appears to be invalid or problematic")
            else:
                st.success("Container number is valid and verified")
        else:
            st.warning("Please enter a container number")

# Issue Reporting Tab
with tab3:
    st.header("Report Invalid Container")
    with st.form("report_form"):
        st.write("Report containers with incorrect numbering")
        bad_number = st.text_input("Container Number").upper()
        issue_type = st.selectbox(
            "Issue Type",
            ["Check digit mismatch", "Format incorrect", "Not in database", "Other"]
        )
        description = st.text_area("Additional Details")
        photo = st.file_uploader("Upload evidence photo", type=["jpg", "png"])
        
        submitted = st.form_submit_button("Submit Report")
        if submitted:
            # In a real app, you would save this to a database
            st.success(f"Report submitted for {bad_number}")
            st.session_state.last_report = {
                "number": bad_number,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    if "last_report" in st.session_state:
        st.info(f"Last report submitted: {st.session_state.last_report['number']} "
               f"at {st.session_state.last_report['timestamp']}")

# Add documentation
st.sidebar.markdown("""
### Container Number Format:
- 4 letters (owner code + category identifier)
- 6 digits (serial number)
- 1 check digit

Example: `TGHU1234565`
""")
