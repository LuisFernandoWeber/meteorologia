import torch
import torch.nn as nn


class BlocoResidual(nn.Module):
    """
    Bloco residual: Linear -> BatchNorm -> LeakyReLU -> Dropout -> Linear -> BatchNorm,
    somado à entrada original (skip connection). Isso ajuda o gradiente a fluir melhor
    em redes mais profundas e tende a estabilizar/acelerar o treinamento.
    """

    def __init__(self, dim, dropout=0.3):
        super().__init__()
        self.bloco = nn.Sequential(
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
            nn.LeakyReLU(0.1),
            nn.Dropout(dropout),
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
        )
        self.ativacao = nn.LeakyReLU(0.1)

    def forward(self, x):
        return self.ativacao(x + self.bloco(x))


class Net(nn.Module):
    """
    Rede neural para previsão meteorológica: múltiplas entradas, uma única saída.

    Parâmetros
    ----------
    input_dim : int
        Número de variáveis de entrada (ex.: temperatura, umidade, pressão, vento).
    hidden_dim : int
        Largura das camadas ocultas e dos blocos residuais.
    num_blocos : int
        Quantos blocos residuais empilhar (controla a profundidade/complexidade).
    dropout : float
        Taxa de dropout para regularização (importante dado o aumento de parâmetros).
    saida_sigmoid : bool
        True  -> aplica Sigmoid na saída. Use para classificação binária
                 (ex.: "vai chover amanhã?") com nn.BCELoss, ou regressão
                 com alvo normalizado entre 0 e 1.
        False -> saída "crua" (logit), sem ativação final. Use para regressão
                 de valores reais (ex.: prever temperatura) com nn.MSELoss ou
                 nn.L1Loss, ou para classificação binária combinada com
                 nn.BCEWithLogitsLoss (mais estável numericamente que
                 Sigmoid + BCELoss).
    """

    def __init__(self, input_dim=4, hidden_dim=64, num_blocos=3,
                 dropout=0.3, saida_sigmoid=True):
        super().__init__()

        self.entrada = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.LeakyReLU(0.1),
            nn.Dropout(dropout),
        )

        self.blocos = nn.Sequential(
            *[BlocoResidual(hidden_dim, dropout) for _ in range(num_blocos)]
        )

        camadas_saida = [
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LeakyReLU(0.1),
            nn.Dropout(dropout / 2),
            nn.Linear(hidden_dim // 2, 16),
            nn.LeakyReLU(0.1),
            nn.Linear(16, 1),
        ]
        if saida_sigmoid:
            camadas_saida.append(nn.Sigmoid())

        self.saida = nn.Sequential(*camadas_saida)

        self._inicializar_pesos()

    def _inicializar_pesos(self):
        """Inicialização de He/Kaiming, adequada para LeakyReLU."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, a=0.1, nonlinearity='leaky_relu')
                nn.init.zeros_(m.bias)

    def forward(self, entrada):
        x = self.entrada(entrada)
        x = self.blocos(x)
        return self.saida(x)


if __name__ == "__main__":
    # Exemplo rápido de uso
    modelo = Net(input_dim=4, hidden_dim=64, num_blocos=3, dropout=0.3, saida_sigmoid=True)
    print(modelo)

    lote_exemplo = torch.randn(8, 4)  # batch de 8 amostras, 4 variáveis cada
    saida = modelo(lote_exemplo)
    print("Formato da saída:", saida.shape)

    n_parametros = sum(p.numel() for p in modelo.parameters())
    print(f"Total de parâmetros: {n_parametros:,}")
