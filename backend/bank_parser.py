import pandas as pd
import io

class BankParser:
    @staticmethod
    def parse_ing_csv(file_content):
        df = pd.read_csv(io.StringIO(file_content))
        
        parsed_data = []
        for _, row in df.iterrows():
            raw_amount = str(row['Bedrag (EUR)']).replace(',', '.')
            amount = float(raw_amount)
            if row['Af Bij'] == 'Af':
                amount = -amount
            
            parsed_data.append({
                'date': str(row['Datum']),
                'description': f"{row['Naam / Omschrijving']} - {row['Mededelingen']}",
                'amount': amount
            })
        return parsed_data

    @staticmethod
    def parse_abn_csv(file_content):
        # ABN AMRO often uses tab-separated values or specific CSV formatting
        df = pd.read_csv(io.StringIO(file_content), sep=None, engine='python')
        
        parsed_data = []
        for _, row in df.iterrows():
            parsed_data.append({
                'date': str(row['Transactiedatum']),
                'description': str(row['Omschrijving']),
                'amount': float(row['Transactiebedrag'])
            })
        return parsed_data
