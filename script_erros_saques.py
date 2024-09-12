import json
from datetime import datetime, timedelta

def contar_erros_bancos_e_parceiros(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

    erros = {}  
    bancos = {}  
    parceiros = {} 
    bancos_pagador = {}  
    erro_merchant_info = {} 

    for item in data:
        erro = item.get('error', 'N/A').upper()  
        banco_pagador = item.get('bank', 'N/A')
        banco_recebedor = item.get('receiver_bank_name', 'N/A')
        parceiro = item.get('merchant_name', 'N/A')
        data_erro = item.get('updatedAt', {}).get('$date', None)

       
        if data_erro:
            data_erro = datetime.strptime(data_erro, "%Y-%m-%dT%H:%M:%S.%fZ")
            data_erro = data_erro - timedelta(hours=3)  


        if erro not in erros:
            erros[erro] = 1
        else:
            erros[erro] += 1


        if banco_recebedor not in bancos:
            bancos[banco_recebedor] = 1
        else:
            bancos[banco_recebedor] += 1

        
        if parceiro not in parceiros:
            parceiros[parceiro] = 1
        else:
            parceiros[parceiro] += 1

        
        if banco_pagador not in bancos_pagador:
            bancos_pagador[banco_pagador] = 1
        else:
            bancos_pagador[banco_pagador] += 1

        
        if erro not in erro_merchant_info:
            erro_merchant_info[erro] = {}

        if parceiro not in erro_merchant_info[erro]:
            erro_merchant_info[erro][parceiro] = {
                'count': 1,
                'last_time': data_erro,
                'banco_pagador': banco_pagador,
                'banco_recebedor': banco_recebedor
            }
        else:
            erro_merchant_info[erro][parceiro]['count'] += 1

            if data_erro > erro_merchant_info[erro][parceiro]['last_time']:
                erro_merchant_info[erro][parceiro]['last_time'] = data_erro

    print("-- Erros:")
    for erro, contagem in erros.items():
        print(f'{erro}: {contagem}')

    print("\n-- Bancos Recebedores:")
    for banco, contagem in bancos.items():
        print(f'{banco}: {contagem}')

    print("\n-- Parceiros:")
    for parceiro, contagem in parceiros.items():
        print(f'{parceiro}: {contagem}')

    print("\n-- Bancos Pagadores:")
    for banco_pagador, contagem in bancos_pagador.items():
        print(f'{banco_pagador}: {contagem}')


    for erro, merchants in erro_merchant_info.items():
        print(f"\n-- Merchants com erro de {erro}:")
        for parceiro, info in merchants.items():
            ultimo_horario = info['last_time'].strftime("%d/%m/%Y %H:%M")
            print(f'{parceiro}: {info["count"]} vezes, último erro em {ultimo_horario} (UTC-3), '
                  f'Banco Pagador: {info["banco_pagador"]}')

contar_erros_bancos_e_parceiros('./pb-v4-transactions.Withdraw.json')
