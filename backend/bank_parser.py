import pandas as pd
import io
import re

class BankParser:
    @staticmethod
    def clean_description(raw_desc):
        desc = str(raw_desc).strip()
        
        # Google Pay
        if "GOOGLE PAY" in desc.upper():
            match = re.search(r'Google Pay (.*?)(?:,PAS|, NR|/|$)', desc, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Mobile Pay / BEA
        if desc.startswith("BEA"):
            merchant_match = re.search(r'(?:BEA, [^ ]+ +)(.*?)(?:,PAS| NR:|/|$)', desc)
            if merchant_match:
                return merchant_match.group(1).strip()
            
        # ABN AMRO / SEPA / TRTP
        if "/NAME/" in desc:
            name_match = re.search(r'/NAME/(.*?)(?:/|$)', desc)
            name = name_match.group(1).strip() if name_match else ""
            
            remi_match = re.search(r'/REMI/(.*?)(?:/|$)', desc)
            remi = remi_match.group(1).strip() if remi_match else ""
            
            # Clean up Tikkie / Payment provider names
            if any(x in name.upper() for x in ["TIKKIE", "MOLLIE", "ADYEN", "DERDENGELDEN", "PAY.NL", "BUCKAROO"]):
                if remi:
                    cleaned_remi = re.sub(r'Tikkie ID [\d\w]+,?', '', remi)
                    cleaned_remi = re.sub(r'/?EREF/.*', '', cleaned_remi)
                    cleaned_remi = re.sub(r'[A-Z]{2}\d{2}[A-Z]{4}\d{10}', '', cleaned_remi)
                    
                    if cleaned_remi.strip():
                        return cleaned_remi.strip(", ")
            
            if name and remi:
                return f"{name} - {remi}"
            return name or desc

        desc = re.sub(r' {2,}', ' ', desc)
        return desc

    @staticmethod
    def categorize(desc):
        desc_upper = desc.upper()
        categories = {
            'Boodschappen': ['AH', 'ALBERT HEIJN', 'JUMBO', 'LIDL', 'ALDI', 'DIRK', 'COOP', 'PLUS'],
            'Horeca': ['LOETJE', 'SUBWAY', 'DINNER', 'CAFE', 'RESTAURANT', 'BEER', 'BAR', 'PIZZA', 'BAGELS'],
            'Vervoer': ['NS ', 'UBER', 'BOLT', 'SHELL', 'FUEL', 'PARKING', 'GAS'],
            'Vaste Lasten': ['HUUR', 'RENT', 'ELECTRICITY', 'ZORGVERZEKERING', 'VGZ', 'FBTO', 'COOLBLUE'],
            'Entertainment': ['CINEMA', 'NETFLIX', 'SPOTIFY', 'STORYTEL', 'CONCERT', 'MUSEUM'],
            'Sport': ['TRAINMORE', 'GYM', 'BASIC-FIT', 'PADEL'],
        }
        
        for cat, keywords in categories.items():
            if any(k in desc_upper for k in keywords):
                return cat
        return "Overig"

    @staticmethod
    def extract_time(desc):
        match = re.search(r'(\d{2}:\d{2})', str(desc))
        return match.group(1) if match else "00:00"

    @staticmethod
    def parse_ing_csv(file_content):
        df = pd.read_csv(io.StringIO(file_content))
        
        parsed_data = []
        for _, row in df.iterrows():
            raw_amount = str(row['Bedrag (EUR)']).replace(',', '.')
            amount = float(raw_amount)
            if row['Af Bij'] == 'Af':
                amount = -amount
            
            raw_desc = f"{row['Naam / Omschrijving']} - {row['Mededelingen']}"
            cleaned_desc = BankParser.clean_description(raw_desc)
            
            parsed_data.append({
                'date': str(row['Datum']),
                'time': BankParser.extract_time(raw_desc),
                'description': cleaned_desc,
                'raw_description': raw_desc,
                'category': BankParser.categorize(cleaned_desc),
                'amount': amount
            })
        return parsed_data

    @staticmethod
    def parse_abn_csv(file_content):
        df = pd.read_csv(io.StringIO(file_content), sep='\t', header=None, 
                         names=['Account', 'Currency', 'Date', 'StartBal', 'EndBal', 'IntDate', 'Amount', 'Description'])
        
        df['time_sort'] = df['Description'].apply(BankParser.extract_time)
        df = df.sort_values(by=['Date', 'time_sort'], ascending=[False, False])
        
        parsed_data = []
        for _, row in df.iterrows():
            date_str = str(row['Date'])
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            amount = float(str(row['Amount']).replace(',', '.'))
            
            raw_desc = str(row['Description']).strip()
            cleaned_desc = BankParser.clean_description(raw_desc)
            
            parsed_data.append({
                'date': formatted_date,
                'time': row['time_sort'],
                'description': cleaned_desc,
                'raw_description': raw_desc,
                'category': BankParser.categorize(cleaned_desc),
                'amount': amount
            })
        return parsed_data
