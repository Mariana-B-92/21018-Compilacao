# MOCP - My Own C in Português

**UAb 2024/2025 – Unidade Curricular de Compilação**  

<img width="420" height="420" alt="logo" src="https://github.com/user-attachments/assets/dc6dc0f6-ef6b-4fa8-8a2e-ee60c5c5f3d6" />


Este projeto tem como objetivo o desenvolvimento de um compilador para a linguagem **MOCP (My Own C in Project)**, uma linguagem fictícia inspirada em C. A gramática foi simplificada e adaptada para fins didáticos, permitindo explorar conceitos de análise léxica e sintática.

---

## 📘 Introdução

A linguagem **MOCP** foi concebida para facilitar o estudo e a experimentação de conceitos de compilação, utilizando ferramentas como o **ANTLR4**.  

Este repositório inclui:  
- A gramática completa da linguagem em ANTLR4 (`MOCP.g4`)  
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
├── MOCPErrorListener.py # Intercepta e traduz erros do ANTLR4 em mensagens amigáveis para MOCP.
├── main.py              # Script principal para execução e análise
├── Testes/              # Diretório com exemplos de programas MOCP
└── README.md            # Documentação do projeto
```

---
## 🚀 Como Executar

### 1️⃣ Instalar Python

**Windows:**
1. Verifique se o Python 3 está instalado:
```bash
python --version
```
2. Caso não esteja, aceder a https://www.python.org/downloads/windows/ 
3. Clique em “Download Python 3.X”  
4. Durante a instalação, ative **Add Python to PATH**  
5. Verificar a instalação:  
```bash
python --version
```

**Linux/Mac:**
1. Verifique se o Python 3 está instalado:
```bash
python --version
```
2. Caso não esteja, use o gestor de pacotes da sua distribuição
```bash
sudo apt install python3
```
ou
```bash
brew install python3
```

---

## 2️⃣ Terminal:

- Windows: CMD, PowerShell ou Git Bash

- Linux/Mac: terminal nativo


**Como utilizar:**

Para gerar a árvore textual
```bash
python3 main.py Teste/teste1.txt -tree
```
Para abrir a GUI da árvore
```bash
python3 main.py Teste/teste1.txt -gui
```
⚠️ Certifique-se de que o ANTLR4 está instalado e o antlr4-parse está no PATH.

---

## 3️⃣ Preparar o ambiente
1. Instale o ANTLR4 e adicione ao PATH (ver instruções em: https://github.com/antlr/antlr4)
2. Instale a runtime Python do ANTLR4:
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
- Undefined Behaviour Team 1
  -  Mariana Barrote - 2200640
  -  Rui Correia - 2102862
- UC de Compilação - Universidade Aberta, 2025/2026
