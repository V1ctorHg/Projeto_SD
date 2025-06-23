from random import normalvariate, random, randint, gauss, uniform, sample
import matplotlib
matplotlib.use('Agg')  # Configurar o backend Agg para evitar problemas com threads
import numpy as np


class eleicao:
    def __init__(self, populacao, partidos, cidades=None):
        """
        Inicializa uma simulação de eleição.
        
        Args:
            populacao: População total de eleitores
            partidos: Lista de partidos participantes
            cidades: Lista de cidades (opcional)
        """
        self.partidos = partidos
        self.populacao = populacao
        self.cidades = cidades if cidades is not None else []
        
    def votacao(self, comparecimento, influencia_cidade=None, tipo='municipal'):
        """
        Função interna para simular votação de um tipo específico.
        
        Args:
            comparecimento (float): Taxa esperada de comparecimento
            influencia_cidade (list): Influência local dos partidos
            tipo (str): 'municipal', 'estadual' ou 'federal'
        """
    
        # Eventos de última hora (clima, escândalos, etc) podem afetar comparecimento
        fator_ultima_hora = uniform(0.95, 1.05)
        comparecimento *= fator_ultima_hora
        
        populacao_efetiva = round(self.populacao * comparecimento)   

        # Viés base de campanha
        vies_campanha = None
        if tipo == 'federal':
            vies_campanha = [uniform(0.1, 3.0) for _ in self.partidos]
            
            # Chance de "onda" em eleição federal (30%)
            if random() < 0.3:
                partido_momentum = randint(0, len(self.partidos)-1)
                vies_campanha[partido_momentum] *= uniform(1.5, 2.5)
                
                # Efeito secundário em partido próximo (20%)
                if random() < 0.2:
                    partido_secundario = randint(0, len(self.partidos)-1)
                    while partido_secundario == partido_momentum:
                        partido_secundario = randint(0, len(self.partidos)-1)
                    vies_campanha[partido_secundario] *= uniform(1.1, 1.3)
            
            # Campanha negativa (40%)
            if random() < 0.4:
                num_alvos = min(randint(1, 3), len(self.partidos))
                alvos = sample(range(len(self.partidos)), k=num_alvos)
                for alvo in alvos:
                    vies_campanha[alvo] *= uniform(0.6, 0.9)
                    
            # Decisões de última hora (15%)
            if random() < 0.15:
                partido_origem = randint(0, len(self.partidos)-1)
                partido_destino = randint(0, len(self.partidos)-1)
                while partido_destino == partido_origem:
                    partido_destino = randint(0, len(self.partidos)-1)
                
                magnitude_mudanca = uniform(0.05, 0.15)
                valor_mudanca = vies_campanha[partido_origem] * magnitude_mudanca
                vies_campanha[partido_origem] -= valor_mudanca
                vies_campanha[partido_destino] += valor_mudanca
                
        if influencia_cidade:
            vies_campanha = [vies * influencia 
                            for vies, influencia in zip(vies_campanha, influencia_cidade)]
        
        faixa_peso_base = {
            'federal': (0.1, 4.0)
        }
        
        peso_min, peso_max = faixa_peso_base[tipo]
        pesos_popularidade = [uniform(peso_min, peso_max) * vies for vies in vies_campanha]
        
        mult_alpha = {
            'federal': 1.0,
        }
        
        proporcoes = np.random.dirichlet([peso * mult_alpha[tipo] for peso in pesos_popularidade]) * 100
        proporcoes = [round(p, 2) for p in proporcoes]
        
        # Ajuste para 100%
        diferenca = round(100 - sum(proporcoes), 2)
        if diferenca != 0:
            indices = list(range(len(proporcoes)))
            np.random.shuffle(indices)
            for i in indices:
                if abs(diferenca) < 0.01:
                    break
                max_ajuste = abs(diferenca) if tipo == 'federal' else abs(diferenca) / 2
                ajuste = uniform(0, max_ajuste)
                proporcoes[i] += ajuste if diferenca > 0 else -ajuste
                diferenca = round(100 - sum(proporcoes), 2)
        
        # Ruído nos votos
        fator_ruido = {
            'federal': 0.15,
        }
        
        votos = []
        for porcentagem in proporcoes:
            votos_estimados = round((porcentagem / 100) * populacao_efetiva)
            votos_ajustados = max(0, round(gauss(
                votos_estimados,
                votos_estimados * fator_ruido[tipo]
            )))
            votos.append(votos_ajustados)
        
        # Ajuste final para populacao_efetiva
        ajuste = populacao_efetiva - sum(votos)
        while ajuste != 0:
            indices = list(range(len(votos)))
            np.random.shuffle(indices)
            for i in indices:
                if ajuste == 0:
                    break
                if ajuste > 0:
                    votos[i] += 1
                    ajuste -= 1
                elif votos[i] > 0:
                    votos[i] -= 1
                    ajuste += 1
        
        return np.array(votos)
    
    def simular_votos(self, comparecimento):
        """
        Simula votos federais de forma consistente para uma cidade.
            
        Args:
            comparecimento (float): Taxa esperada de comparecimento
                
        Returns:
            np.ndarray: Array com os votos federais
        """
        # Gera influência local uma única vez
        influencia_cidade = [uniform(0.7, 1.3) for _ in self.partidos]
            
        # Chance de ter um partido dominante local
        if random() < 0.3:  # 30% de chance
            partido_dominante = randint(0, len(self.partidos)-1)
            influencia_cidade[partido_dominante] *= uniform(1.3, 1.8)
            
        # Simula votação usando a influência local
        votos_federais = self.votacao(comparecimento, influencia_cidade, tipo='federal')
            
        return votos_federais

    @staticmethod
    def processar_eleicao(cidades, partidos, populacao_total):
        """
        Processa a eleição por cidade, computando os votos federais.
        
        Args:
            cidades: Lista de nomes das cidades ou número inteiro de cidades
            partidos: Lista de nomes dos partidos
            populacao_total: População total de eleitores
            
        Returns:
            list: Lista de dicionários com os resultados de cada cidade, onde cada dicionário contém:
                - nome: Nome da cidade
                - populacao: População total da cidade
                - total_votos: Total de votos na cidade
                - vencedor: Partido vencedor na cidade
                - porcentagem_vencedor: Porcentagem do vencedor
                - votos_por_partido: Dicionário com votos de cada partido
        """
        def divide_populacao(populacao_total, num_cidades):
            # Garantir que temos população suficiente para todas as cidades
            if populacao_total < num_cidades:
                raise ValueError("População total deve ser maior que o número de cidades")
            
            populacao_cidades = []
            populacao_restante = populacao_total
            
            # Classificação das cidades
            cidades_grandes = max(1, int(num_cidades * 0.2))  # 20% são cidades grandes
            cidades_medias = max(1, int(num_cidades * 0.3))   # 30% são cidades médias
            cidades_pequenas = num_cidades - cidades_grandes - cidades_medias  # Restante são pequenas
            
            # Distribuição da população
            # Cidades grandes (50% da população)
            pop_grandes = int(populacao_total * 0.5)
            media_grandes = pop_grandes // cidades_grandes
            for _ in range(cidades_grandes):
                # Adiciona variação de ±20% para mais realismo
                variacao = uniform(0.8, 1.2)
                populacao = int(media_grandes * variacao)
                populacao = min(populacao, populacao_restante)  # Não ultrapassar população restante
                populacao_cidades.append(populacao)
                populacao_restante -= populacao
            
            # Cidades médias (30% da população)
            pop_medias = int(populacao_total * 0.3)
            media_medias = pop_medias // cidades_medias
            for _ in range(cidades_medias):
                variacao = uniform(0.8, 1.2)
                populacao = int(media_medias * variacao)
                populacao = min(populacao, populacao_restante)
                populacao_cidades.append(populacao)
                populacao_restante -= populacao
            
            # Cidades pequenas (população restante)
            media_pequenas = populacao_restante // cidades_pequenas
            for i in range(cidades_pequenas):
                if i == cidades_pequenas - 1:
                    # Última cidade recebe o resto para garantir soma total
                    populacao_cidades.append(populacao_restante)
                else:
                    variacao = uniform(0.8, 1.2)
                    populacao = int(media_pequenas * variacao)
                    populacao = min(populacao, populacao_restante)
                    populacao_cidades.append(populacao)
                    populacao_restante -= populacao
            
            # Embaralhar a lista para não ter as cidades ordenadas por tamanho
            np.random.shuffle(populacao_cidades)
            
            return populacao_cidades

        # Inicializa acumuladores
        num_partidos = len(partidos)
        taxa_comparecimento = 0.7
        
        # Determina o número de cidades e cria lista de nomes se necessário
        num_cidades = cidades if isinstance(cidades, int) else len(cidades)
        nomes_cidades = cidades if isinstance(cidades, list) else [f"Cidade {i+1}" for i in range(num_cidades)]
        
        populacao_cidades = divide_populacao(populacao_total, num_cidades)
        
        # Lista para armazenar resultados de cada cidade
        resultados_cidades = []

        # Processa cada cidade
        for i, pop in enumerate(populacao_cidades):
            if pop is None:
                continue
                
            # Cria uma instância de eleição para a cidade atual
            cidade_atual = nomes_cidades[i]
            simulador = eleicao(pop, partidos, [cidade_atual])
            
            # Simula os votos federais
            votos_federais = simulador.simular_votos(taxa_comparecimento)
            
            # Formata os resultados da cidade
            votos_por_partido = {partidos[j]: int(votos_federais[j]) for j in range(num_partidos)}
            total_votos_cidade = sum(votos_federais)
            
            # Encontra o vencedor
            if total_votos_cidade > 0:
                idx_vencedor = np.argmax(votos_federais)
                vencedor = partidos[idx_vencedor]
                porcentagem_vencedor = round((votos_federais[idx_vencedor] / total_votos_cidade) * 100, 2)
            else:
                vencedor = "N/A"
                porcentagem_vencedor = 0

            # Adiciona os resultados à lista
            resultados_cidades.append({
                "nome": cidade_atual,
                "populacao": pop,
                "total_votos": int(total_votos_cidade),
                "vencedor": vencedor,
                "porcentagem_vencedor": porcentagem_vencedor,
                "votos_por_partido": votos_por_partido
            })

        return resultados_cidades