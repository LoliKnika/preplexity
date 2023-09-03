import os
import numpy as np
import pandas as pd
import time
import requests
import random
from selenium import webdriver
import numpy as np
import pandas as pd
import time
import re
import openpyxl
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip
import streamlit as st
from io import BytesIO
import base64
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from random import choice
import json

#ds=pd.read_excel(r"C:\Users\User\Desktop\cosmeticOBS\ing_bard.xlsx") # read data in excel file 

ss="Below is the description and composition of the cosmetic product, I only want to extract the chemical ingredients if they are in the description.\n"
cc="\nI want you to give me the general names of each ingredient according to INCI and CAS number in table form. I want them to be cleaned from duplications and synonyms.\nI want the answer you give me to be a table with three columns (| Name | INCI Name | CAS Number |)"
def table_read():
    try:
        table = WebDriverWait(driver1, 0.1).until(
            EC.presence_of_element_located((By.XPATH, '//table[contains(@class, "border my")]'))
        )
        table_html = table.get_attribute('outerHTML')
        df = pd.read_html(table_html, header=0)[0]
        df.insert(0,"Barcode",ds['Barcode'][i])
        df.insert(1,"Link",ds['links'][i])
    except:
        df=pd.DataFrame(columns=['CAS Number'])
    return df
def question_read(aa,driver1):
    textarea = WebDriverWait(driver1, 5).until(
        EC.presence_of_element_located((By.XPATH, "//textarea[@placeholder='Ask anything...']"))
    )
    textarea.send_keys(aa)
    textarea.send_keys(Keys.ENTER)
def check_and_waiting(url,aa,question_read,driver1,proxy):
    elements = []
    timeout = time.time() + 30  # Set timeout for 30 seconds from now
    while True:
        driver1.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        elements = driver1.find_elements(By.XPATH, "//div[contains(@class,'flex flex-row items-center gap-xs mt-sm -ml-sm')]")
        driver1.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
        if not elements:
            driver1.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            break
        if time.time() > timeout:  # Check if 30 seconds have passed
            proxy = choice(get_working_proxies())
            driver1.quit()
            options = Options()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--headless")
            options.add_argument(f"--proxy-server={proxy}")
            driver1 = Firefox(options=options)
            driver1.get(url)
            time.sleep(1)
            question_read(aa,driver1)
            timeout = time.time() + 30 
    return driver1
def get_proxies():
    proxy_url="https://github.com/clarketm/proxy-list/blob/master/proxy-list-raw.txt"
    r=requests.get(proxy_url)
    parsed_json = json.loads(r.text)
    proxy_list = parsed_json['payload']['blob']['rawLines']
    return proxy_list
def get_random_proxy(proxies):
    return({"https":choice(proxies)})
proxies=get_proxies()
def get_working_proxies():
    working=[]
    for i in range(20):
        proxy=get_random_proxy(proxies)
        print(f"using {proxy}...")
        try:
            r=requests.get("https://www.google.com",proxies==proxy,timeout=3)
            if r.status_code==200:
                working.append(proxy)
        except:
            pass
    return working

st.title("Ingredient Table Generator")
st.write("Upload an Excel file with the product descriptions")
uploaded_file = st.file_uploader("Choose a file", type="xlsx")
if uploaded_file is not None:
    ds = pd.read_excel(uploaded_file)
    df=ds
    if st.button('Confirm'):
        proxy = choice(get_working_proxies())
        big_df=pd.DataFrame()
        empty_prod=[]
        total_len = len(df)
        progress_bar = st.progress(0)
        percentage_display = st.empty()
        for i in range(total_len):
            if (i+1)%50==0:
                proxy = choice(get_working_proxies())
            progress = (i / total_len)
            progress_bar.progress(progress)
            #percentage_display.text(f"Progress: {int(progress * 100)}%")
            percentage_display.text(f"Progress: {progress * 100:.1f}%")

            options = Options()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--headless")
            options.add_argument(f"--proxy-server={proxy}")
            driver1 = Firefox(options=options)
            url="https://www.perplexity.ai/"
            driver1.get(url)
            print(i)
            a=df['ing'][i]
            aa=ss+'" '+str(a)+'" '+cc
            question_read(aa,driver1)
            driver1=check_and_waiting(url,aa,question_read,driver1,proxy)
            df_r=table_read()
            count = 0
            if len(df_r)==0:
                empty_prod.append(df['Barcode'][i])
            else:
                while (sum(df_r.iloc[:,-1]=="-")>len(df_r)/2 or df_r.iloc[:,-1].isna().sum()>len(df_r)/2) and count < 2:  
                    button = WebDriverWait(driver1, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'flex flex-row items-center gap-xs mt-sm -ml-sm')]/button[4]"))
                    )
                    button.click()
                    textarea = WebDriverWait(driver1, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "(//textarea[contains(@class,'outline-none')])"))
                    )
                    textarea.send_keys(Keys.ENTER)
                    driver1 =check_and_waiting(url,aa,question_read,driver1,proxy)
                    time.sleep(0.1)
                    df_r=table_read()
                    count += 1
            big_df=pd.concat([big_df,df_r],axis=0)
            driver1.quit()
            progress = (i + 1) / total_len
            progress_bar.progress(progress)
            #percentage_display.text(f"Progress: {int(progress * 100)}%")
            percentage_display.text(f"Progress: {progress * 100:.1f}%")

        st.write("Table with ingredients:")
        # Export the DataFrame and the empty_prod list to Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            big_df.to_excel(writer, sheet_name='Ingredients', index=False)
            pd.DataFrame({'Empty Products': empty_prod}).to_excel(writer, sheet_name='Empty Products', index=False)
        output.seek(0)

        b64 = base64.b64encode(output.read()).decode("utf-8")
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="results.xlsx">Download Results as Excel File</a>'
        st.markdown(href, unsafe_allow_html=True)


