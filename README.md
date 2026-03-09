# MOCP - My Own Compiler Project

**UAb 2024/2025 – Unidade Curricular de Compilação**  

<img width="420" height="420" alt="logo" src="https://github.com/user-attachments/assets/dc6dc0f6-ef6b-4fa8-8a2e-ee60c5c5f3d6" />


Este projeto tem como objetivo o desenvolvimento de um compilador para a linguagem **MOCP (My Own Compiler Project)**, uma linguagem fictícia inspirada em C. A gramática foi simplificada e adaptada para fins didáticos, permitindo explorar conceitos de análise léxica e sintática.

---

## 📘 Introdução

A linguagem **MOCP** foi concebida para facilitar o estudo e a experimentação de conceitos de compilação, utilizando ferramentas como o **ANTLR4**.  

Este repositório inclui:  
- A gramática completa da linguagem em ANTLR4 (`MOC.g4`)  
- Scripts para compilação, análise e validação de programas escritos em MOCP  

---

## 🛠 Requisitos

- **Python 3.10 ou superior**  
- **ANTLR versão 4.13.2**  
- **Java instalado** (necessário para executar o ANTLR)  

---

## 📂 Estrutura do Projeto

```text
MOCP/
├── MOCP.g4              # Gramática da linguagem MOCP em ANTLR4
├── main.py              # Script principal para execução e análise
├── Testes/              # Diretório com exemplos de programas MOCP
└── README.md            # Documentação do projeto
```

---
## 🚀 Como Executar

### 1️⃣ Instalar Python

**Windows:**  
1. Aceder a https://www.python.org/downloads/windows/ 
2. Clique em “Download Python 3.X”  
3. Durante a instalação, ative **Add Python to PATH**  
4. Verificar a instalação:  
```bash
python --version
```

---

## 2️⃣ Terminal recomendado: Git Bash
Para que o comando main.py -tree funcione corretamente no Windows, recomenda-se o uso de um terminal compatível com comandos Unix, como o Git Bash.

**Instalação**
1. Aceder a  https://git-scm.com/download/wi
2. Transferir o executável mais recente
3. Aceitar todas as opções por defeito
4. Abrir o Git Bash no menu iniciar ou configurar no IDE

**Como utilizar**
No Git Bash, pode executar os comandos do projeto normalmente. Exemplo:
```bash
python3 main.py Teste/teste1.txt -tree
```

---

## 3️⃣ Preparar o ambiente
1. Instale o ANTLR4 e adicione ao PATH (ver instruções em: https://github.com/antlr/antlr4)
2. Instale dependências:
```bash
pip install antlr4-python3-runtime
```

---

## 4️⃣ Compilar a gramática
```bash
antlr4 -Dlanguage=Python3 -visitor MOCP.g4
```

---

## Autores
- Undefined Behaviour - Mariana Barrote - 2200640 / Rui Correia - 2102862
- UC de Compilação - Universidade Aberta, 2025/2026
