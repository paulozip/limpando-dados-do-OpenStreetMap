# Limpeza de dados do OpenStreetMap

### Dados de localização

Este projeto tem como objetivo documentar o processo de limpeza de dados do OpenStreetMap. Além das dificuldades encontradas para alcançar tal objetivo, viso através deste documento salientar as ações realizadas para garantir a validade, a precisão, a completude, consistência e uniformidade dos dados do OpenStreetMap.

Utilizei de um mapa de uma área do Rio de Janeiro, cobrindo em sua totalidade toda a localidade chamada de Região dos Lagos, onde moro atualmente.

Rio de Janeiro, Brasil 
- [https://www.openstreetmap.org/export#map=9/-22.7091/-42.4841]


## Desafios encontrados

Os dados encontrados no OpenStreetMap são gerados por seus próprios usuários, seja através da api do Google ou de submissões na plataforma. Devido a esse fato, tais dados podem sofrer diferentes problemas, desde sua formatação incorreta, erros de grafia ou falta de padronização de dados. Após uma breve análise do arquivo XML, os principais problemas encontrados no mapa foram:

* **Números de telefone preenchidos sem um padrão**:
    Muitos dados são gravados sem a utilização de uma máscara padrão para os números. Alguns usuários colocam o prefixo do país (*+55*), enquanto outros não; há também ocorrência onde o usuário coloca ou não *"-"* dividindo o número; além de situações onde é utilizado parênteses para encapsular o DDD.

    Para resolver esse problema criei uma função em Python que formata e limpa esse dado, de forma que encapsule o DDD entre parênteses, e que separe o número por dígitos (*-*):

    ```python
    for elem in root.iter('tag'):
        #Removendo +55 e '-' do número do telefone:
        if elem.attrib['k'] == 'phone': 
            #Verificando se há +55 no número do telefone
            if '+55' in elem.attrib['v'].replace(' ',''):
                elem.attrib['v'] = elem.attrib['v'].strip().replace(' ','').replace('+55','', 1)
            #Verificando se há 55 no começo do número do telefone
            if '55' in elem.attrib['v'].replace(' ','')[:3]:
                elem.attrib['v'] = elem.attrib['v'].strip().replace(' ','').replace('55','', 1)
            #Verificando se há hífen no número do telefone
            if '-' in elem.attrib['v']:
                elem.attrib['v'] = elem.attrib['v'].strip().replace(' ','').replace('-', '')
            #Buscando por parenteses
            if '(' in elem.attrib['v'] or ')' in elem.attrib['v']:
                elem.attrib['v'] = elem.attrib['v'].strip().replace(' ','').replace('(', '')
                elem.attrib['v'] = elem.attrib['v'].strip().replace(' ','').replace(')', '')
            #Formatando número do telefone
            if not '0800' in elem.attrib['v'][:4]:
                elem.attrib['v'] = '{} {}-{}'.format(elem.attrib['v'][:2], elem.attrib['v'][2:6], elem.attrib['v'][6:10])
    ```
* **Logradouros informados incorretamente**:
    Há ocorrência de muitos endereços com nomes abreviados na `tag[k: addr:street]`, como *av* para *Avenida* e *est.* para *Estrada*, dentre outros. A função realizou uma iteração por todas as tags do arquivo e procura de valores incorretos para correção.

    *Exemplo de dados encontrados*:
    ```XML
    <tag k="addr:street" v="av Costa Azul"/>
    <tag k="addr:street" v="av Amazonas"/>
    <tag k="addr:street" v="Est. Profº Leandro Faria Sarzedas"/>

    ```

* **CEPs indevidos**:
    Assim como os números de telefone, códigos de CEP são informados sem uma máscara que facilitaria a leitura. Utilizando a função `verifica_cep()`,eu realizo a limpeza desses dados e adiciono o dígito *-* para separar os três últimos números.

    *Diferentes tipos de CEP encontrados*
    ```XML
    <tag k="postal_code" v="25900213"/>
    <tag k="postal_code" v="24030-128"/>    
    ```

* **Números inteiros e por extenso**
    Em alguns casos pude perceber que quando há um número no endereço da `<tag k="addr:street"...>`,