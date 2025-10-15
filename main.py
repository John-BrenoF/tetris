import pygame
import random
import sys
import time

pygame.init()
pygame.mixer.init()

LARGURA_TELA, ALTURA_TELA = 1000, 860
TELA = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Tetris")

COLUNAS, LINHAS = 10, 20
TAMANHO_BLOCO = 40
FPS = 60

LARGURA_JOGO = COLUNAS * TAMANHO_BLOCO  # 400
ALTURA_JOGO = LINHAS * TAMANHO_BLOCO    # 800
TOP_LEFT_X = (LARGURA_TELA - LARGURA_JOGO) // 2
TOP_LEFT_Y = ALTURA_TELA - ALTURA_JOGO - 40

PRETO = (20, 20, 20)
BRANCO = (230, 230, 230)
CINZA_ESCURO = (40, 40, 40)
CINZA_CLARO = (100, 100, 100)

CORES = [
    (0, 255, 255),  # Cyan - I
    (0, 0, 255),    # Blue - J
    (255, 165, 0),  # Orange - L
    (255, 255, 0),  # Yellow - O
    (0, 255, 0),    # Green - S
    (160, 32, 240), # Purple - T
    (255, 0, 0),    # Red - Z
    (60, 60, 60)    # Cor da peça fantasma
]

FORMAS = [
    [[['.....', '.....', 'OOOO.', '.....', '.....'],
      ['..O..', '..O..', '..O..', '..O..', '.....']]],
    [[['.....', '.O...', '.OOO.', '.....', '.....'],
      ['.....', '..OO.', '..O..', '..O..', '.....'],
      ['.....', '.....', '.OOO.', '...O.', '.....'],
      ['.....', '..O..', '..O..', '.OO..', '.....']]],
    [[['.....', '...O.', '.OOO.', '.....', '.....'],
      ['.....', '..O..', '..O..', '..OO.', '.....'],
      ['.....', '.....', '.OOO.', '.O...', '.....'],
      ['.....', '.OO..', '..O..', '..O..', '.....']]],
    [[['.....', '.....', '.OO..', '.OO..', '.....']]],
    [[['.....', '.....', '..OO.', '.OO..', '.....'],
      ['.....', '..O..', '..OO.', '...O.', '.....']]],
    [[['.....', '..O..', '.OOO.', '.....', '.....'],
      ['.....', '..O..', '..OO.', '..O..', '.....'],
      ['.....', '.....', '.OOO.', '..O..', '.....'],
      ['.....', '..O..', '.OO..', '..O..', '.....']]],
    [[['.....', '.....', '.OO..', '..OO.', '.....'],
      ['.....', '..O..', '.OO..', '.O...', '.....']]]
]

class Peca:
    def __init__(self, x, y, forma):
        self.x = x
        self.y = y
        self.forma = forma
        self.cor_id = FORMAS.index(forma)
        self.cor = CORES[self.cor_id]
        self.rotation = 0

    def get_posicoes(self):
        posicoes = []
        formatos_possiveis = self.forma[0]
        formato_atual = formatos_possiveis[self.rotation % len(formatos_possiveis)]
        for i, linha in enumerate(formato_atual):
            for j, coluna in enumerate(linha):
                if coluna == 'O':
                    posicoes.append((self.x + j, self.y + i))
        return posicoes

class Particula:
    def __init__(self, x, y, cor):
        self.x = x
        self.y = y
        self.cor = cor
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-3, 1)
        self.tamanho = random.randint(4, 8)
        self.vida = self.tamanho

