from tkinter import Tk, filedialog, Label, Button, messagebox, Scale, colorchooser, Frame
import tkinter.font as tkFont
from tkinter import ttk
from datetime import datetime
from manipulador_imagem import *



class Aplicativo:
    VALIDADE = datetime(2024, 1, 31)  # A data de validade é definida como 31 de dezembro de 2024.

    def __init__(self, janela):
        self.verificar_validade()
        ''' Carrega a janela principal com todos os seus componentes '''
        self.janela = janela
        self.janela.title("TRATAR FOTOS COM METADADOS - V1.0")
        self.janela.configure(bg="#e1e1e1")

        self.quadro = Frame(self.janela, padx=40, pady=30, bg="#e1e1e1")
        self.quadro.pack()

        self.fonte_botao = tkFont.Font(size=12, weight='bold')
        self.fonte_label = tkFont.Font(size=12, weight='normal')
        self.fonte_escala = tkFont.Font(size=12, weight="normal")

        self.botao = Button(self.quadro, text="Clique para selecionar uma pasta de fotos e tratar os metadados",
                            padx=20, pady=20, bg="#4CAF50", fg="white",
                            cursor="hand2",
                            command=self.tratar_fotos,
                            font=self.fonte_botao)
        self.botao.grid(row=0, columnspan=5)

        self.label_tamanho_fonte = Label(self.quadro,
                                         text="Configuração da Fonte a ser Impressa na Foto",
                                         pady=20, justify="center", font=self.fonte_label, bg="#e1e1e1")
        self.label_tamanho_fonte.grid(row=1, columnspan=5)

        self.label_tamanho = Label(self.quadro, text="Tamanho da Fonte:", pady=10, padx=20, justify="right",
                                   font=self.fonte_label, bg="#e1e1e1")
        self.label_tamanho.grid(row=2, column=0, padx=20)
        self.escala_tamanho = Scale(self.quadro, from_=10, to=80, orient="horizontal", font=self.fonte_escala,
                                    bg="#e1e1e1")
        self.escala_tamanho.grid(row=2, column=1, padx=20)
        self.escala_tamanho.set(24)

        self.botao_cor = Button(self.quadro, text="Escolher Cor", padx=20, pady=10, command=self.escolher_cor,
                                font=self.fonte_label, bg="#2196F3", fg="white")
        self.botao_cor.grid(row=2, column=2, padx=20)
        self.cor_texto = "black"

        self.botao_pre_visualizacao = Button(self.quadro, text="Pré-visualizar", padx=20, pady=10,
                                             command=self.pre_visualizar, font=self.fonte_label, bg="#2196F3",
                                             fg="white")
        self.botao_pre_visualizacao.grid(row=2, column=3, padx=20)

        self.barra_progresso = ttk.Progressbar(self.quadro, orient="horizontal", length=400, mode="determinate")
        self.barra_progresso.grid(row=5, columnspan=5, pady=20)

        self.label_arquivo_atual = Label(self.quadro, text="", pady=10, padx=20, font=self.fonte_label, bg="#e1e1e1")
        self.label_arquivo_atual.grid(row=6, columnspan=5)

        self.label_creditos = Label(self.janela, text="Desenvolvido por Diogo Batista - diogo@dtbintelligence.com.br",
                                    bg="#e1e1e1", fg="#696969")
        self.label_creditos.pack(side="bottom", pady=5)

    # Verifica a data de ativação do app
    def verificar_validade(self):
        if datetime.now() > Aplicativo.VALIDADE:
            messagebox.showerror("Licença Expirada",
                                 "Sua licença para este software expirou. Por favor, entre em contato com o desenvolvedor. Diogo Batista (diogo@dtbintelligence.com.br)")
            exit()

    # Opção de pre-visualização da foto
    def pre_visualizar(self):
        caminho_arquivo = filedialog.askopenfilename(title="Selecione uma foto para pré-visualizar",
                                                     filetypes=[("JPEG files", "*.jpg"), ("JPEG files", "*.jpeg")])
        if caminho_arquivo:
            with Image.open(caminho_arquivo) as imagem:
                if "exif" not in imagem.info:
                    messagebox.showwarning("Aviso", "Arquivo sem metadados")
                    return

            metadados = extrair_metadados(caminho_arquivo)
            if any(metadados):
                imagem_com_metadados = desenhar_metadados_na_imagem(caminho_arquivo, metadados,
                                                                    self.escala_tamanho.get(),
                                                                    self.cor_texto, "Topo Esquerdo")
                imagem_com_metadados.show()

    # Ataliza a barras de estatus
    def atualizar_progresso(self, arquivo, valor):
        self.label_arquivo_atual.config(text=f"Processando: {arquivo}")
        self.barra_progresso["value"] += valor
        self.janela.update_idletasks()


    # Trata as fotos
    def tratar_fotos(self):
        pasta_fotos = filedialog.askdirectory(title="Selecione uma pasta de fotos")
        if not pasta_fotos:
            return

        tamanho_fonte = self.escala_tamanho.get()
        fotos_nao_processadas = {}
        pasta_tratadas_criada = False
        fotos_tratadas = 0  # Inicializa o contador

        self.barra_progresso["maximum"] = len(os.listdir(pasta_fotos))

        for nome_arquivo in os.listdir(pasta_fotos):
            caminho_completo = os.path.join(pasta_fotos, nome_arquivo)
            self.atualizar_progresso(nome_arquivo, 0)

            if caminho_completo.lower().endswith(('.jpg', '.jpeg')) and arquivo_jpeg_valido(caminho_completo):
                try:
                    metadados = extrair_metadados(caminho_completo)

                    if not any(metadados):
                        fotos_nao_processadas[nome_arquivo] = "Sem metadados"
                        continue

                    if not pasta_tratadas_criada:
                        if not os.path.exists(os.path.join(pasta_fotos, "Fotos tratadas")):
                            os.makedirs(os.path.join(pasta_fotos, "Fotos tratadas"), exist_ok=True)
                            pasta_tratadas_criada = True

                    imagem_com_metadados = desenhar_metadados_na_imagem(caminho_completo, metadados, tamanho_fonte,
                                                                        self.cor_texto, "Topo Esquerdo")
                    nome_arquivo_tratado = gerar_novo_nome(os.path.join(pasta_fotos, "Fotos tratadas"), nome_arquivo)
                    caminho_tratado = os.path.join(pasta_fotos, "Fotos tratadas", nome_arquivo_tratado)
                    imagem_com_metadados.save(caminho_tratado)
                    fotos_tratadas += 1  # Incremente o contador
                    self.atualizar_progresso(nome_arquivo, 1)
                except Exception as e:
                    fotos_nao_processadas[nome_arquivo] = str(e)
                    continue

        self.barra_progresso["value"] = 0
        self.label_arquivo_atual.config(text=f"{fotos_tratadas} arquivos processados")

        if fotos_nao_processadas:
            lista_fotos = "\n".join([f"{arquivo}: {motivo}" for arquivo, motivo in fotos_nao_processadas.items()])
            messagebox.showwarning("Aviso",
                                   f"As seguintes imagens não foram processadas:\n\n{lista_fotos}")

    # Escolhe a cor da fonte a ser usa
    def escolher_cor(self):
        cor = colorchooser.askcolor()[1]
        if cor:
            self.cor_texto = cor

if __name__ == '__main__':
    janela = Tk()
    app = Aplicativo(janela)
    janela.mainloop()