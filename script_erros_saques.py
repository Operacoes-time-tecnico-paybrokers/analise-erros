import json

def contar_erros_bancos_e_parceiros(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

    erros = {}
    bancos = {}
    parceiros = {}

    for item in data:
        erro = item.get('error', 'N/A')
        banco = item.get('receiver_bank_name', 'N/A')
        parceiro = item.get('merchant_name', 'N/A')

        if erro in erros:
            erros[erro] += 1
        else:
            erros[erro] = 1

        if banco in bancos:
            bancos[banco] += 1
        else:
            bancos[banco] = 1

        if parceiro in parceiros:
            parceiros[parceiro] += 1
        else:
            parceiros[parceiro] = 1

    print("Erros:")
    for erro, contagem in erros.items():
        print(f'{erro}: {contagem}')

    print("\nBancos:")
    for banco, contagem in bancos.items():
        print(f'{banco}: {contagem}')

    print("\nParceiros:")
    for parceiro, contagem in parceiros.items():
        print(f'{parceiro}: {contagem}')

contar_erros_bancos_e_parceiros('./pb-v4-transactions.Withdraw.json')
