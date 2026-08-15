import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from core.config import LOCAL_IMPORT


"""
    Robo responsavel por logar no Weathercloud e exportar
    o CSV com os dados da estacao para a pasta de Downloads.
    Esse arquivo e usado pelo ImportarCSV (services/importarCSV.py)
    em seguida, no main.py.
"""


# --- Configuracao ---

def obter_credenciais():
    """Le usuario e senha das variaveis de ambiente."""
    usuario = os.environ.get("WEATHERCLOUD_USUARIO")
    senha = os.environ.get("WEATHERCLOUD_SENHA")

    if not usuario or not senha:
        raise RuntimeError(
            "Defina WEATHERCLOUD_USUARIO e WEATHERCLOUD_SENHA nas variaveis de ambiente."
        )

    return usuario, senha


def criar_navegador():
    """Cria e configura o navegador Chrome (headless-friendly, com
    download automatico habilitado direto para a pasta de import,
    a mesma pasta que o ImportarCSV le - LOCAL_IMPORT)."""
    pasta_download = str(LOCAL_IMPORT.resolve())  # <-- caminho absoluto
    LOCAL_IMPORT.mkdir(parents=True, exist_ok=True)  # <-- garante que existe

    chrome_options = Options()
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 2,
        "profile.managed_default_content_settings.images": 2,
        "download.default_directory": pasta_download,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    servico = Service(ChromeDriverManager().install())
    navegador = webdriver.Chrome(service=servico, options=chrome_options)

    return navegador, pasta_download


# --- Helpers de interacao com a pagina ---

def fechar_popup_upgrade(navegador, timeout=8):
    """Tenta fechar qualquer modal (ex: 'Upgrade account') que esteja
    bloqueando a pagina. Retorna True se conseguiu fechar algo."""
    seletores = [
        '//*[@id="database-index"]/div[1]/div/div[3]/div/button/span[1]',
        "//h4[contains(text(),'Upgrade account')]/following-sibling::*[self::span or self::button or self::i]",
        "//div[contains(@class,'modal')]//button[contains(@class,'close')]",
        "//*[@class='close']",
        "//span[text()='\u00d7']",
    ]
    for seletor in seletores:
        try:
            botao = WebDriverWait(navegador, timeout).until(
                EC.element_to_be_clickable((By.XPATH, seletor))
            )
            navegador.execute_script("arguments[0].click();", botao)
            print("Popup fechado.")
            time.sleep(1)
            return True
        except TimeoutException:
            continue
    print("Nenhum popup encontrado (ou ja estava fechado).")
    return False


def clicar_forcado(navegador, by, valor):
    """Clica em um elemento via JavaScript, contornando overlays
    que poderiam interceptar o clique normal."""
    elemento = navegador.find_element(by, valor)
    navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
    navegador.execute_script("arguments[0].click();", elemento)
    return elemento


def selecionar_ano(navegador, ano, select_id="database-select-year"):
    """Seleciona o ano no <select> escondido por tras do dropdown
    Bootstrap-select, disparando o evento 'change' para a UI atualizar."""
    script = """
    var select = document.getElementById(arguments[0]);
    if (!select) { return 'no-select'; }
    select.value = arguments[1];
    if (window.jQuery) {
        jQuery(select).trigger('change');
        if (jQuery(select).selectpicker) {
            jQuery(select).selectpicker('refresh');
        }
    } else {
        var event = new Event('change', { bubbles: true });
        select.dispatchEvent(event);
    }
    return 'ok';
    """
    resultado = navegador.execute_script(script, select_id, str(ano))
    if resultado == "no-select":
        print(f"AVISO: nao encontrei <select id='{select_id}'>. "
              f"Confirme o id real do dropdown 'Ano' no HTML.")
    else:
        print(f"Ano selecionado: {ano}")
    return resultado


def clicar_exportar(navegador, timeout=10):
    """Clica no botao/link 'Exportar' da tela Banco de dados."""
    seletor = "//a[contains(@class,'database-button')]"
    botao = WebDriverWait(navegador, timeout).until(
        EC.element_to_be_clickable((By.XPATH, seletor))
    )
    navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
    navegador.execute_script("arguments[0].click();", botao)
    print("Cliquei em Exportar.")


# --- Etapas do fluxo ---

def realizar_login(navegador, usuario, senha):
    """Acessa o Weathercloud e realiza o login."""
    navegador.get("https://app.weathercloud.net/")
    navegador.maximize_window()
    time.sleep(5)

    links = navegador.find_elements(By.TAG_NAME, "a")
    for i, link in enumerate(links):
        if "Entrar" in link.text:
            print("ENCONTRADO:", i)
            print(link.get_attribute("outerHTML"))
            navegador.execute_script("arguments[0].scrollIntoView();", link)
            navegador.execute_script("arguments[0].click();", link)
            break

    time.sleep(10)

    navegador.find_element(By.XPATH, '//*[@id="LoginForm_entity"]').send_keys(usuario)
    navegador.find_element(By.XPATH, '//*[@id="LoginForm_password"]').send_keys(senha)
    navegador.find_element(By.XPATH, '//*[@id="logon-form"]/div[4]/button').click()

    time.sleep(10)

    # Depois do login pode aparecer o popup "Upgrade account" -- fecha se existir
    fechar_popup_upgrade(navegador)


def exportar_dados_ano_atual(navegador):
    """Navega ate Banco de dados, seleciona o ano atual e exporta o CSV."""
    # Clicar no menu principal / Banco de dados (com clique forcado via JS)
    clicar_forcado(navegador, By.XPATH, '//*[@id="header-main-menu"]/li[3]/a')
    time.sleep(10)

    # Pode aparecer o popup de novo aqui -- fecha se existir
    fechar_popup_upgrade(navegador)

    ano_atual = datetime.now().year
    selecionar_ano(navegador, ano_atual)
    time.sleep(2)

    clicar_exportar(navegador)

    # Aguarda o download terminar
    time.sleep(10)


# --- Ponto de entrada ---

def executar():
    """Roda o robo por completo: login no Weathercloud + exportacao do
    CSV do ano atual para a pasta de Downloads."""
    usuario, senha = obter_credenciais()
    navegador, pasta_download = criar_navegador()

    try:
        realizar_login(navegador, usuario, senha)
        exportar_dados_ano_atual(navegador)
        print(f"Processo concluido. Verifique a pasta: {pasta_download}")
    finally:
        navegador.quit()


if __name__ == "__main__":
    executar()