class TetrisGame:
    def __init__(self):
        self.tela = TELA
        self.clock = pygame.time.Clock()
        self.rodando = True
        self.game_over = False

        self.grid = [[-1 for _ in range(COLUNAS)] for _ in range(LINHAS)]
        self.pecas_bag = list(range(len(FORMAS)))
        self.peca_atual = self.pegar_peca_aleatoria()
        self.proxima_peca = self.pegar_peca_aleatoria()
        self.peca_segura = None
        self.pode_segurar = True

        self.score = 0
        self.linhas_limpas = 0
        self.nivel = 1
        self.tempo_queda = 0
        self.velocidade_queda = 0.5  # segundos por linha

        self.linhas_para_animar = []
        self.tempo_animacao = 0
        self.peca_travada_para_animar = None
        self.particulas = []

        self.shake_duracao = 0
        self.shake_intensidade = 0
        self.offset_tela = (0, 0)

        self.carregar_sons()

    def carregar_sons(self):
        self.sons = {}
        sons_para_carregar = {
            'move': 'move.wav',
            'rotate': 'Minha-gravação-7.mp3',
            'drop': 'stone-dropping-6843.mp3',
            'clear': 'explosion-312361.mp3',
            'gameover': 'wrong-buzzer-6268.mp3',
            'levelup': 'levelup.wav'
        }
        if pygame.mixer.get_init():
            for nome_som, nome_arquivo in sons_para_carregar.items():
                try:
                    self.sons[nome_som] = pygame.mixer.Sound(nome_arquivo)
                except (pygame.error, FileNotFoundError) as e:
                    print(f"Aviso: Não foi possível carregar o som '{nome_arquivo}'. Erro: {e}")
                    self.sons[nome_som] = None
            try:
                pygame.mixer.music.load('som-de-fundo.mp3')
                pygame.mixer.music.set_volume(0.20)
                pygame.mixer.music.play(-1)
            except pygame.error as e:
                print(f"Aviso: Não foi possível carregar a música de fundo 'som-de-fundo.mp3'. Erro: {e}")

    def tocar_som(self, nome):
        if self.sons.get(nome):
            self.sons[nome].play()

    def pegar_peca_aleatoria(self):
        if not self.pecas_bag:
            self.pecas_bag = list(range(len(FORMAS)))
            random.shuffle(self.pecas_bag)
        forma_idx = self.pecas_bag.pop()
        return Peca(5, 0, FORMAS[forma_idx])

    def posicao_valida(self, peca):
        for x, y in peca.get_posicoes():
            if not (0 <= x < COLUNAS and y < LINHAS and (y < 0 or self.grid[y][x] == -1)):
                return False
        return True

    def travar_peca(self):
        posicoes_peca = self.peca_atual.get_posicoes()
        for x, y in posicoes_peca:
            if y >= 0:
                self.grid[y][x] = self.peca_atual.cor_id
                px = TOP_LEFT_X + x * TAMANHO_BLOCO + TAMANHO_BLOCO // 2
                py = TOP_LEFT_Y + y * TAMANHO_BLOCO + TAMANHO_BLOCO // 2
                self.criar_particulas_travamento(px, py, self.peca_atual.cor)

        self.peca_travada_para_animar = self.peca_atual
        self.tocar_som('drop')

    def apagar_linhas(self):
        if self.linhas_para_animar: return 0

        linhas_completas = 0
        indices_linhas_apagadas = []
        for i in range(LINHAS - 1, -1, -1):
            if -1 not in self.grid[i]:
                linhas_completas += 1
                indices_linhas_apagadas.append(i)

                linha_apagada = self.grid[i]
                for x_bloco in range(COLUNAS):
                    cor_id = linha_apagada[x_bloco]
                    px = TOP_LEFT_X + x_bloco * TAMANHO_BLOCO + TAMANHO_BLOCO // 2
                    py = TOP_LEFT_Y + i * TAMANHO_BLOCO + TAMANHO_BLOCO // 2
                    self.criar_particulas(px, py, CORES[cor_id])

                for k in range(i, 0, -1):
                    self.grid[k] = list(self.grid[k - 1])
                self.grid[0] = [-1 for _ in range(COLUNAS)]
        
        if linhas_completas > 0:
            self.tocar_som('clear')
            self.score += [40, 100, 300, 1200][linhas_completas - 1] * self.nivel
            self.linhas_limpas += linhas_completas
            
            nivel_anterior = self.nivel
            self.nivel = (self.linhas_limpas // 10) + 1
            if self.nivel > nivel_anterior:
                self.tocar_som('levelup')

            velocidade_base_nivel = 0.5 - (self.nivel - 1) * 0.05
            bonus_velocidade_linhas = self.linhas_limpas * 0.0005
            self.velocidade_queda = max(0.08, velocidade_base_nivel - bonus_velocidade_linhas)
            
            self.shake_duracao = 15
            self.shake_intensidade = linhas_completas * 2
            
            self.linhas_para_animar = indices_linhas_apagadas
            self.tempo_animacao = time.time()

    def desenhar_bloco(self, x, y, cor_id, offset_x=0, offset_y=0):
        cor_base = CORES[cor_id]
        cor_clara = tuple(min(255, c + 50) for c in cor_base)
        cor_escura = tuple(max(0, c - 50) for c in cor_base)
        
        px, py = offset_x + x * TAMANHO_BLOCO, offset_y + y * TAMANHO_BLOCO
        
        pygame.draw.rect(self.tela, cor_base, (px, py, TAMANHO_BLOCO, TAMANHO_BLOCO))
        pygame.draw.rect(self.tela, cor_escura, (px, py + TAMANHO_BLOCO - 4, TAMANHO_BLOCO, 4))
        pygame.draw.rect(self.tela, cor_escura, (px + TAMANHO_BLOCO - 4, py, 4, TAMANHO_BLOCO))
        pygame.draw.rect(self.tela, cor_clara, (px + 3, py + 3, TAMANHO_BLOCO - 10, 5))

    def desenhar_tela(self):
        self.tela.fill(PRETO)

        fonte_titulo = pygame.font.SysFont('comicsans', 50, bold=True)
        titulo = fonte_titulo.render('TETRIS', True, BRANCO)
        self.tela.blit(titulo, (LARGURA_TELA // 2 - titulo.get_width() // 2 + self.offset_tela[0], 30 + self.offset_tela[1]))

        for y in range(LINHAS):
            for x in range(COLUNAS):
                pygame.draw.rect(self.tela, CINZA_ESCURO, (TOP_LEFT_X + x * TAMANHO_BLOCO + self.offset_tela[0], TOP_LEFT_Y + y * TAMANHO_BLOCO + self.offset_tela[1], TAMANHO_BLOCO, TAMANHO_BLOCO), 1)

        for y in range(LINHAS):
            for x in range(COLUNAS):
                if self.grid[y][x] != -1:
                    self.desenhar_bloco(x, y, self.grid[y][x], TOP_LEFT_X + self.offset_tela[0], TOP_LEFT_Y + self.offset_tela[1])

        if not self.game_over:
            peca_fantasma = Peca(self.peca_atual.x, self.peca_atual.y, self.peca_atual.forma)
            peca_fantasma.rotation = self.peca_atual.rotation
            while self.posicao_valida(peca_fantasma):
                peca_fantasma.y += 1
            peca_fantasma.y -= 1
            for x, y in peca_fantasma.get_posicoes():
                if y >= 0:
                    pygame.draw.rect(self.tela, CORES[7], (TOP_LEFT_X + x * TAMANHO_BLOCO + self.offset_tela[0], TOP_LEFT_Y + y * TAMANHO_BLOCO + self.offset_tela[1], TAMANHO_BLOCO, TAMANHO_BLOCO), 4)

            for x, y in self.peca_atual.get_posicoes():
                if y >= 0:
                    self.desenhar_bloco(x, y, self.peca_atual.cor_id, TOP_LEFT_X, TOP_LEFT_Y)

        if self.peca_travada_para_animar:
            for x, y in self.peca_travada_para_animar.get_posicoes():
                if y >= 0:
                    self.desenhar_bloco(x, y, self.peca_travada_para_animar.cor_id, TOP_LEFT_X + self.offset_tela[0], TOP_LEFT_Y + self.offset_tela[1])
            self.peca_travada_para_animar = None

        if self.linhas_para_animar:
            tempo_decorrido = time.time() - self.tempo_animacao
            if tempo_decorrido < 0.2:
                for y_linha in self.linhas_para_animar:
                    pygame.draw.rect(self.tela, BRANCO if int(tempo_decorrido * 20) % 2 == 0 else CINZA_CLARO, (TOP_LEFT_X + self.offset_tela[0], TOP_LEFT_Y + y_linha * TAMANHO_BLOCO + self.offset_tela[1], LARGURA_JOGO, TAMANHO_BLOCO))
            else:
                self.linhas_para_animar = []

        for p in self.particulas:
            pygame.draw.rect(self.tela, p.cor, (p.x + self.offset_tela[0], p.y + self.offset_tela[1], p.tamanho, p.tamanho))

        pygame.draw.rect(self.tela, CINZA_CLARO, (TOP_LEFT_X + self.offset_tela[0], TOP_LEFT_Y + self.offset_tela[1], LARGURA_JOGO, ALTURA_JOGO), 4)

        self.desenhar_ui()

        if self.game_over:
            self.desenhar_game_over()

        pygame.display.update()

    def desenhar_ui(self):
        fonte_ui = pygame.font.SysFont('comicsans', 30)
        fonte_ui_pequena = pygame.font.SysFont('comicsans', 24)

        largura_ui = 200
        espaco_lateral_direito = LARGURA_TELA - (TOP_LEFT_X + LARGURA_JOGO)
        ui_box_x = TOP_LEFT_X + LARGURA_JOGO + (espaco_lateral_direito - largura_ui) // 2
        pygame.draw.rect(self.tela, CINZA_ESCURO, (ui_box_x + self.offset_tela[0], TOP_LEFT_Y + self.offset_tela[1], 200, 120), border_radius=10)
        pygame.draw.rect(self.tela, CINZA_CLARO, (ui_box_x + self.offset_tela[0], TOP_LEFT_Y + self.offset_tela[1], 200, 120), 3, border_radius=10)
        
        texto_score_label = fonte_ui_pequena.render('SCORE', True, CINZA_CLARO)
        self.tela.blit(texto_score_label, (ui_box_x + (200 - texto_score_label.get_width()) // 2 + self.offset_tela[0], TOP_LEFT_Y + 15 + self.offset_tela[1]))
        texto_score = fonte_ui.render(f'{self.score}', True, BRANCO)
        self.tela.blit(texto_score, (ui_box_x + (200 - texto_score.get_width()) // 2 + self.offset_tela[0], TOP_LEFT_Y + 40 + self.offset_tela[1]))

        texto_nivel_label = fonte_ui_pequena.render('NÍVEL', True, CINZA_CLARO)
        self.tela.blit(texto_nivel_label, (ui_box_x + (200 - texto_nivel_label.get_width()) // 2 + self.offset_tela[0], TOP_LEFT_Y + 75 + self.offset_tela[1]))
        texto_nivel = fonte_ui.render(f'{self.nivel}', True, BRANCO)
        self.tela.blit(texto_nivel, (ui_box_x + (200 - texto_nivel.get_width()) // 2 + self.offset_tela[0], TOP_LEFT_Y + 90 + self.offset_tela[1]))

        pygame.draw.rect(self.tela, CINZA_ESCURO, (ui_box_x + self.offset_tela[0], TOP_LEFT_Y + 140 + self.offset_tela[1], 200, 160), border_radius=10)
        pygame.draw.rect(self.tela, CINZA_CLARO, (ui_box_x + self.offset_tela[0], TOP_LEFT_Y + 140 + self.offset_tela[1], 200, 160), 3, border_radius=10)
        texto_proxima = fonte_ui_pequena.render('PRÓXIMA', True, CINZA_CLARO)
        self.tela.blit(texto_proxima, (ui_box_x + (200 - texto_proxima.get_width()) // 2 + self.offset_tela[0], TOP_LEFT_Y + 155 + self.offset_tela[1]))
        
        posicoes_proxima = self.proxima_peca.get_posicoes()
        min_x = min(p[0] for p in posicoes_proxima)
        min_y = min(p[1] for p in posicoes_proxima)
        max_x = max(p[0] for p in posicoes_proxima)
        max_y = max(p[1] for p in posicoes_proxima)
        
        offset_x_peca = (200 - (max_x - min_x + 1) * TAMANHO_BLOCO) // 2
        offset_y_peca = (160 - (max_y - min_y + 1) * TAMANHO_BLOCO) // 2

        for x, y in posicoes_proxima:
            self.desenhar_bloco(x - min_x, y - min_y, self.proxima_peca.cor_id, ui_box_x + offset_x_peca + self.offset_tela[0], TOP_LEFT_Y + 140 + offset_y_peca + self.offset_tela[1])

        pygame.draw.rect(self.tela, CINZA_ESCURO, (ui_box_x + self.offset_tela[0], TOP_LEFT_Y + 320 + self.offset_tela[1], 200, 160), border_radius=10)
        pygame.draw.rect(self.tela, CINZA_CLARO, (ui_box_x + self.offset_tela[0], TOP_LEFT_Y + 320 + self.offset_tela[1], 200, 160), 3, border_radius=10)
        texto_segurar = fonte_ui_pequena.render('SEGURAR (C)', True, CINZA_CLARO)
        self.tela.blit(texto_segurar, (ui_box_x + (200 - texto_segurar.get_width()) // 2 + self.offset_tela[0], TOP_LEFT_Y + 335 + self.offset_tela[1]))
        if self.peca_segura:
            posicoes_segura = self.peca_segura.get_posicoes()
            min_x = min(p[0] for p in posicoes_segura)
            min_y = min(p[1] for p in posicoes_segura)
            max_x = max(p[0] for p in posicoes_segura)
            max_y = max(p[1] for p in posicoes_segura)

            offset_x_peca = (200 - (max_x - min_x + 1) * TAMANHO_BLOCO) // 2
            offset_y_peca = (160 - (max_y - min_y + 1) * TAMANHO_BLOCO) // 2

            for x, y in posicoes_segura:
                self.desenhar_bloco(x - min_x, y - min_y, self.peca_segura.cor_id, ui_box_x + offset_x_peca + self.offset_tela[0], TOP_LEFT_Y + 320 + offset_y_peca + self.offset_tela[1])

    def desenhar_game_over(self):
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.tela.blit(overlay, (0, 0))
        fonte_go = pygame.font.SysFont('comicsans', 80, bold=True)
        fonte_restart = pygame.font.SysFont('comicsans', 30)
        texto_go = fonte_go.render('GAME OVER', True, (255, 50, 50))
        texto_restart = fonte_restart.render('Pressione ENTER para reiniciar', True, BRANCO)
        self.tela.blit(texto_go, (LARGURA_TELA // 2 - texto_go.get_width() // 2, ALTURA_TELA // 2 - texto_go.get_height() // 2))
        self.tela.blit(texto_restart, (LARGURA_TELA // 2 - texto_restart.get_width() // 2, ALTURA_TELA // 2 + 50))

    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False
            if evento.type == pygame.KEYDOWN:
                if self.game_over:
                    if evento.key == pygame.K_RETURN:
                        self.resetar_jogo()
                    return

                if evento.key in [pygame.K_LEFT, pygame.K_a]:
                    self.peca_atual.x -= 1
                    if not self.posicao_valida(self.peca_atual): self.peca_atual.x += 1
                    else: self.tocar_som('move')

                elif evento.key in [pygame.K_RIGHT, pygame.K_d]:
                    self.peca_atual.x += 1
                    if not self.posicao_valida(self.peca_atual): self.peca_atual.x -= 1
                    else: self.tocar_som('move')

                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.peca_atual.y += 1
                    if not self.posicao_valida(self.peca_atual): self.peca_atual.y -= 1
                    else: self.tocar_som('move')

                elif evento.key in [pygame.K_UP, pygame.K_w]:
                    self.peca_atual.rotation = (self.peca_atual.rotation + 1) % len(self.peca_atual.forma[0])
                    if not self.posicao_valida(self.peca_atual):
                        self.peca_atual.x += 1
                        if not self.posicao_valida(self.peca_atual):
                            self.peca_atual.x -= 2
                            if not self.posicao_valida(self.peca_atual):
                                self.peca_atual.x += 1
                                self.peca_atual.rotation = (self.peca_atual.rotation - 1) % len(self.peca_atual.forma[0])
                            else:
                                self.tocar_som('rotate')
                        else:
                            self.tocar_som('rotate')
                    else: self.tocar_som('rotate')
                
                elif evento.key == pygame.K_SPACE:
                    while self.posicao_valida(self.peca_atual):
                        self.peca_atual.y += 1
                    self.peca_atual.y -= 1
                    self.travar_peca()
                    self.nova_peca()
                
                elif evento.key == pygame.K_c:
                    self.segurar_peca()

    def segurar_peca(self):
        if not self.pode_segurar: return

        if self.peca_segura is None:
            self.peca_segura = self.peca_atual
            self.nova_peca(ignorar_apagar_linhas=True)
        else:
            self.peca_segura, self.peca_atual = self.peca_atual, self.peca_segura
            self.peca_atual.x = 5
            self.peca_atual.y = 0
        
        self.pode_segurar = False

    def nova_peca(self, ignorar_apagar_linhas=False):
        if len(self.particulas) > 200:
            self.particulas = self.particulas[-200:]

        self.peca_atual = self.proxima_peca
        self.proxima_peca = self.pegar_peca_aleatoria()
        self.pode_segurar = True
        if not ignorar_apagar_linhas:
            self.apagar_linhas()
        if not self.posicao_valida(self.peca_atual):
            self.game_over = True
            self.tocar_som('gameover')

    def criar_particulas(self, x, y, cor):
        for _ in range(random.randint(5, 10)):
            self.particulas.append(Particula(x, y, cor))

    def criar_particulas_travamento(self, x, y, cor):
        for _ in range(random.randint(1, 3)):
            self.particulas.append(Particula(x, y, cor))

    def atualizar_particulas(self):
        particulas_ativas = []
        for p in self.particulas:
            p.x += p.vx
            p.y += p.vy
            p.tamanho -= 0.2
            if p.tamanho > 0:
                particulas_ativas.append(p)
        self.particulas = particulas_ativas

    def atualizar_shake(self):
        if self.shake_duracao > 0:
            self.shake_duracao -= 1
            offset_x = random.randint(-self.shake_intensidade, self.shake_intensidade)
            offset_y = random.randint(-self.shake_intensidade, self.shake_intensidade)
            self.offset_tela = (offset_x, offset_y)
        else:
            self.offset_tela = (0, 0)

    def atualizar(self):
        if self.game_over:
            return

        if self.linhas_para_animar and time.time() - self.tempo_animacao < 0.2:
            return

        self.tempo_queda += self.clock.get_rawtime()
        if self.tempo_queda / 1000 >= self.velocidade_queda:
            self.tempo_queda = 0
            self.peca_atual.y += 1
            if not self.posicao_valida(self.peca_atual):
                self.peca_atual.y -= 1
                self.travar_peca()
                self.nova_peca()

    def resetar_jogo(self):
        estado_sons = self.sons
        self.__init__()
        self.sons = estado_sons

    def run(self):
        while self.rodando:
            self.clock.tick(FPS)
            self.processar_eventos()
            self.atualizar()
            self.atualizar_shake()
            self.atualizar_particulas()
            self.desenhar_tela()
        pygame.quit()
        sys.exit()

def main():
    jogo = TetrisGame()
    jogo.run()

if __name__ == "__main__":
    main()