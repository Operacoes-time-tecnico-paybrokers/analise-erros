import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import pandas as pd
import requests
import pyotp
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

HTTP_OK = 200
HTTP_CREATED = 201
GREEN = "\033[92m"
RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
BASE_URL = 'https://api.pagfast.com/v1/corporate'
LOGIN_URL = f'{BASE_URL}/auth/login'
MFA_URL = f'{BASE_URL}/auth/mfa/validate'
BASE_URL_TRANSATIONS = 'https://api.pagfast.com/v1/corporate/accounts/transactions/pix'
MAX_MFA_ATTEMPTS = 4

headers = {
    'Content-Type': 'application/json',
}

USERNAME = ''
PASSWORD = ''
MFA_SECRET = ''

class TransactionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Configuração de Transação")
        self.root.geometry("600x650")
        self.root.configure(bg="#f2f2f2")
        self.is_running = False  

        style = ttk.Style()
        style.configure("TLabel",font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10, "bold"))
        style.configure("TCheckbutton", )

        # Configuração do arquivo
        self.file_path = tk.StringVar()
        ttk.Label(root, text="Selecionar Arquivo XLSX:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(root, textvariable=self.file_path, width=30).grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(root, text="Procurar", command=self.select_file).grid(row=0, column=2, padx=10, pady=10)

        # Configuração do local de saída
        self.output_dir = tk.StringVar()
        ttk.Label(root, text="Selecionar Diretório de Saída:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(root, textvariable=self.output_dir, width=30).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(root, text="Procurar", command=self.select_output_dir).grid(row=1, column=2, padx=10, pady=10)

        # Configuração de parâmetros
        ttk.Label(root, text="ID Coluna:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.coluna_id = ttk.Entry(root)
        self.coluna_id.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(root, text="Data Início:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.start_date = DateEntry(root, date_pattern='dd/mm/yyyy', background="darkblue", foreground="white", borderwidth=2)
        self.start_date.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(root, text="Data Fim:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.end_date = DateEntry(root, date_pattern='dd/mm/yyyy', background="darkblue", foreground="white", borderwidth=2)
        self.end_date.grid(row=4, column=1, padx=10, pady=5)

        # Seleção de Tipo e IDs
        ttk.Label(root, text="Tipo de Transação:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.type_option = ttk.Combobox(root, values=["Credit", "Debit"])
        self.type_option.set("Credit")
        self.type_option.grid(row=5, column=1, padx=10, pady=5)

        self.id_plataforma = tk.BooleanVar()
        self.id_pagfast = tk.BooleanVar()
        self.e2e = tk.BooleanVar()
        ttk.Checkbutton(root, text="ID Plataforma", variable=self.id_plataforma).grid(row=6, column=0, padx=10, pady=5, sticky="w")
        ttk.Checkbutton(root, text="ID PagFast", variable=self.id_pagfast).grid(row=6, column=1, padx=10, pady=5, sticky="w")
        ttk.Checkbutton(root, text="E2E", variable=self.e2e).grid(row=6, column=2, padx=10, pady=5, sticky="w")

        # Label e Barra de Progresso
        self.progress_label = ttk.Label(root, text="Progresso: 0/0 linhas processadas")
        self.progress_label.grid(row=7, column=0, columnspan=3, pady=10)
        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

        # Botões para Executar e Parar
        self.start_button = ttk.Button(root, text="Processar Transações", command=self.start_processing)
        self.start_button.grid(row=9, column=1, padx=10, pady=20)
        self.stop_button = ttk.Button(root, text="Parar", command=self.stop_processing, state="disabled")
        self.stop_button.grid(row=9, column=2, padx=10, pady=20)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.file_path.set(file_path)

    def select_output_dir(self):
        output_dir = filedialog.askdirectory()
        if output_dir:
            self.output_dir.set(output_dir)

    def start_processing(self):
        file_path = self.file_path.get()
        output_dir = self.output_dir.get()
        
        if not file_path:
            messagebox.showerror("Erro", "Por favor, selecione um arquivo XLSX.")
            return
        if not output_dir:
            messagebox.showerror("Erro", "Por favor, selecione um diretório de saída.")
            return

        try:
            coluna_id = int(self.coluna_id.get())
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um valor numérico para o ID da Coluna.")
            return

        start_date = self.start_date.get_date().strftime('%Y-%m-%d')
        end_date = self.end_date.get_date().strftime('%Y-%m-%d')
        transaction_type = self.type_option.get()
        id_plataforma = self.id_plataforma.get()
        id_pagfast = self.id_pagfast.get()
        e2e = self.e2e.get()

        token = login()
        if not token:
            messagebox.showerror("Erro", "Falha no login ou MFA.")
            return

        headers['Authorization'] = f'Bearer {token}'
        
        self.is_running = True
        self.stop_button.config(state="normal")
        self.start_button.config(state="disabled")
        
        self.process_transactions(file_path, output_dir, coluna_id, start_date, end_date, transaction_type, id_plataforma, id_pagfast, e2e)

    def stop_processing(self):
        self.is_running = False
        self.stop_button.config(state="disabled")
        self.start_button.config(state="normal")
        messagebox.showinfo("Parado", "O processamento foi interrompido.")

    def process_transactions(self, file_path, output_dir, coluna_id, start_date, end_date, transaction_type, id_plataforma, id_pagfast, e2e):
        try:
            df = pd.read_excel(file_path)
            total_rows = len(df)
            self.progress_bar["maximum"] = total_rows
            results = []
            processed_rows = 0
            found_transactions = 0

            output_file_name = f"resultados_{os.path.basename(file_path)}"
            output_file_path = os.path.join(output_dir, output_file_name)

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(process_transaction, row.iloc[coluna_id], start_date, end_date, transaction_type, id_plataforma, id_pagfast, e2e) for index, row in df.iterrows()]
                for future in as_completed(futures):
                    if not self.is_running: 
                        executor.shutdown(wait=False)
                        break

                    result = future.result()
                    results.extend(result)
                    processed_rows += 1
                    if result:
                        found_transactions += len(result)

                    # Atualizar a barra de progresso e a label
                    self.progress_bar["value"] = processed_rows
                    self.progress_label.config(text=f"Progresso: {processed_rows}/{total_rows} linhas processadas, {found_transactions} transações encontradas")
                    self.root.update_idletasks()

            if self.is_running and results:
                results_df = pd.DataFrame(results)
                results_df.to_excel(output_file_path, index=False)
                messagebox.showinfo("Concluído", f"Processamento completo. Resultados salvos em:\n{output_file_path}")
            elif not self.is_running:
                messagebox.showinfo("Interrompido", "Processamento interrompido pelo usuário.")
            else:
                messagebox.showwarning("Aviso", "Nenhum dado de transação encontrado.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
        finally:
            self.is_running = False
            self.stop_button.config(state="disabled")
            self.start_button.config(state="normal")

def login():
    print('\n===== Login Corporate Developer Successful.')
    login_data = {'login': USERNAME, 'password': PASSWORD}
    response = requests.post(LOGIN_URL, headers=headers, json=login_data)
    if response.status_code != HTTP_CREATED:
        print('Login failed.')
        return None

    headers['Authorization'] = f'Bearer {response.text}'
    
    for _ in range(MAX_MFA_ATTEMPTS):
        totp = pyotp.TOTP(MFA_SECRET)
        mfa_code = totp.now()
        mfa_data = {'app': mfa_code}

        response = requests.post(MFA_URL, headers=headers, json=mfa_data)

        if response.status_code == HTTP_CREATED:
            print('MFA successful.')
            return response.text
        else:
            print('MFA failed. Retrying...')
    
    print('MFA failed after maximum attempts.')
    return None

def process_transaction(transaction_order_id, start_date, end_date, transaction_type, id_plataforma, id_pagfast, e2e):
    try:
        transaction_order_id = str(transaction_order_id).split('.')[0]
        print(f"Buscando por {transaction_order_id}")

        if not transaction_order_id:
            print("ID de transação inválido.")
            return []

        query_params = {
            'dataset.limit': '50',
            'dataset.offset': '0',
            'transactionType': transaction_type,
            'startDate': f"{start_date}T00:00:00.000Z",
            'endDate': f"{end_date}T23:59:59.999Z"
        }

        if id_plataforma:
            query_params['transactionOrderId'] = transaction_order_id  # BUSCAR POR ID PLATAFORMA
        elif id_pagfast:
            query_params['transactionId'] = transaction_order_id  # BUSCAR POR ID PAGFAST
        elif e2e:
            query_params['transactionReceiptVoucher'] = transaction_order_id  # BUSCAR POR E2E

        response = requests.get(BASE_URL_TRANSATIONS, params=query_params, headers=headers)
        
        try:
            response_json = response.json()
        except ValueError:
            print("Erro ao decodificar JSON da resposta.")
            return []
        
        if 'data' in response_json and 'items' in response_json['data']:
            results = []
            items = response_json['data']['items']
            
            if not items:
                print(f"{YELLOW}Transação não encontrada.{RESET}")
                return results
           
            for item in items:
                transactionItens = item.get('transaction')
                if not transactionItens:
                    print("Item sem dados de transação.")
                    continue
                
                id = transactionItens.get('id')
                if not id:
                    print("Transação sem ID.")
                    continue

                try:
                    responseDetail = requests.get(BASE_URL_TRANSATIONS + '/' + id, headers=headers)
                    if responseDetail.status_code == 200:
                        response_detail = responseDetail.json()
                        transaction = response_detail['data'].get('transaction', {})
                        webhook = response_detail['data'].get('webhook', {})
                        
                        transaction_type = transaction.get('type')
                        
                        if transaction_type == 'Debit':
                            recipient_info = transactionItens.get('recipient')
                            recipient_name = recipient_info.get('name') if recipient_info else None
                            recipient_taxnumber = recipient_info.get('taxNumber') if recipient_info else None
                            payer_name = None
                            payer_taxnumber = None
                        elif transaction_type == 'Credit':
                            payer_info = transactionItens.get('payer')
                            payer_name = payer_info.get('name') if payer_info else None
                            payer_taxnumber = payer_info.get('taxNumber') if payer_info else None
                            recipient_name = None
                            recipient_taxnumber = None
                        else:
                            payer_name = None
                            payer_taxnumber = None
                            recipient_name = None
                            recipient_taxnumber = None
                            print("Tipo de transação desconhecido.")

                        results.append({
                            'PAGFAST ID': transaction.get('id'),
                            'PLATAFORM ID': transaction.get('orderId'),
                            'DATE': transaction.get('date'),
                            'VALUE': transaction.get('amount'),
                            'NAME': recipient_name if transaction_type == 'Debit' else payer_name,
                            'TAXNUMBER': recipient_taxnumber if transaction_type == 'Debit' else payer_taxnumber,
                            'STATUS': transaction.get('state'),
                            'WEBHOOK STATUS': webhook.get('deliveryStatus')
                        })
 
                        print(f"{GREEN}Transação ENCONTRADA: {transaction.get('orderId')}{RESET}")
                       
                    else:
                        print(f"Erro na requisição para ID {id}: Status code {responseDetail.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"{RED}Erro de requisição para ID {id}: {e}{RESET}")
            
            return results
        else:
            print("Resposta JSON inválida ou dados de transação ausentes.")
            return []
    except Exception as e:
        print(f"Ocorreu um erro ao processar a transação: {e}")
        return []

if __name__ == '__main__':
    root = tk.Tk()
    app = TransactionApp(root)
    root.mainloop()
