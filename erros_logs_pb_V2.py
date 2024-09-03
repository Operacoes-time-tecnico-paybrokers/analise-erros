#pb-v4-log > pb-v4-logs > Pix_Withdraw_Logs
# {createdAt:{$gte:ISODate("2024-08-19T21:00:00.000Z"),$lt: ISODate("2024-08-19T23:00:00.000Z")}}

import json
def contar_erros(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    
    erros = {}
    for item in data:
        erro = item.get('error_message', 'N/A')
        if erro in erros:
            erros[erro] += 1
        else:
            erros[erro] = 1
    
    for erro, contagem in erros.items():
        print(f'{erro}: {contagem}')

contar_erros('./pb-v4-logs.Pix_Withdraw_Logs.json')